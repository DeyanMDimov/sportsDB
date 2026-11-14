from nfl_db.models import nflMatch, nflTeam, playByPlay, playerMatchUsage, playerPropLine, passerStatSplit
from nfl_db.crudLogic import TEAM_WEEKLY_STATS, playWasNullified


# Props page: each sportsbook line next to what the player has actually done in his
# recent games, and, for weeks already played, whether the side his recent average
# pointed to came in.

# The prop types the page can compare, in dropdown order: ESPN prop type id ->
# label, the TEAM_WEEKLY_STATS keys that add up to it, and the smallest line the
# edge is measured against. Books post the odd 0.5-yard line (a backup QB's rushing),
# where any average at all is a huge share of the line; measuring those against 10
# yards keeps them from crowding the top of the table.
PROP_STATS = [
    (13, "Receiving Yards", ["receivingYards"], 10),
    (14, "Receptions", ["receptions"], 1),
    (12, "Rushing Yards", ["rushingYards"], 10),
    (11, "Carries", ["rushingAttempts"], 1),
    (20, "Rushing + Receiving Yards", ["rushingYards", "receivingYards"], 10),
    (8, "Passing Yards", ["passingYards"], 10),
    (10, "Passing Touchdowns", ["passingTds"], 1),
]
PROP_STATS_BY_ID = {propTypeId: (label, statKeys, edgeFloor) for propTypeId, label, statKeys, edgeFloor in PROP_STATS}

# Not a By Team stat, so defined here: a touchdown pass on a play that stood.
PROP_STAT_VALUES = dict(TEAM_WEEKLY_STATS, passingTds = (passerStatSplit, lambda statSplit: 1 if statSplit.passingTdScored else 0))

RECENT_GAME_CHOICES = [3, 5, 8]
DEFAULT_RECENT_GAMES = 5

# Season record buckets: how far the recent average sat above or below the line,
# as a share of the line. (label, low, high), low inclusive.
EDGE_BUCKETS = [
    ("20%+ under", None, -0.20),
    ("10-20% under", -0.20, -0.10),
    ("0-10% under", -0.10, 0),
    ("0-10% over", 0, 0.10),
    ("10-20% over", 0.10, 0.20),
    ("20%+ over", 0.20, None),
]
# A lean this far from the line counts as a strong one.
STRONG_EDGE = 0.15
# An average over fewer games than this says too little: those players go to the
# bottom of the table and stay out of the records.
MIN_GAMES = 3


def matchesWithPlays(seasonYear):
    # Games whose play-by-play has been pulled. A game without it says nothing about
    # what a player did, so it is left out rather than counted as a zero.
    return set(playByPlay.objects.filter(nflMatch__yearOfSeason = seasonYear).values_list('nflMatch_id', flat = True).distinct())


def playerGameStats(playerIds, seasonYear, statKeys, playedMatchIds):
    # {player id: {match id: {stat key: value}}} for every game the player took part in
    # (played offensive snaps, or turns up in the play-by-play) among playedMatchIds.
    # A game he played without touching the ball has zeros.
    statsByPlayer = {}

    for playerId, matchId in playerMatchUsage.objects.filter(
        player_id__in = playerIds, nflMatch__yearOfSeason = seasonYear, offenseSnaps__gt = 0,
    ).values_list('player_id', 'nflMatch_id'):
        if matchId in playedMatchIds:
            statsByPlayer.setdefault(playerId, {}).setdefault(matchId, {})

    statsBySplitModel = {}
    for statKey in statKeys:
        splitModel, playValue = PROP_STAT_VALUES[statKey]
        statsBySplitModel.setdefault(splitModel, []).append((statKey, playValue))

    for splitModel, modelStats in statsBySplitModel.items():
        # A re-pulled game leaves repeat split rows; a player only counts once per play.
        countedPlays = set()
        for statSplit in splitModel.objects.filter(
            player_id__in = playerIds, play__nflMatch__yearOfSeason = seasonYear,
        ).select_related('play', 'player'):
            matchId = statSplit.play.nflMatch_id
            if matchId not in playedMatchIds or (statSplit.player_id, statSplit.play_id) in countedPlays:
                continue
            countedPlays.add((statSplit.player_id, statSplit.play_id))
            gameStats = statsByPlayer.setdefault(statSplit.player_id, {}).setdefault(matchId, {})
            if playWasNullified(statSplit.play.playDescription):
                continue
            for statKey, playValue in modelStats:
                gameStats[statKey] = gameStats.get(statKey, 0) + playValue(statSplit)

    return statsByPlayer


def average(values):
    return sum(values) / len(values) if values else None


def lineOutcome(value, line):
    if value > line:
        return 'over'
    if value < line:
        return 'under'
    return 'push'


def edgeBucket(edgeShare):
    for label, low, high in EDGE_BUCKETS:
        if (low == None or edgeShare >= low) and (high == None or edgeShare < high):
            return label
    return None


def playerTeamsByMatch(playerIds, matchIds):
    # {(player id, match id): team} from the snap counts, which say which side he was on.
    return {(usage.player_id, usage.nflMatch_id): usage.team for usage in playerMatchUsage.objects.filter(
        player_id__in = playerIds, nflMatch_id__in = matchIds).select_related('team')}


