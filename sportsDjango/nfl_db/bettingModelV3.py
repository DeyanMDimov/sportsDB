"""Betting model V3: opponent-adjusted team ratings, measured in points.

Every team gets an offense rating (points it scores above an average team) and a
defense rating (points it keeps an average opponent below their usual score). All
of them are solved for at once from past results, so a team that put up 30 on a
bad defense gets less credit than one that put up 30 on a good defense.

A game's expected score is then

    home points = league average + half of home field + home offense - away defense
    away points = league average - half of home field + away offense - home defense

plus, for each team, a quarterback adjustment: how much better or worse this
week's starter has passed than the quarterbacks behind the team's rating.

Everything above the Database section is pure (no database), so the arithmetic
can be tested and backtested on its own. docs/betting-model-v3.md explains the
reasoning and how the settings below were chosen.
"""
import math
from collections import namedtuple

from django.db.models import Count, F, Min

from nfl_db.models import nflMatch, passerStatSplit, playerWeekStatus, teamMatchPerformance


#-------Settings-------#

# A game this many weeks old counts half as much as one played last week.
HALF_LIFE_WEEKS = 10

# How many "weeks" apart the same week of two consecutive seasons is treated as
# being. A season is about 18 weeks, so the offseason ages last year's games by
# roughly 8 extra weeks: rosters and coaches change over the summer.
WEEKS_BETWEEN_SEASONS = 26

# Ratings only look at this season and the one before it. Anything older would
# count for under 3% anyway, and it keeps the stored-results invalidation in
# businessLogic.invalidateModelResults exact.
SEASONS_OF_HISTORY = 2

# Every rating is pulled toward zero (league average) as if the team had also
# played this many games at exactly average. It stops two or three unusual games
# from producing an extreme rating early in a season.
SHRINKAGE_GAMES = 4

# Totals are harder to predict than margins, so the team part of a predicted
# total is damped toward the league average.
TOTAL_RATING_WEIGHT = 0.8

# Home field is the average home margin over the same games, pulled toward
# HOME_FIELD_PRIOR_POINTS as if that had been seen in HOME_FIELD_PRIOR_GAMES games.
HOME_FIELD_PRIOR_POINTS = 2.0
HOME_FIELD_PRIOR_GAMES = 250

# How long a quarterback's passing counts for. A passer changes more slowly than
# a team does, so this is longer than HALF_LIFE_WEEKS.
QUARTERBACK_HALF_LIFE_WEEKS = 40

# A quarterback with no passes on record is assumed to be this many adjusted
# yards per dropback worse than the league average. Quarterbacks nobody has seen
# are mostly backups and rookies.
UNPROVEN_QUARTERBACK_PENALTY = 2.0

# Every quarterback is pulled toward that unproven level as if he had also
# dropped back this many times at it (about six games' worth).
QUARTERBACK_PRIOR_DROPBACKS = 200

# Points per game that one adjusted yard per dropback is worth.
QUARTERBACK_POINTS_PER_YARD = 3.0

# Stands in for "somebody without a track record" when the usual starter is out
# and nobody else on the team has thrown a pass.
UNPROVEN_QUARTERBACK = 0

# With fewer earlier games than this (about six weeks' worth) there is too little
# to rate teams on, and the model makes no prediction. It only comes up where the
# database is missing most of the previous season.
MINIMUM_GAMES_FOR_RATINGS = 100

# The model only names a bet when it disagrees with the book by at least this much.
MINIMUM_EDGE_POINTS = 1.0

# How far final margins typically land from this model's predicted margin
# (standard deviation, from the 2019-2026 backtest).
MARGIN_STANDARD_DEVIATION = 13.0

# Win rate needed to break even at the standard -110 price.
BREAK_EVEN_WIN_RATE = 110 / 210


#-------Ratings-------#

pastGame = namedtuple('pastGame', [
    'yearOfSeason', 'weekOfSeason', 'homeTeamEspnId', 'awayTeamEspnId',
    'homeTeamPoints', 'awayTeamPoints', 'neutralStadium',
])


def gameAgeInWeeks(game, yearOfSeason, weekOfSeason):
    return (weekOfSeason - game.weekOfSeason) + (yearOfSeason - game.yearOfSeason) * WEEKS_BETWEEN_SEASONS


