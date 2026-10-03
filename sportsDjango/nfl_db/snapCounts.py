from nfl_db.models import nflTeam, nflMatch, player, playerMatchUsage
from django.db import transaction
from decimal import Decimal
import csv, io, requests


# nflverse publishes one snap count file per season and refreshes it daily in season.
# Each file holds the whole season so far, so pulling it again just rewrites the
# same figures and adds any games played since.
snapCountsUrl = "https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_{season}.csv"
# Crosswalk from the Pro Football Reference ids the snap counts use to ESPN ids.
nflversePlayersUrl = "https://github.com/nflverse/nflverse-data/releases/download/players/players.csv"

# nflverse abbreviations that differ from the ones stored on nflTeam. The relocated
# franchises each have a single nflTeam row under their current abbreviation.
nflverseTeamAbbreviations = {
    'LA': 'LAR',
    'STL': 'LAR',
    'WAS': 'WSH',
    'OAK': 'LV',
    'SD': 'LAC',
}

snapFields = ['offenseSnaps', 'offenseSnapPct', 'defenseSnaps', 'defenseSnapPct', 'specialTeamsSnaps', 'specialTeamsSnapPct']


def fetchCsvRows(url):
    response = requests.get(url, timeout = 60)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    # Decoded directly: the nflverse files are UTF-8, and leaving requests to guess the
    # encoding of a multi-megabyte file takes the best part of a minute.
    return list(csv.DictReader(io.StringIO(response.content.decode('utf-8'))))


def teamAbbreviation(nflverseAbbreviation):
    return nflverseTeamAbbreviations.get(nflverseAbbreviation, nflverseAbbreviation)


def buildMatchLookup(seasonYear):
    # Keyed on the pair of teams rather than home and away, so a neutral-site game
    # where the two sources disagree on which side is home still lines up. Two teams
    # never meet twice in one week, or twice in one postseason. Playoff matches are
    # stored as weeks 19 and up whatever the season length, while nflverse numbers
    # them straight on from the last regular-season week, so they are keyed apart.
    matchLookup = {}
    seasonMatches = nflMatch.objects.filter(yearOfSeason = seasonYear).prefetch_related('homeTeam', 'awayTeam')
    for match in seasonMatches:
        matchTeams = frozenset([team.abbreviation for team in match.homeTeam.all()] + [team.abbreviation for team in match.awayTeam.all()])
        if len(matchTeams) != 2:
            continue
        weekKey = 'post' if match.weekOfSeason >= 19 else match.weekOfSeason
        matchLookup[(weekKey, matchTeams)] = match
    return matchLookup


def findMatch(matchLookup, row):
    # game_id is "<season>_<week>_<away>_<home>", e.g. 2026_01_ARI_LAC.
    gameIdParts = row['game_id'].split('_')
    matchTeams = frozenset([teamAbbreviation(gameIdParts[2]), teamAbbreviation(gameIdParts[3])])
    weekKey = int(row['week']) if row['game_type'] == 'REG' else 'post'
    return matchLookup.get((weekKey, matchTeams))


def resolvePlayersByPfrId(pfrIds):
    playersByPfrId = {playerObj.pfrId: playerObj for playerObj in player.objects.filter(pfrId__in = pfrIds)}

    unresolvedPfrIds = set(pfrIds) - set(playersByPfrId.keys())
    if len(unresolvedPfrIds) == 0:
        return playersByPfrId

    espnIdByPfrId = {}
    for crosswalkRow in fetchCsvRows(nflversePlayersUrl) or []:
        if crosswalkRow['pfr_id'] in unresolvedPfrIds and crosswalkRow['espn_id'].isdigit():
            espnIdByPfrId[crosswalkRow['pfr_id']] = int(crosswalkRow['espn_id'])

    playersByEspnId = {playerObj.espnId: playerObj for playerObj in player.objects.filter(espnId__in = espnIdByPfrId.values())}
    newlyMatchedPlayers = []
    for pfrId, espnId in espnIdByPfrId.items():
        playerObj = playersByEspnId.get(espnId)
        # A player already carrying a different pfrId is left alone rather than overwritten.
        if playerObj == None or (playerObj.pfrId != None and playerObj.pfrId != pfrId):
            continue
        playerObj.pfrId = pfrId
        newlyMatchedPlayers.append(playerObj)
        playersByPfrId[pfrId] = playerObj

    player.objects.bulk_update(newlyMatchedPlayers, ['pfrId'])
    return playersByPfrId


