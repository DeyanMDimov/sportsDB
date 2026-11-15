"""Betting model V3: opponent-adjusted team ratings, measured in points.

Every team gets an offense rating (points it scores above an average team) and a
defense rating (points it keeps an average opponent below their usual score). All
of them are solved for at once from past results, so a team that put up 30 on a
bad defense gets less credit than one that put up 30 on a good defense.

A game's expected score is then

    home points = league average + half of home field + home offense - away defense
    away points = league average - half of home field + away offense - home defense

The functions down to evaluatePredictions are pure (no database), so the
arithmetic can be tested and backtested on its own. docs/betting-model-v3.md
explains the reasoning and how the settings below were chosen.
"""
import math
from collections import namedtuple

from django.db.models import Q

from nfl_db.models import nflMatch


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

# With fewer earlier games than this (about six weeks' worth) there is too little
# to rate teams on, and the model makes no prediction. It only comes up where the
# database is missing most of the previous season.
MINIMUM_GAMES_FOR_RATINGS = 100

# The model only names a bet when it disagrees with the book by at least this much.
MINIMUM_EDGE_POINTS = 1.0

# How far final margins typically land from this model's predicted margin
# (standard deviation, from the 2019-2026 backtest).
MARGIN_STANDARD_DEVIATION = 13.1

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

    def expectedPoints(self, homeTeamEspnId, awayTeamEspnId, neutralStadium = False):
        """(home points, away points) the model expects, to one decimal."""
        homeField = 0.0 if neutralStadium else self.homeFieldPoints
        expectedMargin = homeField + self.overallRating(homeTeamEspnId) - self.overallRating(awayTeamEspnId)
        scoringLean = (self.offenseRating(homeTeamEspnId) - self.defenseRating(awayTeamEspnId)
                       + self.offenseRating(awayTeamEspnId) - self.defenseRating(homeTeamEspnId))
        expectedTotal = 2 * self.leagueAveragePoints + TOTAL_RATING_WEIGHT * scoringLean
        return round((expectedTotal + expectedMargin) / 2, 1), round((expectedTotal - expectedMargin) / 2, 1)


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

def loadPastGames(yearOfSeason, weekOfSeason):
    """Completed regular season and playoff games a prediction for this week may use."""
    yearOfSeason = int(yearOfSeason)
    weekOfSeason = int(weekOfSeason)
    matches = nflMatch.objects.filter(
        completed = True, preseason = False, weekOfSeason__gte = 1,
        homeTeamPoints__isnull = False, awayTeamPoints__isnull = False,
        homeTeamEspnId__isnull = False, awayTeamEspnId__isnull = False,
        yearOfSeason__gte = yearOfSeason - (SEASONS_OF_HISTORY - 1),
    ).filter(
        Q(yearOfSeason__lt = yearOfSeason) | Q(yearOfSeason = yearOfSeason, weekOfSeason__lt = weekOfSeason)
    ).values_list('yearOfSeason', 'weekOfSeason', 'homeTeamEspnId', 'awayTeamEspnId', 'homeTeamPoints', 'awayTeamPoints', 'neutralStadium')
    return [pastGame(*match) for match in matches]


def ratingsForWeek(yearOfSeason, weekOfSeason):
    """Team ratings as they stood going into this week."""
    yearOfSeason = int(yearOfSeason)
    weekOfSeason = int(weekOfSeason)
    return fitRatings(loadPastGames(yearOfSeason, weekOfSeason), yearOfSeason, weekOfSeason)


def backtestPredictions(firstSeason = None, lastSeason = None):
    """Walk forward through every completed game that has book lines, predicting
    each week only from the games played before it. Returns predictedGame rows."""
    matches = nflMatch.objects.filter(
        completed = True, preseason = False, weekOfSeason__gte = 1,
        homeTeamPoints__isnull = False, awayTeamPoints__isnull = False,
        homeTeamEspnId__isnull = False, awayTeamEspnId__isnull = False,
    ).order_by('yearOfSeason', 'weekOfSeason').values_list(
        'yearOfSeason', 'weekOfSeason', 'homeTeamEspnId', 'awayTeamEspnId', 'homeTeamPoints', 'awayTeamPoints', 'neutralStadium',
        'matchLineHomeTeam', 'overUnderLine',
    )
    matches = list(matches)
    games = [pastGame(*match[:7]) for match in matches]

    ratingsByWeek = {}
    predictions = []
    for match, game in zip(matches, games):
        bookSpread, bookTotal = match[7], match[8]
        if bookSpread is None or not bookTotal:
            continue
        if firstSeason is not None and game.yearOfSeason < firstSeason:
            continue
        if lastSeason is not None and game.yearOfSeason > lastSeason:
            continue

        week = (game.yearOfSeason, game.weekOfSeason)
        if week not in ratingsByWeek:
            ratingsByWeek[week] = fitRatings(games, game.yearOfSeason, game.weekOfSeason)
        ratings = ratingsByWeek[week]
        if not ratings.hasEnoughGames:
            continue

        homePoints, awayPoints = ratings.expectedPoints(game.homeTeamEspnId, game.awayTeamEspnId, game.neutralStadium)
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