def gamesBeforeWeek(games, yearOfSeason, weekOfSeason):
    """The games a prediction for this week is allowed to see: strictly earlier
    weeks, no further back than SEASONS_OF_HISTORY."""
    earliestSeason = yearOfSeason - (SEASONS_OF_HISTORY - 1)
    return [
        game for game in games
        if game.yearOfSeason >= earliestSeason
        and (game.yearOfSeason < yearOfSeason or (game.yearOfSeason == yearOfSeason and game.weekOfSeason < weekOfSeason))
    ]


def homeFieldPoints(games):
    """Average home margin in games that had a real home team, pulled toward the prior."""
    homeMargins = [game.homeTeamPoints - game.awayTeamPoints for game in games if not game.neutralStadium]
    return (sum(homeMargins) + HOME_FIELD_PRIOR_POINTS * HOME_FIELD_PRIOR_GAMES) / (len(homeMargins) + HOME_FIELD_PRIOR_GAMES)


class teamRatings:
    def __init__(self, leagueAveragePoints, homeField, offense, defense, gamesUsed):
        self.leagueAveragePoints = leagueAveragePoints
        self.homeFieldPoints = homeField
        self.offense = offense
        self.defense = defense
        self.gamesUsed = gamesUsed
        # A quarterbackValues for the same week, when passing data is available.
        self.quarterbacks = None

    @property
    def hasEnoughGames(self):
        return self.gamesUsed >= MINIMUM_GAMES_FOR_RATINGS

    def offenseRating(self, teamEspnId):
        return self.offense.get(teamEspnId, 0.0)

    def defenseRating(self, teamEspnId):
        return self.defense.get(teamEspnId, 0.0)

    def overallRating(self, teamEspnId):
        """Points better than an average team on a neutral field."""
        return self.offenseRating(teamEspnId) + self.defenseRating(teamEspnId)

    def rankings(self):
        """{teamEspnId: (offense rank, defense rank, overall rank)}, 1 is best."""
        teamIds = list(self.offense.keys())
        ranks = {teamId: [0, 0, 0] for teamId in teamIds}
        for position, rating in enumerate((self.offenseRating, self.defenseRating, self.overallRating)):
            for rank, teamId in enumerate(sorted(teamIds, key = rating, reverse = True), start = 1):
                ranks[teamId][position] = rank
        return {teamId: tuple(teamRanks) for teamId, teamRanks in ranks.items()}

    def quarterbackAdjustment(self, teamEspnId, starterId):
        """Points to add to a team's expected score for starting this quarterback."""
        if self.quarterbacks is None:
            return 0.0
        return self.quarterbacks.adjustment(teamEspnId, starterId)

    def expectedPoints(self, homeTeamEspnId, awayTeamEspnId, neutralStadium = False, homeQuarterbackPoints = 0.0, awayQuarterbackPoints = 0.0):
        """(home points, away points) the model expects, to one decimal."""
        homeField = 0.0 if neutralStadium else self.homeFieldPoints
        expectedMargin = homeField + self.overallRating(homeTeamEspnId) - self.overallRating(awayTeamEspnId)
        scoringLean = (self.offenseRating(homeTeamEspnId) - self.defenseRating(awayTeamEspnId)
                       + self.offenseRating(awayTeamEspnId) - self.defenseRating(homeTeamEspnId))
        expectedTotal = 2 * self.leagueAveragePoints + TOTAL_RATING_WEIGHT * scoringLean
        homePoints = (expectedTotal + expectedMargin) / 2 + homeQuarterbackPoints
        awayPoints = (expectedTotal - expectedMargin) / 2 + awayQuarterbackPoints
        return round(homePoints, 1), round(awayPoints, 1)