def buildPropBoard(seasonYear, weekOfSeason, propTypeId, recentGames = DEFAULT_RECENT_GAMES):
    # Every line of one prop type in the season, each with the player's average over
    # his last recentGames games before it. Returns the selected week's rows and the
    # season's record of how the lean (the side of the line the average was on) did.
    label, statKeys, edgeFloor = PROP_STATS_BY_ID[propTypeId]
    seasonLines = list(playerPropLine.objects.filter(
        nflMatch__yearOfSeason = seasonYear, propTypeId = propTypeId,
    ).select_related('player', 'player__team', 'nflMatch'))

    playedMatchIds = matchesWithPlays(seasonYear)
    playerIds = {line.player_id for line in seasonLines}
    statsByPlayer = playerGameStats(playerIds, seasonYear, statKeys, playedMatchIds)
    weekByMatchId = dict(nflMatch.objects.filter(yearOfSeason = seasonYear).values_list('id', 'weekOfSeason'))

    def gameValue(gameStats):
        return sum(gameStats.get(statKey, 0) for statKey in statKeys)

    rows = []
    for propLine in seasonLines:
        line = float(propLine.line)
        playerGames = statsByPlayer.get(propLine.player_id, {})
        # His games before this one, most recent first.
        priorGames = sorted(((weekByMatchId[matchId], gameValue(gameStats)) for matchId, gameStats in playerGames.items()
                             if weekByMatchId.get(matchId, 99) < propLine.nflMatch.weekOfSeason), reverse = True)
        recent = priorGames[:recentGames]
        recentAverage = average([value for week, value in recent])

        row = {
            'propLine': propLine,
            'player': propLine.player,
            'line': line,
            'lineMove': line - float(propLine.openLine) if propLine.openLine != None else None,
            'recentGames': [{'week': week, 'value': value, 'outcome': lineOutcome(value, line)} for week, value in recent],
            'recentAverage': recentAverage,
            'seasonAverage': average([value for week, value in priorGames]),
            'gamesPlayed': len(priorGames),
            'recentOvers': sum(1 for week, value in recent if value > line),
            'enoughGames': len(recent) >= min(MIN_GAMES, recentGames),
            'edge': None, 'edgeShare': None, 'lean': None, 'result': None, 'outcome': None, 'leanHit': None,
        }
        if recentAverage != None:
            row['edge'] = recentAverage - line
            row['edgeShare'] = row['edge'] / max(line, edgeFloor)
            row['lean'] = 'over' if row['edge'] > 0 else 'under' if row['edge'] < 0 else None

        # The game itself, once its plays are in. A player with no part in it most
        # likely sat out, which voids the bet rather than losing it.
        if propLine.nflMatch_id in playedMatchIds and propLine.nflMatch_id in playerGames:
            row['result'] = gameValue(playerGames[propLine.nflMatch_id])
            row['outcome'] = lineOutcome(row['result'], line)
            if row['lean'] and row['outcome'] != 'push':
                row['leanHit'] = row['outcome'] == row['lean']
        rows.append(row)

    weekRows = [row for row in rows if row['propLine'].nflMatch.weekOfSeason == weekOfSeason]
    addMatchups(weekRows)
    # Biggest lean either way first; players with too few games at the bottom.
    weekRows.sort(key = lambda row: (not row['enoughGames'], row['edgeShare'] == None, -abs(row['edgeShare'] or 0), row['player'].name))

    countedRows = [row for row in rows if row['enoughGames']]
    return {
        'label': label,
        'weekRows': weekRows,
        'weekRecord': leanRecord([row for row in weekRows if row['enoughGames'] and row['leanHit'] != None]),
        'seasonRecord': seasonRecord(countedRows),
        'minGames': min(MIN_GAMES, recentGames),
        'seasonLineCount': len(rows),
    }


def addMatchups(weekRows):
    # "vs NE" / "@ NE" when we know which side the player was on, else "NE @ DET".
    matchIds = {row['propLine'].nflMatch_id for row in weekRows}
    teamsByEspnId = {team.espnId: team for team in nflTeam.objects.all()}
    teamsByPlayerMatch = playerTeamsByMatch({row['player'].id for row in weekRows}, matchIds)
    for row in weekRows:
        match = row['propLine'].nflMatch
        homeTeam, awayTeam = teamsByEspnId.get(match.homeTeamEspnId), teamsByEspnId.get(match.awayTeamEspnId)
        playerTeam = teamsByPlayerMatch.get((row['player'].id, match.id))
        if playerTeam == None and row['player'].team in (homeTeam, awayTeam):
            playerTeam = row['player'].team
        row['team'] = playerTeam
        if playerTeam != None and playerTeam == homeTeam and awayTeam:
            row['matchup'] = "vs " + awayTeam.abbreviation
        elif playerTeam != None and playerTeam == awayTeam and homeTeam:
            row['matchup'] = "@ " + homeTeam.abbreviation
        else:
            row['matchup'] = (awayTeam.abbreviation if awayTeam else "?") + " @ " + (homeTeam.abbreviation if homeTeam else "?")


def leanRecord(rows):
    hits = sum(1 for row in rows if row['leanHit'])
    return {'bets': len(rows), 'hits': hits, 'misses': len(rows) - hits,
            'hitRate': hits / len(rows) if rows else None}


def seasonRecord(rows):
    # Lines that have both a lean and a result (not a push), by how far the average was
    # from the line. overRate is how often the over came in, whatever the lean.
    decided = [row for row in rows if row['leanHit'] != None]
    buckets = []
    for label, low, high in EDGE_BUCKETS:
        bucketRows = [row for row in decided if edgeBucket(row['edgeShare']) == label]
        record = leanRecord(bucketRows)
        record['label'] = label
        record['overRate'] = (sum(1 for row in bucketRows if row['outcome'] == 'over') / len(bucketRows)) if bucketRows else None
        buckets.append(record)
    strong = leanRecord([row for row in decided if abs(row['edgeShare']) >= STRONG_EDGE])
    return {'all': leanRecord(decided), 'strong': strong, 'buckets': buckets,
            'overRate': (sum(1 for row in decided if row['outcome'] == 'over') / len(decided)) if decided else None}
