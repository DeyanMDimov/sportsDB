from nfl_db.models import nflMatch, player, playerPropLine
from django.db import transaction
from django.utils import timezone as djangoTimezone
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal
import re, requests


# ESPN's odds feed lists player props per game, for whichever sportsbook ESPN partners
# with: DraftKings from 2026, ESPN BET in 2024 and 2025. Earlier seasons only have a
# handful of props per game. A game has 700-1,400 props, so it takes one or two pages.
espnLeagueUrl = "http://sports.core.api.espn.com/v2/sports/football/leagues/nfl"
# The most ESPN returns per page. Ask for more and it falls back to 25 a page.
propPageSize = 1000
# Games fetched at once. The requests are small, so a few at a time keeps a season
# backfill to a few minutes without hammering ESPN.
fetchWorkers = 4

propLineFields = ['sportsbook', 'propType', 'line', 'openLine', 'overOdds', 'underOdds', 'lastUpdated']


def fetchJson(url):
    response = requests.get(url, timeout = 30)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def propProvider(matchEspnId):
    # The sportsbook whose props ESPN carries for this game, as (provider id, name),
    # or None if no provider has props. ESPN BET seasons also list an "ESPN Bet - Live
    # Odds" provider with in-game props, which isn't wanted.
    oddsData = fetchJson(espnLeagueUrl + "/events/" + str(matchEspnId) + "/competitions/" + str(matchEspnId) + "/odds?lang=en&region=us")
    for item in (oddsData or {}).get('items', []):
        providerName = item['provider']['name']
        if 'propBets' in item and 'live' not in providerName.lower():
            return int(item['provider']['id']), providerName
    return None


def fetchPropBets(matchEspnId, providerId):
    propBetsUrl = (espnLeagueUrl + "/events/" + str(matchEspnId) + "/competitions/" + str(matchEspnId)
                   + "/odds/" + str(providerId) + "/propBets?lang=en&region=us&limit=" + str(propPageSize))
    propBets = []
    page = 1
    while True:
        pageData = fetchJson(propBetsUrl + "&page=" + str(page))
        if pageData == None:
            return propBets
        propBets += pageData.get('items', [])
        if page >= pageData.get('pageCount', 1):
            return propBets
        page += 1


def isFullGameOverUnder(propTypeName):
    # "Total Receiving Yards (incl. overtime)", "Longest Reception (incl. overtime)",
    # "Total Defensive Interceptions". Leaves out the milestone ladders ("Receiving Yards
    # Milestones"), touchdown scorer props and the "1st Half"/"1st Quarter" lines.
    return propTypeName.startswith(('Total ', 'Longest '))


def propTypeLabel(propTypeName):
    # "Total Receiving Yards (incl. overtime)" -> "Receiving Yards"
    label = propTypeName.replace(' (incl. overtime)', '')
    return label[len('Total '):] if label.startswith('Total ') else label


def targetValue(prices):
    target = (prices or {}).get('target')
    return Decimal(str(target['value'])) if target and target.get('value') != None else None


def americanOdds(price):
    # ESPN's price block, e.g. {"american": "-115", ...}, as an int.
    american = str((price or {}).get('american', '')).strip()
    if american.upper() == 'EVEN':
        return 100
    try:
        return int(american.replace('+', ''))
    except ValueError:
        return None


def espnTimestamp(value):
    # "2026-11-14T07:48Z"
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None


def mainLine(propBets):
    # The main line out of every prop bet on one player and prop type. ESPN BET props
    # come with alternate lines, and only the main line has odds on it: one prop with
    # the over price and one with the under. DraftKings props have no odds and no
    # alternates, just the main line listed twice (over and under). Returns None if
    # the props don't agree on a single line.
    priced = [prop for prop in propBets if 'over' in prop.get('current', {}) or 'under' in prop.get('current', {})]
    candidates = priced or propBets

    lines = {targetValue(prop.get('current')) for prop in candidates} - {None}
    if len(lines) > 1:
        # Now and then a game still lists an older pair alongside the line it moved
        # to, so fall back on the props updated most recently.
        latestUpdate = max(prop.get('lastUpdated') or '' for prop in candidates)
        candidates = [prop for prop in candidates if (prop.get('lastUpdated') or '') == latestUpdate]
        lines = {targetValue(prop.get('current')) for prop in candidates} - {None}
    if len(lines) != 1:
        return None
    openLines = {targetValue(prop.get('open')) for prop in candidates} - {None}

    overOdds = underOdds = None
    for prop in candidates:
        current = prop.get('current', {})
        overOdds = overOdds if overOdds != None else americanOdds(current.get('over'))
        underOdds = underOdds if underOdds != None else americanOdds(current.get('under'))

    updateTimes = [time for time in (espnTimestamp(prop.get('lastUpdated')) for prop in candidates) if time != None]
    return {
        'line': lines.pop(),
        'openLine': openLines.pop() if len(openLines) == 1 else None,
        'overOdds': overOdds,
        'underOdds': underOdds,
        'lastUpdated': max(updateTimes) if updateTimes else None,
    }