def fitRatings(games, yearOfSeason, weekOfSeason, halfLifeWeeks = HALF_LIFE_WEEKS, shrinkageGames = SHRINKAGE_GAMES):
    """Rate every team from the games played before this week.

    Each game gives two observations, one per team's score:
        points = league average +/- half of home field + offense rating - opponent's defense rating
    Recent games weigh more, and every rating is shrunk toward zero. That is a
    weighted ridge regression; it is solved here by repeatedly re-estimating one
    number at a time with the others held fixed, until nothing moves."""
    games = gamesBeforeWeek(games, yearOfSeason, weekOfSeason)
    homeField = homeFieldPoints(games)

    # (weight, points, half of home field with its sign, offense team, defense team)
    observations = []
    for game in games:
        weight = 0.5 ** (gameAgeInWeeks(game, yearOfSeason, weekOfSeason) / halfLifeWeeks)
        homeHalf = 0.0 if game.neutralStadium else homeField / 2
        observations.append((weight, game.homeTeamPoints, homeHalf, game.homeTeamEspnId, game.awayTeamEspnId))
        observations.append((weight, game.awayTeamPoints, -homeHalf, game.awayTeamEspnId, game.homeTeamEspnId))

    offense = {}
    defense = {}
    for weight, points, homeHalf, offenseTeam, defenseTeam in observations:
        offense[offenseTeam] = 0.0
        defense[offenseTeam] = 0.0

    totalWeight = sum(observation[0] for observation in observations)
    if totalWeight == 0:
        return teamRatings(0.0, homeField, offense, defense, 0)

    leagueAverage = sum(weight * (points - homeHalf) for weight, points, homeHalf, offenseTeam, defenseTeam in observations) / totalWeight

    for iteration in range(500):
        largestChange = 0.0

        offenseSums = dict.fromkeys(offense, 0.0)
        offenseWeights = dict.fromkeys(offense, 0.0)
        for weight, points, homeHalf, offenseTeam, defenseTeam in observations:
            offenseSums[offenseTeam] += weight * (points - leagueAverage - homeHalf + defense[defenseTeam])
            offenseWeights[offenseTeam] += weight
        for team in offense:
            newRating = offenseSums[team] / (offenseWeights[team] + shrinkageGames)
            largestChange = max(largestChange, abs(newRating - offense[team]))
            offense[team] = newRating

        defenseSums = dict.fromkeys(defense, 0.0)
        defenseWeights = dict.fromkeys(defense, 0.0)
        for weight, points, homeHalf, offenseTeam, defenseTeam in observations:
            defenseSums[defenseTeam] += weight * (leagueAverage + homeHalf + offense[offenseTeam] - points)
            defenseWeights[defenseTeam] += weight
        for team in defense:
            newRating = defenseSums[team] / (defenseWeights[team] + shrinkageGames)
            largestChange = max(largestChange, abs(newRating - defense[team]))
            defense[team] = newRating

        newAverage = sum(
            weight * (points - homeHalf - offense[offenseTeam] + defense[defenseTeam])
            for weight, points, homeHalf, offenseTeam, defenseTeam in observations
        ) / totalWeight
        largestChange = max(largestChange, abs(newAverage - leagueAverage))
        leagueAverage = newAverage

        if largestChange < 0.0005:
            break

    return teamRatings(leagueAverage, homeField, offense, defense, len(games))


#-------Quarterbacks-------#

# One team's passing in one game. starterId took the team's first dropback;
# passerId took the most, and is credited with the whole game's passing.
quarterbackGame = namedtuple('quarterbackGame', [
    'yearOfSeason', 'weekOfSeason', 'teamEspnId', 'starterId', 'passerId', 'dropbacks', 'adjustedYards',
])


def adjustedPassingYards(passingYards, touchdowns, interceptions, sackYardsLost):
    """Passing yards with touchdowns, interceptions and sacks priced in yards.
    Divided by dropbacks this is adjusted net yards per attempt."""
    return passingYards + 20 * touchdowns - 45 * interceptions - abs(sackYardsLost)