def snapCount(value):
    return int(value) if value not in (None, '', 'NA') else None


def snapPct(value):
    # nflverse gives the share as a fraction (0.08); stored as a percentage (8.0) like
    # the other Pct fields.
    if value in (None, '', 'NA'):
        return None
    return Decimal(str(round(float(value) * 100, 1)))


def pullSnapCounts(seasonYear):
    summary = {'season': seasonYear, 'rows': 0, 'created': 0, 'updated': 0, 'unchanged': 0,
               'unmatchedPlayers': {}, 'unmatchedGames': set(), 'unmatchedTeams': set()}

    snapRows = fetchCsvRows(snapCountsUrl.format(season = seasonYear))
    if snapRows == None:
        print("No nflverse snap count file for " + str(seasonYear) + ".")
        return summary
    summary['rows'] = len(snapRows)

    teamsByAbbreviation = {team.abbreviation: team for team in nflTeam.objects.all()}
    matchLookup = buildMatchLookup(seasonYear)
    playersByPfrId = resolvePlayersByPfrId({row['pfr_player_id'] for row in snapRows if row['pfr_player_id']})

    existingUsage = {(usage.player_id, usage.nflMatch_id): usage
                     for usage in playerMatchUsage.objects.filter(nflMatch__yearOfSeason = seasonYear)}

    usageToCreate = {}
    usageToUpdate = {}
    for row in snapRows:
        playerObj = playersByPfrId.get(row['pfr_player_id'])
        if playerObj == None:
            summary['unmatchedPlayers'][row['pfr_player_id']] = row['player'] + " (" + row['position'] + ", " + row['team'] + ")"
            continue
        match = findMatch(matchLookup, row)
        if match == None:
            summary['unmatchedGames'].add(row['game_id'])
            continue
        team = teamsByAbbreviation.get(teamAbbreviation(row['team']))
        if team == None:
            summary['unmatchedTeams'].add(row['team'])
            continue

        snapValues = {
            'offenseSnaps': snapCount(row['offense_snaps']),
            'offenseSnapPct': snapPct(row['offense_pct']),
            'defenseSnaps': snapCount(row['defense_snaps']),
            'defenseSnapPct': snapPct(row['defense_pct']),
            'specialTeamsSnaps': snapCount(row['st_snaps']),
            'specialTeamsSnapPct': snapPct(row['st_pct']),
        }

        usageKey = (playerObj.id, match.id)
        usage = existingUsage.get(usageKey)
        if usage == None:
            usageToCreate[usageKey] = playerMatchUsage(nflMatch = match, team = team, player = playerObj, **snapValues)
            continue

        if usage.team_id == team.id and all(getattr(usage, field) == snapValues[field] for field in snapFields):
            summary['unchanged'] += 1
            continue
        usage.team = team
        for field in snapFields:
            setattr(usage, field, snapValues[field])
        usageToUpdate[usageKey] = usage

    with transaction.atomic():
        playerMatchUsage.objects.bulk_create(usageToCreate.values(), batch_size = 1000)
        playerMatchUsage.objects.bulk_update(usageToUpdate.values(), snapFields + ['team'], batch_size = 1000)

    summary['created'] = len(usageToCreate)
    summary['updated'] = len(usageToUpdate)
    return summary


def printSnapCountSummary(summary):
    print(str(summary['season']) + ": " + str(summary['rows']) + " rows read, "
          + str(summary['created']) + " created, " + str(summary['updated']) + " updated, "
          + str(summary['unchanged']) + " already stored and unchanged.")
    if len(summary['unmatchedPlayers']) > 0:
        print("   " + str(len(summary['unmatchedPlayers'])) + " players not in the player table, skipped:")
        for pfrId, description in sorted(summary['unmatchedPlayers'].items(), key = lambda item: item[1]):
            print("      " + description + " [" + pfrId + "]")
    if len(summary['unmatchedGames']) > 0:
        print("   " + str(len(summary['unmatchedGames'])) + " games with no stored nflMatch, skipped: "
              + ", ".join(sorted(summary['unmatchedGames'])))
    if len(summary['unmatchedTeams']) > 0:
        print("   Unknown team abbreviations, skipped: " + ", ".join(sorted(summary['unmatchedTeams'])))