def athleteEspnId(prop):
    found = re.search(r'/athletes/(\d+)', (prop.get('athlete') or {}).get('$ref', ''))
    return int(found.group(1)) if found else None


def fetchMatchPropLines(matchEspnId):
    # Everything ESPN has for one game, network only so it can run on a worker thread.
    # Returns {'provider': (id, name) or None, 'lines': {(athleteEspnId, propTypeId): fields},
    # 'ambiguous': count, 'athleteRefs': {athleteEspnId: url}, 'error': str or None}.
    result = {'provider': None, 'lines': {}, 'ambiguous': 0, 'athleteRefs': {}, 'error': None}
    try:
        result['provider'] = propProvider(matchEspnId)
        if result['provider'] == None:
            return result

        grouped = {}
        for prop in fetchPropBets(matchEspnId, result['provider'][0]):
            propTypeName = prop.get('type', {}).get('name', '')
            athleteId = athleteEspnId(prop)
            if athleteId == None or not isFullGameOverUnder(propTypeName):
                continue
            grouped.setdefault((athleteId, int(prop['type']['id']), propTypeName), []).append(prop)
            result['athleteRefs'][athleteId] = prop['athlete']['$ref']

        for (athleteId, propTypeId, propTypeName), propBets in grouped.items():
            line = mainLine(propBets)
            if line == None:
                result['ambiguous'] += 1
                continue
            line['propType'] = propTypeLabel(propTypeName)
            result['lines'][(athleteId, propTypeId)] = line
    except Exception as e:
        result['error'] = repr(e)
    return result


def matchLabel(match):
    awayTeams = [team.abbreviation for team in match.awayTeam.all()]
    homeTeams = [team.abbreviation for team in match.homeTeam.all()]
    return (awayTeams[0] if awayTeams else '?') + " @ " + (homeTeams[0] if homeTeams else '?') + " (week " + str(match.weekOfSeason) + ")"


def athleteName(athleteRef):
    try:
        return fetchJson(athleteRef).get('displayName', '?')
    except Exception:
        return '?'


def currentWeek(seasonYear):
    # The week of the next game yet to kick off, or None once the season is over. Goes by
    # the kickoff time rather than the completed flag, which stays False until the
    # game's data is pulled, so a game nobody has pulled yet doesn't hold the week back.
    nextMatch = nflMatch.objects.filter(yearOfSeason = seasonYear, datePlayed__gte = djangoTimezone.now()).order_by('datePlayed').first()
    return nextMatch.weekOfSeason if nextMatch else None


def newPullSummary(seasonYear):
    return {'season': seasonYear, 'matches': 0, 'created': 0, 'updated': 0, 'unchanged': 0, 'ambiguous': 0,
            'sportsbooks': set(), 'matchesWithoutProps': [], 'upcomingWithoutProps': 0, 'failedMatches': [], 'unmatchedPlayers': {}}


def upcomingPropMatchIds(seasonYear, weeks):
    # The games a Pull Data run pulls lines for: those in the pulled weeks and the week
    # after the last one that haven't kicked off yet. Lines move until kickoff and stay
    # put after it, so a game already under way has nothing new to give.
    pullWeeks = set(weeks) | {max(weeks) + 1}
    return list(nflMatch.objects.filter(
        yearOfSeason = seasonYear, weekOfSeason__in = pullWeeks, datePlayed__gt = djangoTimezone.now(),
    ).order_by('datePlayed').values_list('espnId', flat = True))


def pullMatchPropLines(matchEspnId):
    # One game's lines, for the Pull Data page to call game by game: a web request
    # there can't run the worker threads pullPropLines uses.
    match = nflMatch.objects.filter(espnId = matchEspnId).prefetch_related('homeTeam', 'awayTeam').first()
    if match == None:
        return {'status': 'error', 'error': 'Unknown game'}
    summary = newPullSummary(match.yearOfSeason)
    storePropLines([match], [fetchMatchPropLines(match.espnId)], summary)
    if summary['failedMatches']:
        return {'status': 'error', 'label': matchLabel(match), 'error': summary['failedMatches'][0]}
    return {'status': 'ok', 'label': matchLabel(match), 'posted': bool(summary['sportsbooks']),
            'lines': summary['created'] + summary['updated'] + summary['unchanged'],
            'unmatchedProps': sum(details['props'] for details in summary['unmatchedPlayers'].values())}