class quarterbackValues:
    def __init__(self, leagueAverage, yardsPerDropback, teamBaselines, recentQuarterbacks):
        # Adjusted yards per dropback: league-wide, and each quarterback's after shrinking.
        self.leagueAverage = leagueAverage
        self.yardsPerDropback = yardsPerDropback
        # {team: points above average of the quarterbacks behind the team's rating}
        self.teamBaselines = teamBaselines
        # {team: its quarterbacks, the latest starter first}
        self.recentQuarterbacks = recentQuarterbacks

    def pointsAboveAverage(self, playerId):
        """Points per game this quarterback is worth over a league-average one."""
        unproven = self.leagueAverage - UNPROVEN_QUARTERBACK_PENALTY
        return QUARTERBACK_POINTS_PER_YARD * (self.yardsPerDropback.get(playerId, unproven) - self.leagueAverage)

    def pointsAboveUnproven(self, playerId):
        """The same value measured from a quarterback nobody has seen, which is the
        easier number to read: a solid starter is around +6, a new backup is 0."""
        return self.pointsAboveAverage(playerId) + QUARTERBACK_POINTS_PER_YARD * UNPROVEN_QUARTERBACK_PENALTY

    def teamBaseline(self, teamEspnId):
        return self.teamBaselines.get(teamEspnId)

    def adjustment(self, teamEspnId, starterId):
        """Points to add to the team's expected score: this starter's value minus
        the value of the quarterbacks whose games produced the team's rating. Zero
        when the same quarterback has played all of them."""
        if starterId is None or teamEspnId not in self.teamBaselines:
            return 0.0
        return self.pointsAboveAverage(starterId) - self.teamBaselines[teamEspnId]

    def expectedStarter(self, teamEspnId, unavailable = ()):
        """Who to expect at quarterback in a game that hasn't been played: whoever
        started the team's last game, or failing that its most recent other
        quarterback. None when the team has no passing on record."""
        candidates = self.recentQuarterbacks.get(teamEspnId)
        if not candidates:
            return None
        for playerId in candidates:
            if playerId not in unavailable:
                return playerId
        return UNPROVEN_QUARTERBACK


def fitQuarterbackValues(quarterbackGames, yearOfSeason, weekOfSeason):
    """Value every quarterback from the passing in games before this week. Returns
    None when there is no passing on record."""
    games = gamesBeforeWeek(quarterbackGames, yearOfSeason, weekOfSeason)
    totalDropbacks = sum(game.dropbacks for game in games)
    if totalDropbacks == 0:
        return None

    leagueAverage = sum(game.adjustedYards for game in games) / totalDropbacks
    unproven = leagueAverage - UNPROVEN_QUARTERBACK_PENALTY

    weightedYards = {}
    weightedDropbacks = {}
    for game in games:
        weight = 0.5 ** (gameAgeInWeeks(game, yearOfSeason, weekOfSeason) / QUARTERBACK_HALF_LIFE_WEEKS)
        weightedYards[game.passerId] = weightedYards.get(game.passerId, 0.0) + weight * game.adjustedYards
        weightedDropbacks[game.passerId] = weightedDropbacks.get(game.passerId, 0.0) + weight * game.dropbacks
    yardsPerDropback = {
        playerId: (weightedYards[playerId] + QUARTERBACK_PRIOR_DROPBACKS * unproven) / (weightedDropbacks[playerId] + QUARTERBACK_PRIOR_DROPBACKS)
        for playerId in weightedYards
    }
    values = quarterbackValues(leagueAverage, yardsPerDropback, {}, {})

    # A team's rating was earned with whoever played quarterback in its games, so
    # its baseline is those quarterbacks' values, weighted the way the games are.
    baselineSums = {}
    baselineWeights = {}
    for game in games:
        weight = 0.5 ** (gameAgeInWeeks(game, yearOfSeason, weekOfSeason) / HALF_LIFE_WEEKS)
        baselineSums[game.teamEspnId] = baselineSums.get(game.teamEspnId, 0.0) + weight * values.pointsAboveAverage(game.passerId)
        baselineWeights[game.teamEspnId] = baselineWeights.get(game.teamEspnId, 0.0) + weight
    values.teamBaselines = {team: baselineSums[team] / baselineWeights[team] for team in baselineSums}

    for game in sorted(games, key = lambda game: (game.yearOfSeason, game.weekOfSeason), reverse = True):
        quarterbacks = values.recentQuarterbacks.setdefault(game.teamEspnId, [])
        for playerId in (game.starterId, game.passerId):
            if playerId not in quarterbacks:
                quarterbacks.append(playerId)

    return values


#-------Turning a number into a bet-------#

def spreadEdge(modelSpread, bookSpread):
    """Points of disagreement on the home team's line. Positive means the model
    likes the home team more than the book does."""
    return float(bookSpread) - float(modelSpread)


def totalEdge(modelTotal, bookTotal):
    """Positive means the model expects more points than the book."""
    return float(modelTotal) - float(bookTotal)


def coverProbability(edgePoints, standardDeviation = MARGIN_STANDARD_DEVIATION):
    """Chance of covering with this many points of edge, IF the model's number were
    the true expectation. The backtest shows the closing line is the better number,
    so read this as an upper bound, not a forecast."""
    return 0.5 * (1 + math.erf(edgePoints / (standardDeviation * math.sqrt(2))))


# One game's prediction next to the book's lines and what happened. Spreads are
# the home team's line (negative = home favored), the way nflMatch stores them.
predictedGame = namedtuple('predictedGame', [
    'yearOfSeason', 'weekOfSeason', 'modelSpread', 'modelTotal', 'bookSpread', 'bookTotal', 'actualSpread', 'actualTotal',
])


#-------Database-------#

# Completed pass, incomplete pass, sack: the plays that have a passer.
PASSING_PLAY_TYPES = (2, 3, 4)
QUARTERBACK_POSITION = 1

startingQuarterback = namedtuple('startingQuarterback', ['playerId', 'name', 'hasPlayed'])


def loadSeasonGames(yearOfSeason):
    """One season's completed regular season and playoff games."""
    matches = nflMatch.objects.filter(
        yearOfSeason = yearOfSeason, completed = True, preseason = False, weekOfSeason__gte = 1,
        homeTeamPoints__isnull = False, awayTeamPoints__isnull = False,
        homeTeamEspnId__isnull = False, awayTeamEspnId__isnull = False,
    ).values_list('yearOfSeason', 'weekOfSeason', 'homeTeamEspnId', 'awayTeamEspnId', 'homeTeamPoints', 'awayTeamPoints', 'neutralStadium')
    return [pastGame(*match) for match in matches]


def loadSeasonQuarterbackGames(yearOfSeason):
    """One season's passing, a quarterbackGame per team per game, and the names of
    the passers. Who passed comes from the play-by-play; the passing line is the
    team's box score, credited to whoever dropped back most."""
    passers = passerStatSplit.objects.filter(
        play__nflMatch__yearOfSeason = yearOfSeason, play__nflMatch__preseason = False, play__nflMatch__weekOfSeason__gte = 1,
        play__playType__in = PASSING_PLAY_TYPES,
    ).values('play__nflMatch__espnId', 'play__teamOnOffense__espnId', 'player_id', 'player__name', 'player__playerPosition').annotate(
        # Counting plays, not rows: some plays have their passer stored twice.
        dropbacks = Count('play', distinct = True), firstPlay = Min('play__sequenceNumber'))

    passersByTeamGame = {}
    names = {}
    for passer in passers:
        passersByTeamGame.setdefault((passer['play__nflMatch__espnId'], passer['play__teamOnOffense__espnId']), []).append(passer)
        names[passer['player_id']] = passer['player__name']

    passingLines = teamMatchPerformance.objects.filter(yearOfSeason = yearOfSeason, weekOfSeason__gte = 1).values_list(
        'matchEspnId', 'teamEspnId', 'weekOfSeason', 'passingAttempts', 'sacksTaken',
        'totalPassingYards', 'passingTouchdowns', 'interceptionsOnOffense', 'sackYardsLost')

    quarterbackGames = []
    for matchEspnId, teamEspnId, weekOfSeason, attempts, sacks, yards, touchdowns, interceptions, sackYards in passingLines:
        passersInGame = passersByTeamGame.get((matchEspnId, teamEspnId))
        dropbacks = (attempts or 0) + (sacks or 0)
        if not passersInGame or dropbacks == 0:
            continue
        passer = max(passersInGame, key = lambda passer: passer['dropbacks'])
        # The starter took the first dropback. A receiver throwing on a trick play doesn't count.
        realPassers = [passer for passer in passersInGame if passer['player__playerPosition'] == QUARTERBACK_POSITION or passer['dropbacks'] >= 5]
        starter = min(realPassers or passersInGame, key = lambda passer: passer['firstPlay'])
        quarterbackGames.append(quarterbackGame(
            yearOfSeason, weekOfSeason, teamEspnId, starter['player_id'], passer['player_id'], dropbacks,
            adjustedPassingYards(yards or 0, touchdowns or 0, interceptions or 0, float(sackYards or 0)),
        ))
    return quarterbackGames, names


def quarterbacksOut(yearOfSeason, weekOfSeason):
    """Ids of the quarterbacks whose latest status for this week has them sitting out."""
    statuses = playerWeekStatus.objects.filter(
        yearOfSeason = yearOfSeason, weekOfSeason = weekOfSeason, player__playerPosition = QUARTERBACK_POSITION,
    ).order_by(F('reportDate').asc(nulls_first = True), 'id').values_list('player_id', 'playerStatus')
    latestStatus = {playerId: status for playerId, status in statuses}
    return {playerId for playerId, status in latestStatus.items() if status in playerWeekStatus.outStatuses}