def pullPropLines(seasonYear, weeks = None):
    summary = newPullSummary(seasonYear)

    seasonMatches = nflMatch.objects.filter(yearOfSeason = seasonYear).prefetch_related('homeTeam', 'awayTeam')
    if weeks:
        seasonMatches = seasonMatches.filter(weekOfSeason__in = weeks)
    matchesByWeek = {}
    for match in seasonMatches.order_by('weekOfSeason', 'datePlayed'):
        matchesByWeek.setdefault(match.weekOfSeason, []).append(match)

    # A week at a time, so a backfill writes as it goes and shows progress.
    for weekOfSeason, weekMatches in matchesByWeek.items():
        with ThreadPoolExecutor(max_workers = fetchWorkers) as pool:
            fetched = list(pool.map(fetchMatchPropLines, [match.espnId for match in weekMatches]))
        weekCounts = storePropLines(weekMatches, fetched, summary)
        print("   " + str(seasonYear) + " week " + str(weekOfSeason) + ": " + str(len(weekMatches)) + " games, "
              + str(weekCounts['created']) + " lines created, " + str(weekCounts['updated']) + " updated, "
              + str(weekCounts['unchanged']) + " unchanged.")

    if summary['unmatchedPlayers']:
        for athleteId, details in summary['unmatchedPlayers'].items():
            details['name'] = athleteName(details['ref'])
    return summary


def storePropLines(weekMatches, fetched, summary):
    weekCounts = {'created': 0, 'updated': 0, 'unchanged': 0}
    athleteIds = {athleteId for result in fetched for (athleteId, propTypeId) in result['lines']}
    playersByEspnId = {playerObj.espnId: playerObj for playerObj in player.objects.filter(espnId__in = athleteIds)}
    existingLines = {(line.nflMatch_id, line.player_id, line.espnProviderId, line.propTypeId): line
                     for line in playerPropLine.objects.filter(nflMatch__in = weekMatches)}

    linesToCreate = []
    linesToUpdate = []
    for match, result in zip(weekMatches, fetched):
        summary['matches'] += 1
        if result['error'] != None:
            summary['failedMatches'].append(matchLabel(match) + ": " + result['error'])
            continue
        if result['provider'] == None or not result['lines']:
            # Sportsbooks post props a few days before kickoff, so later weeks have none yet.
            if match.datePlayed != None and match.datePlayed > djangoTimezone.now():
                summary['upcomingWithoutProps'] += 1
            else:
                summary['matchesWithoutProps'].append(matchLabel(match))
            continue
        providerId, sportsbook = result['provider']
        summary['sportsbooks'].add(sportsbook)
        summary['ambiguous'] += result['ambiguous']

        for (athleteId, propTypeId), fields in result['lines'].items():
            playerObj = playersByEspnId.get(athleteId)
            if playerObj == None:
                unmatched = summary['unmatchedPlayers'].setdefault(athleteId, {'ref': result['athleteRefs'][athleteId], 'props': 0})
                unmatched['props'] += 1
                continue

            values = dict(fields, sportsbook = sportsbook)
            existing = existingLines.get((match.id, playerObj.id, providerId, propTypeId))
            if existing == None:
                linesToCreate.append(playerPropLine(nflMatch = match, player = playerObj, espnProviderId = providerId,
                                                    propTypeId = propTypeId, **values))
            elif all(getattr(existing, field) == values[field] for field in propLineFields):
                weekCounts['unchanged'] += 1
            else:
                for field in propLineFields:
                    setattr(existing, field, values[field])
                # bulk_update doesn't touch auto_now fields itself.
                existing.updatedAt = djangoTimezone.now()
                linesToUpdate.append(existing)

    with transaction.atomic():
        playerPropLine.objects.bulk_create(linesToCreate, batch_size = 1000)
        playerPropLine.objects.bulk_update(linesToUpdate, propLineFields + ['updatedAt'], batch_size = 1000)

    weekCounts['created'] = len(linesToCreate)
    weekCounts['updated'] = len(linesToUpdate)
    for key in weekCounts:
        summary[key] += weekCounts[key]
    return weekCounts


def printPropLineSummary(summary):
    print(str(summary['season']) + ": " + str(summary['matches']) + " games from "
          + (", ".join(sorted(summary['sportsbooks'])) or "no sportsbook") + ". "
          + str(summary['created']) + " lines created, " + str(summary['updated']) + " updated, "
          + str(summary['unchanged']) + " already stored and unchanged.")
    if summary['ambiguous'] > 0:
        # Mostly players offered only as a milestone ladder (15+, 20+, 25+ yards), which
        # ESPN BET filed under the same prop type as the over/unders.
        print("   " + str(summary['ambiguous']) + " player props skipped for having no single main line"
              + " (usually milestone ladders like 15+/20+/25+ yards).")
    if summary['matchesWithoutProps']:
        print("   " + str(len(summary['matchesWithoutProps'])) + " games with no player props on ESPN: "
              + ", ".join(summary['matchesWithoutProps']))
    if summary['upcomingWithoutProps'] > 0:
        print("   " + str(summary['upcomingWithoutProps']) + " upcoming games have no props posted yet.")
    if summary['failedMatches']:
        print("   " + str(len(summary['failedMatches'])) + " games failed to load:")
        for failure in summary['failedMatches']:
            print("      " + failure)
    if summary['unmatchedPlayers']:
        print("   " + str(len(summary['unmatchedPlayers'])) + " players not in the player table, their props skipped:")
        for athleteId, details in sorted(summary['unmatchedPlayers'].items(), key = lambda item: item[1].get('name', '')):
            print("      " + details.get('name', '?') + " [ESPN " + str(athleteId) + "], " + str(details['props']) + " props")