class modelData:
    """What the model reads from the database, kept so that a caller working
    through many weeks reads each season once and fits each week once."""

    def __init__(self, useAvailability = True):
        # Whether an expected starter who is listed as out gets replaced. The
        # backtest turns this off: past weeks' statuses were often updated after
        # the game, which a bettor could not have seen.
        self.useAvailability = useAvailability
        self.gamesBySeason = {}
        self.quarterbackGamesBySeason = {}
        self.quarterbackNames = {}
        self.ratingsByWeek = {}
        self.quarterbacksOutByWeek = {}

    def seasonsFor(self, yearOfSeason):
        return range(yearOfSeason - (SEASONS_OF_HISTORY - 1), yearOfSeason + 1)

    def games(self, yearOfSeason):
        games = []
        for season in self.seasonsFor(yearOfSeason):
            if season not in self.gamesBySeason:
                self.gamesBySeason[season] = loadSeasonGames(season)
            games += self.gamesBySeason[season]
        return games

    def quarterbackGames(self, yearOfSeason):
        quarterbackGames = []
        for season in self.seasonsFor(yearOfSeason):
            if season not in self.quarterbackGamesBySeason:
                self.quarterbackGamesBySeason[season], names = loadSeasonQuarterbackGames(season)
                self.quarterbackNames.update(names)
            quarterbackGames += self.quarterbackGamesBySeason[season]
        return quarterbackGames

    def ratingsForWeek(self, yearOfSeason, weekOfSeason):
        """Team ratings and quarterback values as they stood going into this week."""
        week = (int(yearOfSeason), int(weekOfSeason))
        if week not in self.ratingsByWeek:
            ratings = fitRatings(self.games(week[0]), *week)
            ratings.quarterbacks = fitQuarterbackValues(self.quarterbackGames(week[0]), *week)
            self.ratingsByWeek[week] = ratings
        return self.ratingsByWeek[week]

    def startingQuarterback(self, yearOfSeason, weekOfSeason, teamEspnId, beforeTheGame = False):
        """The quarterback to rate the team with this week: whoever took its first
        dropback if the game has been played, otherwise the expected starter.
        beforeTheGame asks for the expected starter even if it has been played."""
        week = (int(yearOfSeason), int(weekOfSeason))
        for game in self.quarterbackGames(week[0]):
            if beforeTheGame:
                break
            if (game.yearOfSeason, game.weekOfSeason) == week and game.teamEspnId == teamEspnId:
                return startingQuarterback(game.starterId, self.quarterbackNames.get(game.starterId), True)

        quarterbacks = self.ratingsForWeek(*week).quarterbacks
        if quarterbacks is None:
            return startingQuarterback(None, None, False)
        if week not in self.quarterbacksOutByWeek:
            self.quarterbacksOutByWeek[week] = quarterbacksOut(*week) if self.useAvailability else set()
        playerId = quarterbacks.expectedStarter(teamEspnId, self.quarterbacksOutByWeek[week])
        return startingQuarterback(playerId, self.quarterbackNames.get(playerId), False)


def ratingsForWeek(yearOfSeason, weekOfSeason):
    """Team ratings as they stood going into this week."""
    return modelData().ratingsForWeek(yearOfSeason, weekOfSeason)


def backtestPredictions(firstSeason = None, lastSeason = None, quarterbacks = "actual", data = None):
    """Walk forward through every completed game that has book lines, predicting
    each week only from the games played before it. Returns predictedGame rows.

    quarterbacks says who each team is rated with:
        "actual"    whoever took its first dropback in the game. Known by kickoff,
                    though not always when a bet is placed.
        "expected"  whoever started the team's previous game, which is what the
                    model assumes before a game when it has no injury news.
        "none"      no quarterback adjustment.
    data is a modelData to reuse between calls."""
    matches = nflMatch.objects.filter(
        completed = True, preseason = False, weekOfSeason__gte = 1,
        homeTeamPoints__isnull = False, awayTeamPoints__isnull = False,
        homeTeamEspnId__isnull = False, awayTeamEspnId__isnull = False,
        matchLineHomeTeam__isnull = False, overUnderLine__gt = 0,
    ).order_by('yearOfSeason', 'weekOfSeason').values_list(
        'yearOfSeason', 'weekOfSeason', 'homeTeamEspnId', 'awayTeamEspnId', 'homeTeamPoints', 'awayTeamPoints', 'neutralStadium',
        'matchLineHomeTeam', 'overUnderLine',
    )
    if firstSeason is not None:
        matches = matches.filter(yearOfSeason__gte = firstSeason)
    if lastSeason is not None:
        matches = matches.filter(yearOfSeason__lte = lastSeason)

    if data is None:
        data = modelData(useAvailability = False)
    predictions = []
    for match in matches:
        game = pastGame(*match[:7])
        bookSpread, bookTotal = match[7], match[8]
        week = (game.yearOfSeason, game.weekOfSeason)
        ratings = data.ratingsForWeek(*week)
        if not ratings.hasEnoughGames:
            continue

        homeQuarterbackPoints = awayQuarterbackPoints = 0.0
        if quarterbacks != "none":
            beforeTheGame = quarterbacks == "expected"
            homeQuarterbackPoints = ratings.quarterbackAdjustment(game.homeTeamEspnId, data.startingQuarterback(*week, game.homeTeamEspnId, beforeTheGame).playerId)
            awayQuarterbackPoints = ratings.quarterbackAdjustment(game.awayTeamEspnId, data.startingQuarterback(*week, game.awayTeamEspnId, beforeTheGame).playerId)

        homePoints, awayPoints = ratings.expectedPoints(game.homeTeamEspnId, game.awayTeamEspnId, game.neutralStadium, homeQuarterbackPoints, awayQuarterbackPoints)
        predictions.append(predictedGame(
            game.yearOfSeason, game.weekOfSeason,
            round(awayPoints - homePoints, 1), round(homePoints + awayPoints, 1),
            float(bookSpread), float(bookTotal),
            game.awayTeamPoints - game.homeTeamPoints, game.homeTeamPoints + game.awayTeamPoints,
        ))
    return predictions


#-------Backtest-------#


def betRecord(predictions, minimumEdge, betOnTotals = False):
    """(wins, losses, pushes) from betting every game where the model disagrees
    with the book by at least minimumEdge points."""
    wins = losses = pushes = 0
    for prediction in predictions:
        if betOnTotals:
            edge = totalEdge(prediction.modelTotal, prediction.bookTotal)
            result = prediction.actualTotal - float(prediction.bookTotal)
        else:
            edge = spreadEdge(prediction.modelSpread, prediction.bookSpread)
            # The home team covers when it wins by more than the line asks.
            result = float(prediction.bookSpread) - prediction.actualSpread
        if edge == 0 or abs(edge) < minimumEdge:
            continue
        if result == 0:
            pushes += 1
        elif (edge > 0) == (result > 0):
            wins += 1
        else:
            losses += 1
    return wins, losses, pushes


def evaluatePredictions(predictions):
    """Summary numbers for a list of predictedGame rows that all have book lines."""
    gameCount = len(predictions)
    if gameCount == 0:
        return None

    def meanAbsolute(errors):
        return sum(abs(error) for error in errors) / gameCount

    # How much of the disagreement with the book shows up in the result. Slope 1
    # would mean the model is right and the book is wrong; slope 0 means the
    # disagreement carries no information.
    edges = [spreadEdge(prediction.modelSpread, prediction.bookSpread) for prediction in predictions]
    coverMargins = [float(prediction.bookSpread) - prediction.actualSpread for prediction in predictions]
    edgeMean = sum(edges) / gameCount
    coverMean = sum(coverMargins) / gameCount
    edgeVariance = sum((edge - edgeMean) ** 2 for edge in edges)
    edgeSlope = None
    if edgeVariance > 0:
        edgeSlope = sum((edge - edgeMean) * (cover - coverMean) for edge, cover in zip(edges, coverMargins)) / edgeVariance

    return {
        'games': gameCount,
        'modelSpreadError': meanAbsolute([prediction.actualSpread - prediction.modelSpread for prediction in predictions]),
        'bookSpreadError': meanAbsolute([prediction.actualSpread - float(prediction.bookSpread) for prediction in predictions]),
        'modelTotalError': meanAbsolute([prediction.actualTotal - prediction.modelTotal for prediction in predictions]),
        'bookTotalError': meanAbsolute([prediction.actualTotal - float(prediction.bookTotal) for prediction in predictions]),
        'edgeSlope': edgeSlope,
    }
