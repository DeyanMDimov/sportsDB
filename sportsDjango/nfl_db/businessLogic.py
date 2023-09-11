from nfl_db import models
from nfl_db.models import nflMatch, teamMatchPerformance, nflTeam, driveOfPlay
from datetime import datetime
import json


    
class individualBettingModelResult:
    team1Name   =""
    team2Name   =""
    team1TotalOffensiveYardsPerGame     = 0.0
    team1TotalYardsPerPoint             = 0.0
    team1TotalDefensiveYardPerGame      = 0.0
    team1TotalDefensiveYardsPerPoint    = 0.0

    team2TotalOffensiveYardsPerGame     = 0.0
    team2TotalYardsPerPoint             = 0.0
    team2TotalDefensiveYardPerGame      = 0.0
    team2TotalDefensiveYardsPerPoint    = 0.0

    team1ExpectedYardsPerGame = 0.0
    team1ExpectedYardsPerPoint = 0.0

    team2ExpectedYardsPerGame = 0.0
    team2ExpectedYardsPerPoint = 0.0

    team1CalculatedPoints = 0.0
    team2CalculatedPoints = 0.0   

    team1ActualYards = 0.0
    team2ActualYards = 0.0 
    team1ActualPoints = 0.0
    team2ActualPoints = 0.0

    calculatedSpread = 0.0
    bookProvidedSpread = 0.0
    actualSpread = 0.0

    calculatedTotal = 0.0
    bookProvidedTotal = 0.0
    actualTotal = 0.0

    gameCompleted = False

    overUnderBet = ""
    overUnderBetIsCorrect = "None"

    lineBet = ""
    lineBetIsCorrect = "None"

    t1_OffenseYardsPerGameRank = 0
    t1_OffenseYardsPerPointRank = 0
    t1_OffenseTotalPointsRank = 0
    t1_DefenseYardsRank = 0
    t1_DefenseYardsPerPointRank = 0
    t1_DefenseTotalPointsRank = 0

    t2_OffenseYardsPerGameRank = 0
    t2_OffenseYardsPerPointRank = 0
    t2_OffenseTotalPointsRank = 0
    t2_DefenseYardsRank = 0
    t2_DefenseYardsPerPointRank = 0
    t2_DefenseTotalPointsRank = 0

    betRankScore = 0

    def __init__(self, t1name, t1oypg, t1ypp, t1dypg, t1dypp, t2name, t2oypg, t2ypp, t2dypg, t2dypp):
        
        self.team1Name = t1name
        self.team1TotalOffensiveYardsPerGame    = round(t1oypg, 2)
        self.team1TotalYardsPerPoint            = round(t1ypp, 2)
        self.team1TotalDefensiveYardsPerGame    = round(t1dypg, 2)
        self.team1TotalDefensiveYardsPerPoint   = round(t1dypp, 2)

        self.team2Name = t2name
        self.team2TotalOffensiveYardsPerGame    = round(t2oypg, 2)
        self.team2TotalYardsPerPoint            = round(t2ypp, 2)
        self.team2TotalDefensiveYardsPerGame    = round(t2dypg, 2)
        self.team2TotalDefensiveYardsPerPoint   = round(t2dypp, 2)

        self.team1ExpectedYardsPerGame  = round(((self.team1TotalOffensiveYardsPerGame + self.team2TotalDefensiveYardsPerGame)/2), 2)
        self.team1ExpectedYardsPerPoint = round(((self.team1TotalYardsPerPoint + self.team2TotalDefensiveYardsPerPoint)/2), 2)

        self.team2ExpectedYardsPerGame  = round((self.team2TotalOffensiveYardsPerGame + self.team1TotalDefensiveYardsPerGame)/2, 2)
        self.team2ExpectedYardsPerPoint = round((self.team2TotalYardsPerPoint + self.team1TotalDefensiveYardsPerPoint)/2, 2)

        self.team1CalculatedPoints = round(self.team1ExpectedYardsPerGame/self.team1ExpectedYardsPerPoint, 0)
        self.team2CalculatedPoints = round(self.team2ExpectedYardsPerGame/self.team2ExpectedYardsPerPoint, 0)

        self.calculatedSpread = self.team2CalculatedPoints - self.team1CalculatedPoints
        self.calculatedTotal = self.team1CalculatedPoints + self.team2CalculatedPoints

def generateBettingModelV1(gameData, seasonWeek, seasonYear):
    homeTeamEspnId = gameData['competitions'][0]['competitors'][0]['id']                    
    awayTeamEspnId = gameData['competitions'][0]['competitors'][1]['id']

    homeTeamPastGames = nflMatch.objects.filter(homeTeamEspnId = homeTeamEspnId, weekOfSeason__lt = seasonWeek, yearOfSeason = seasonYear, completed = True) | nflMatch.objects.filter(awayTeamEspnId = homeTeamEspnId, weekOfSeason__lt = seasonWeek, yearOfSeason = seasonYear, completed = True)

    awayTeamPastGames = nflMatch.objects.filter(homeTeamEspnId = awayTeamEspnId, weekOfSeason__lt = seasonWeek, yearOfSeason = seasonYear, completed = True) | nflMatch.objects.filter(awayTeamEspnId = awayTeamEspnId, weekOfSeason__lt = seasonWeek, yearOfSeason = seasonYear, completed = True)

    homeTeamGamesPlayed = homeTeamPastGames.count()
    awayTeamGamesPlayed = awayTeamPastGames.count()

    homeTeamTotalOffenseYards = 0
    homeTeamTotalPoints = 0

    homeTeamTotalYardsAllowed = 0
    homeTeamTotalPointsAllowed = 0

    for homeTeamPastMatch in homeTeamPastGames:
        if int(homeTeamEspnId) == int(homeTeamPastMatch.homeTeamEspnId):
            homeTeamTotalOffenseYards   += homeTeamPastMatch.homeTeamTotalYards
            homeTeamTotalPoints         += homeTeamPastMatch.homeTeamPoints
            homeTeamTotalYardsAllowed   += homeTeamPastMatch.homeTeamYardsAllowed
            homeTeamTotalPointsAllowed  += homeTeamPastMatch.homeTeamPointsAllowed
            
        else:
            homeTeamTotalOffenseYards   += homeTeamPastMatch.awayTeamTotalYards
            homeTeamTotalPoints         += homeTeamPastMatch.awayTeamPoints
            homeTeamTotalYardsAllowed   += homeTeamPastMatch.awayTeamYardsAllowed
            homeTeamTotalPointsAllowed  += homeTeamPastMatch.awayTeamPointsAllowed
           

    awayTeamTotalOffenseYards = 0
    awayTeamTotalPoints = 0

    awayTeamTotalYardsAllowed = 0
    awayTeamTotalPointsAllowed = 0


    for awayTeamPastMatch in awayTeamPastGames:
        if int(awayTeamEspnId) == int(awayTeamPastMatch.homeTeamEspnId):
            awayTeamTotalOffenseYards   += awayTeamPastMatch.homeTeamTotalYards
            awayTeamTotalPoints         += awayTeamPastMatch.homeTeamPoints
            awayTeamTotalYardsAllowed   += awayTeamPastMatch.homeTeamYardsAllowed
            awayTeamTotalPointsAllowed  += awayTeamPastMatch.homeTeamPointsAllowed
 
        else:
            awayTeamTotalOffenseYards   += awayTeamPastMatch.awayTeamTotalYards
            awayTeamTotalPoints         += awayTeamPastMatch.awayTeamPoints
            awayTeamTotalYardsAllowed   += awayTeamPastMatch.awayTeamYardsAllowed
            awayTeamTotalPointsAllowed  += awayTeamPastMatch.awayTeamPointsAllowed
       

    team1TotalOffensiveYardsPerGame     = homeTeamTotalOffenseYards/homeTeamGamesPlayed
    team1TotalYardsPerPoint             = homeTeamTotalOffenseYards/homeTeamTotalPoints
    team1TotalDefensiveYardsPerGame     = homeTeamTotalYardsAllowed/homeTeamGamesPlayed
    team1TotalDefensiveYardsPerPoint    = homeTeamTotalYardsAllowed/homeTeamTotalPointsAllowed

    team2TotalOffensiveYardsPerGame     = awayTeamTotalOffenseYards/awayTeamGamesPlayed
    team2TotalYardsPerPoint             = awayTeamTotalOffenseYards/awayTeamTotalPoints
    team2TotalDefensiveYardsPerGame     = awayTeamTotalYardsAllowed/awayTeamGamesPlayed
    team2TotalDefensiveYardsPerPoint    = awayTeamTotalYardsAllowed/awayTeamTotalPointsAllowed

    homeTeamObject = nflTeam.objects.get(espnId = homeTeamEspnId)
    homeTeamName = homeTeamObject.abbreviation

    awayTeamObject = nflTeam.objects.get(espnId = awayTeamEspnId)
    awayTeamName = awayTeamObject.abbreviation

    return individualBettingModelResult(homeTeamName, team1TotalOffensiveYardsPerGame, team1TotalYardsPerPoint, team1TotalDefensiveYardsPerGame, team1TotalDefensiveYardsPerPoint, awayTeamName, team2TotalOffensiveYardsPerGame, team2TotalYardsPerPoint, team2TotalDefensiveYardsPerGame, team2TotalDefensiveYardsPerPoint)

def generateBettingModelHistV1(gameData, week1 = False):
    homeTeamEspnId = gameData.homeTeamEspnId                    
    awayTeamEspnId = gameData.awayTeamEspnId

    homeTeamPastGames = None
    awayTeamPastGames = None
    if week1:
        getSeasonYear = gameData.yearOfSeason - 1
        homeTeamPastGames = nflMatch.objects.filter(homeTeamEspnId = homeTeamEspnId, weekOfSeason__lt = 19, yearOfSeason = getSeasonYear, completed = True) | nflMatch.objects.filter(awayTeamEspnId = homeTeamEspnId, weekOfSeason__lt = 19, yearOfSeason = getSeasonYear, completed = True)

        awayTeamPastGames = nflMatch.objects.filter(homeTeamEspnId = awayTeamEspnId, weekOfSeason__lt = 19, yearOfSeason = getSeasonYear, completed = True) | nflMatch.objects.filter(awayTeamEspnId = awayTeamEspnId, weekOfSeason__lt = 19, yearOfSeason = getSeasonYear, completed = True)
    else:
        homeTeamPastGames = nflMatch.objects.filter(homeTeamEspnId = homeTeamEspnId, weekOfSeason__lt = gameData.weekOfSeason, yearOfSeason = gameData.yearOfSeason, completed = True) | nflMatch.objects.filter(awayTeamEspnId = homeTeamEspnId, weekOfSeason__lt = gameData.weekOfSeason, yearOfSeason = gameData.yearOfSeason, completed = True)

        awayTeamPastGames = nflMatch.objects.filter(homeTeamEspnId = awayTeamEspnId, weekOfSeason__lt = gameData.weekOfSeason, yearOfSeason = gameData.yearOfSeason, completed = True) | nflMatch.objects.filter(awayTeamEspnId = awayTeamEspnId, weekOfSeason__lt = gameData.weekOfSeason, yearOfSeason = gameData.yearOfSeason, completed = True)

    homeTeamGamesPlayed = homeTeamPastGames.count()
    awayTeamGamesPlayed = awayTeamPastGames.count()

    homeTeamTotalOffenseYards = 0
    homeTeamTotalPoints = 0

    homeTeamTotalYardsAllowed = 0
    homeTeamTotalPointsAllowed = 0

    for homeTeamPastMatch in homeTeamPastGames:
        if int(homeTeamEspnId) == int(homeTeamPastMatch.homeTeamEspnId):
            homeTeamTotalOffenseYards   += homeTeamPastMatch.homeTeamTotalYards
            homeTeamTotalPoints         += homeTeamPastMatch.homeTeamPoints
            homeTeamTotalYardsAllowed   += homeTeamPastMatch.homeTeamYardsAllowed
            homeTeamTotalPointsAllowed  += homeTeamPastMatch.homeTeamPointsAllowed
            
        else:
            homeTeamTotalOffenseYards   += homeTeamPastMatch.awayTeamTotalYards
            homeTeamTotalPoints         += homeTeamPastMatch.awayTeamPoints
            homeTeamTotalYardsAllowed   += homeTeamPastMatch.awayTeamYardsAllowed
            homeTeamTotalPointsAllowed  += homeTeamPastMatch.awayTeamPointsAllowed
           

    awayTeamTotalOffenseYards = 0
    awayTeamTotalPoints = 0

    awayTeamTotalYardsAllowed = 0
    awayTeamTotalPointsAllowed = 0


    for awayTeamPastMatch in awayTeamPastGames:
        if int(awayTeamEspnId) == int(awayTeamPastMatch.homeTeamEspnId):
            awayTeamTotalOffenseYards   += awayTeamPastMatch.homeTeamTotalYards
            awayTeamTotalPoints         += awayTeamPastMatch.homeTeamPoints
            awayTeamTotalYardsAllowed   += awayTeamPastMatch.homeTeamYardsAllowed
            awayTeamTotalPointsAllowed  += awayTeamPastMatch.homeTeamPointsAllowed
 
        else:
            awayTeamTotalOffenseYards   += awayTeamPastMatch.awayTeamTotalYards
            awayTeamTotalPoints         += awayTeamPastMatch.awayTeamPoints
            awayTeamTotalYardsAllowed   += awayTeamPastMatch.awayTeamYardsAllowed
            awayTeamTotalPointsAllowed  += awayTeamPastMatch.awayTeamPointsAllowed
       

    team1TotalOffensiveYardsPerGame     = homeTeamTotalOffenseYards/homeTeamGamesPlayed
    team1TotalYardsPerPoint             = homeTeamTotalOffenseYards/homeTeamTotalPoints
    team1TotalDefensiveYardsPerGame     = homeTeamTotalYardsAllowed/homeTeamGamesPlayed
    team1TotalDefensiveYardsPerPoint    = homeTeamTotalYardsAllowed/homeTeamTotalPointsAllowed

    team2TotalOffensiveYardsPerGame     = awayTeamTotalOffenseYards/awayTeamGamesPlayed
    team2TotalYardsPerPoint             = awayTeamTotalOffenseYards/awayTeamTotalPoints
    team2TotalDefensiveYardsPerGame     = awayTeamTotalYardsAllowed/awayTeamGamesPlayed
    team2TotalDefensiveYardsPerPoint    = awayTeamTotalYardsAllowed/awayTeamTotalPointsAllowed

    homeTeamObject = nflTeam.objects.get(espnId = homeTeamEspnId)
    homeTeamName = homeTeamObject.abbreviation

    awayTeamObject = nflTeam.objects.get(espnId = awayTeamEspnId)
    awayTeamName = awayTeamObject.abbreviation

    modelResult = individualBettingModelResult(homeTeamName, team1TotalOffensiveYardsPerGame, team1TotalYardsPerPoint, team1TotalDefensiveYardsPerGame, team1TotalDefensiveYardsPerPoint, awayTeamName, team2TotalOffensiveYardsPerGame, team2TotalYardsPerPoint, team2TotalDefensiveYardsPerGame, team2TotalDefensiveYardsPerPoint)

    return modelResult

def setBetRankingsV1(v1_modelResults):
    OffenseYardsPerGame = []
    OffenseYardsPerPoint = []
    #OffenseTotalPoints = []
    DefenseYardsPerGame = []
    DefenseYardsPerPoint = []
    #DefenseTotalPoints = []
    teams = []

    teamsPlayingInWeek = len(v1_modelResults)*2

    for ind_model_result in v1_modelResults:
        OffenseYardsPerGame.append([ind_model_result.team1Name, ind_model_result.team1TotalOffensiveYardsPerGame]) 
        OffenseYardsPerGame.append([ind_model_result.team2Name, ind_model_result.team2TotalOffensiveYardsPerGame])
        #OffenseYardsPerGame[ind_model_result.team1Name] = ind_model_result.team1TotalOffensiveYardsPerGame
        #OffenseYardsPerGame[ind_model_result.team2Name] = ind_model_result.team2TotalOffensiveYardsPerGame
        OffenseYardsPerPoint.append([ind_model_result.team1Name, ind_model_result.team1TotalYardsPerPoint])
        OffenseYardsPerPoint.append([ind_model_result.team2Name, ind_model_result.team2TotalYardsPerPoint])
        #OffenseTotalPoints.append({ind_model_result.team1Name: ind_model_result.team1TotalOffensiveYardsPerGame}, {ind_model_result.team2Name: ind_model_result.team2TotalOffensiveYardsPerGame})
        DefenseYardsPerGame.append([ind_model_result.team1Name, ind_model_result.team1TotalDefensiveYardsPerGame])
        DefenseYardsPerGame.append([ind_model_result.team2Name, ind_model_result.team2TotalDefensiveYardsPerGame])
        DefenseYardsPerPoint.append([ind_model_result.team1Name, ind_model_result.team1TotalDefensiveYardsPerPoint])
        DefenseYardsPerPoint.append([ind_model_result.team2Name, ind_model_result.team2TotalDefensiveYardsPerPoint])
        #DefenseTotalPoints.append({ind_model_result.team1Name: ind_model_result.team1TotalOffensiveYardsPerGame}, {ind_model_result.team2Name: ind_model_result.team2TotalOffensiveYardsPerGame})\
        teams.append(ind_model_result.team1Name)
        teams.append(ind_model_result.team2Name)


    OffenseYardsPerGame.sort(key = lambda x: x[1], reverse = True)
    OffenseYardsPerPoint.sort(key = lambda x: x[1])
    DefenseYardsPerGame.sort(key = lambda x: x[1])
    DefenseYardsPerPoint.sort(key = lambda x: x[1], reverse = True)

    for i in range(0,teamsPlayingInWeek):
        modelResultOYPG = list(filter(lambda x: x.team1Name == OffenseYardsPerGame[i][0] or x.team2Name == OffenseYardsPerGame[i][0], v1_modelResults))[0]
        if modelResultOYPG.team1Name == OffenseYardsPerGame[i][0]:
            modelResultOYPG.t1_OffenseYardsPerGameRank = i+1
        elif modelResultOYPG.team2Name == OffenseYardsPerGame[i][0]:
            modelResultOYPG.t2_OffenseYardsPerGameRank = i+1
        
        modelResultOYPP = list(filter(lambda x: x.team1Name == OffenseYardsPerPoint[i][0] or x.team2Name == OffenseYardsPerPoint[i][0], v1_modelResults))[0]
        if modelResultOYPP.team1Name == OffenseYardsPerPoint[i][0]:
            modelResultOYPP.t1_OffenseYardsPerPointRank = i+1
        elif modelResultOYPP.team2Name == OffenseYardsPerPoint[i][0]:
            modelResultOYPP.t2_OffenseYardsPerPointRank = i+1
        
        modelResultDYPG = list(filter(lambda x: x.team1Name == DefenseYardsPerGame[i][0] or x.team2Name == DefenseYardsPerGame[i][0], v1_modelResults))[0]
        if modelResultDYPG.team1Name == DefenseYardsPerGame[i][0]:
            modelResultDYPG.t1_DefenseYardsPerGameRank = i+1
        elif modelResultDYPG.team2Name == DefenseYardsPerGame[i][0]:
            modelResultDYPG.t2_DefenseYardsPerGameRank = i+1

        modelResultDYPP = list(filter(lambda x: x.team1Name == DefenseYardsPerPoint[i][0] or x.team2Name == DefenseYardsPerPoint[i][0], v1_modelResults))[0]
        if modelResultDYPP.team1Name == DefenseYardsPerPoint[i][0]:
            modelResultDYPP.t1_DefenseYardsPerPointRank = i+1
        elif modelResultDYPP.team2Name == DefenseYardsPerPoint[i][0]:
            modelResultDYPP.t2_DefenseYardsPerPointRank = i+1

    for mr in v1_modelResults:
        mr.betRankScore = abs((mr.t1_OffenseYardsPerGameRank + mr.t1_OffenseYardsPerPointRank)-(mr.t2_DefenseYardsPerGameRank + mr.t2_DefenseYardsPerPointRank))+abs((mr.t2_OffenseYardsPerGameRank + mr.t2_OffenseYardsPerPointRank)-(mr.t1_DefenseYardsPerGameRank + mr.t1_DefenseYardsPerPointRank))

    v1_modelResults.sort(key = lambda x: x.betRankScore, reverse = True)

    for mr in v1_modelResults:
        print()
        print(mr.team1Name + " vs. " + mr.team2Name)
        print(mr.team1Name + " Offense YPG Rank: " + str(mr.t1_OffenseYardsPerGameRank))
        print(mr.team1Name + " Offense YPP Rank: " + str(mr.t1_OffenseYardsPerPointRank))
        print(mr.team1Name + " Defense YPG Rank: " + str(mr.t1_DefenseYardsPerGameRank))
        print(mr.team1Name + " Defense YPP Rank: " + str(mr.t1_DefenseYardsPerPointRank))
        print(mr.team2Name + " Offense YPG Rank: " + str(mr.t2_OffenseYardsPerGameRank))
        print(mr.team2Name + " Offense YPP Rank: " + str(mr.t2_OffenseYardsPerPointRank))
        print(mr.team2Name + " Defense YPG Rank: " + str(mr.t2_DefenseYardsPerGameRank))
        print(mr.team2Name + " Defense YPP Rank: " + str(mr.t2_DefenseYardsPerPointRank))
        print("   " + mr.team1Name + " Offense Combined Rank: " + str(mr.t1_OffenseYardsPerGameRank + mr.t1_OffenseYardsPerPointRank))
        print("   " + mr.team2Name + " Defense Combined Rank: " + str(mr.t2_DefenseYardsPerGameRank + mr.t2_DefenseYardsPerPointRank))
        print()
        print("   " + mr.team2Name + " Offense Combined Rank: " + str(mr.t2_OffenseYardsPerGameRank + mr.t2_OffenseYardsPerPointRank))
        print("   " + mr.team1Name + " Defense Combined Rank: " + str(mr.t1_DefenseYardsPerGameRank + mr.t1_DefenseYardsPerPointRank))
        print("Model Bet Rank Score = " + str(mr.betRankScore))
        print()

    return v1_modelResults

class individualV2ModelResult:
    team1Name   =""
    team2Name   =""
    
    team1TotalOffensiveYardsPerGame     = 0.0
    team1TotalYardsPerPoint             = 0.0
    team1TotalDefensiveYardPerGame      = 0.0
    team1TotalDefensiveYardsPerPoint    = 0.0

    team1ExpectedYardsPerGame = 0.0
    team1ExpectedYardsPerPoint = 0.0
    team1CalculatedPoints = 0.0
    team1ActualYards = 0.0
    team1ActualPoints = 0.0

    avg_t1_OffenseDrives = 0.0
    avg_t1_DrivesRedZone = 0.0
    avg_t1_RedZoneConv = 0.0
    avg_t1_OpponentDrives = 0.0
    avg_t1_OpponentDrivesRedZone = 0.0
    avg_t1_OpponentRedZoneConv = 0.0

    expected_t1_OffenseDrives = 0.0
    expected_t1_DrivesRedZone = 0.0
    expected_t1_RedZoneConv = 0.0

    actual_t1_OffenseDrives = 0.0
    actual_t1_DrivesRedZone = 0.0
    actual_t1_RedZoneConv = 0.0
    

    team2TotalOffensiveYardsPerGame     = 0.0
    team2TotalYardsPerPoint             = 0.0
    team2TotalDefensiveYardPerGame      = 0.0
    team2TotalDefensiveYardsPerPoint    = 0.0

    team2ExpectedYardsPerGame = 0.0
    team2ExpectedYardsPerPoint = 0.0
    team2CalculatedPoints = 0.0   
    team2ActualYards = 0.0 
    team2ActualPoints = 0.0

    avg_t2_OffenseDrives = 0.0
    avg_t2_DrivesRedZone = 0.0
    avg_t2_RedZoneConv = 0.0
    avg_t2_OpponentDrives = 0.0
    avg_t2_OpponentDrivesRedZone = 0.0
    avg_t2_OpponentRedZoneConv = 0.0

    expected_t2_OffenseDrives = 0.0
    expected_t2_DrivesRedZone = 0.0
    expected_t2_RedZoneConv = 0.0

    actual_t2_OffenseDrives = 0.0
    actual_t2_DrivesRedZone = 0.0
    actual_t2_RedZoneConv = 0.0

    expected_points_from_drives_t1 = 0.0
    expected_points_from_drives_t2 = 0.0
   

    calculatedSpread = 0.0
    bookProvidedSpread = 0.0
    actualSpread = 0.0

    calculatedTotal = 0.0
    bookProvidedTotal = 0.0
    actualTotal = 0.0

    gameCompleted = False

    overUnderBet = ""
    overUnderBetIsCorrect = "None"

    lineBet = ""
    lineBetIsCorrect = "None"

    t1_OffenseYardsPerGameRank = 0
    t1_OffenseYardsPerPointRank = 0
    t1_OffenseTotalPointsRank = 0
    t1_DefenseYardsRank = 0
    t1_DefenseYardsPerPointRank = 0
    t1_DefenseTotalPointsRank = 0

    t2_OffenseYardsPerGameRank = 0
    t2_OffenseYardsPerPointRank = 0
    t2_OffenseTotalPointsRank = 0
    t2_DefenseYardsRank = 0
    t2_DefenseYardsPerPointRank = 0
    t2_DefenseTotalPointsRank = 0

    betRankScore = 0

    def __init__(self, t1name, t1oypg, t1ypp, t1dypg, t1dypp, t2name, t2oypg, t2ypp, t2dypg, t2dypp):
        
        self.team1Name = t1name
        self.team1TotalOffensiveYardsPerGame    = round(t1oypg, 2)
        self.team1TotalYardsPerPoint            = round(t1ypp, 2)
        self.team1TotalDefensiveYardsPerGame    = round(t1dypg, 2)
        self.team1TotalDefensiveYardsPerPoint   = round(t1dypp, 2)

        self.team2Name = t2name
        self.team2TotalOffensiveYardsPerGame    = round(t2oypg, 2)
        self.team2TotalYardsPerPoint            = round(t2ypp, 2)
        self.team2TotalDefensiveYardsPerGame    = round(t2dypg, 2)
        self.team2TotalDefensiveYardsPerPoint   = round(t2dypp, 2)

        self.team1ExpectedYardsPerGame  = round(((self.team1TotalOffensiveYardsPerGame + self.team2TotalDefensiveYardsPerGame)/2), 2)
        self.team1ExpectedYardsPerPoint = round(((self.team1TotalYardsPerPoint + self.team2TotalDefensiveYardsPerPoint)/2), 2)

        self.team2ExpectedYardsPerGame  = round((self.team2TotalOffensiveYardsPerGame + self.team1TotalDefensiveYardsPerGame)/2, 2)
        self.team2ExpectedYardsPerPoint = round((self.team2TotalYardsPerPoint + self.team1TotalDefensiveYardsPerPoint)/2, 2)

        self.team1CalculatedPoints = round(self.team1ExpectedYardsPerGame/self.team1ExpectedYardsPerPoint, 0)
        self.team2CalculatedPoints = round(self.team2ExpectedYardsPerGame/self.team2ExpectedYardsPerPoint, 0)

        self.calculatedSpread = self.team2CalculatedPoints - self.team1CalculatedPoints
        self.calculatedTotal = self.team1CalculatedPoints + self.team2CalculatedPoints

    def calculateExpectedResult(self):
        self.expected_t1_OffenseDrives = round((self.avg_t1_OffenseDrives + self.avg_t2_OpponentDrives)/2, 2)
        self.expected_t1_DrivesRedZone = round((self.avg_t1_DrivesRedZone + self.avg_t2_OpponentDrivesRedZone)/2, 2)
        self.expected_t1_RedZoneConv = round((self.avg_t1_RedZoneConv + self.avg_t2_OpponentRedZoneConv)/2, 2)

        self.expected_t2_OffenseDrives = round((self.avg_t2_OffenseDrives + self.avg_t1_OpponentDrives)/2, 2)
        self.expected_t2_DrivesRedZone = round((self.avg_t2_DrivesRedZone + self.avg_t1_OpponentDrivesRedZone)/2, 2)
        self.expected_t2_RedZoneConv = round((self.avg_t2_RedZoneConv + self.avg_t1_OpponentRedZoneConv)/2, 2)

        self.expected_points_from_drives_t1 = round((self.expected_t1_DrivesRedZone-self.expected_t1_RedZoneConv)*3 + self.expected_t1_RedZoneConv*7, 0)
        self.expected_points_from_drives_t2 = round((self.expected_t2_DrivesRedZone-self.expected_t2_RedZoneConv)*3 + self.expected_t2_RedZoneConv*7, 0)

        self.calculatedSpread = self.expected_points_from_drives_t2 - self.expected_points_from_drives_t1
        self.calculatedTotal = self.expected_points_from_drives_t1 + self.expected_points_from_drives_t2

def generateBettingModelV2(gameData, seasonWeek, seasonYear):
    
    homeTeamEspnId = gameData['competitions'][0]['competitors'][0]['id']                    
    homeTeamObject = nflTeam.objects.get(espnId = homeTeamEspnId)
    homeTeamPastGames = nflMatch.objects.filter(homeTeamEspnId = homeTeamEspnId, weekOfSeason__lt = seasonWeek, yearOfSeason = seasonYear, completed = True) | nflMatch.objects.filter(awayTeamEspnId = homeTeamEspnId, weekOfSeason__lt = seasonWeek, yearOfSeason = seasonYear, completed = True)
    
    homeTeamGamesPlayed = homeTeamPastGames.count()

    homeTeamTotalOffenseYards = 0
    homeTeamTotalPoints = 0

    homeTeamTotalYardsAllowed = 0
    homeTeamTotalPointsAllowed = 0

    homeTeamOffensiveDriveCountArray = []
    homeTeamDriveRedZone = []
    homeTeamRedZoneConv = []
    homeTeamOpponentDriveCountArray = []
    homeTeamOpponentDriveRedZone = []
    homeTeamOpponentRedZoneConv = []

    homeTeamName = homeTeamObject.abbreviation
    
    for homeTeamPastMatch in homeTeamPastGames:
        if int(homeTeamEspnId) == int(homeTeamPastMatch.homeTeamEspnId):
            homeTeamTotalOffenseYards   += homeTeamPastMatch.homeTeamTotalYards
            homeTeamTotalPoints         += homeTeamPastMatch.homeTeamPoints
            homeTeamTotalYardsAllowed   += homeTeamPastMatch.homeTeamYardsAllowed
            homeTeamTotalPointsAllowed  += homeTeamPastMatch.homeTeamPointsAllowed
            
        else:
            homeTeamTotalOffenseYards   += homeTeamPastMatch.awayTeamTotalYards
            homeTeamTotalPoints         += homeTeamPastMatch.awayTeamPoints
            homeTeamTotalYardsAllowed   += homeTeamPastMatch.awayTeamYardsAllowed
            homeTeamTotalPointsAllowed  += homeTeamPastMatch.awayTeamPointsAllowed

        ht_offensiveDrivesInGame = driveOfPlay.objects.filter(nflMatch = homeTeamPastMatch, teamOnOffense = homeTeamObject)
        homeTeamOffensiveDriveCountArray.append(len(ht_offensiveDrivesInGame))

        ht_redZoneDrives = ht_offensiveDrivesInGame.filter(reachedRedZone = True)
        homeTeamDriveRedZone.append(len(ht_redZoneDrives))

        ht_redZoneDrivesConverted = ht_redZoneDrives.filter(driveResult = 1)
        homeTeamRedZoneConv.append(len(ht_redZoneDrivesConverted))

        ht_opponentDrivesInGame = driveOfPlay.objects.filter(nflMatch = homeTeamPastMatch).exclude(teamOnOffense = homeTeamObject)
        homeTeamOpponentDriveCountArray.append(len(ht_opponentDrivesInGame))

        ht_opponentRedZoneDrives = ht_opponentDrivesInGame.filter(reachedRedZone = True)
        homeTeamOpponentDriveRedZone.append(len(ht_opponentRedZoneDrives))

        ht_opponentRedZoneDrivesConverted = ht_opponentRedZoneDrives.filter(driveResult = 1)
        homeTeamOpponentRedZoneConv.append(len(ht_opponentRedZoneDrivesConverted))

        
    avg_ht_OffenseDrives = round(sum(homeTeamOffensiveDriveCountArray)/len(homeTeamOffensiveDriveCountArray), 2)
    avg_ht_DrivesRedZone = round(sum(homeTeamDriveRedZone)/len(homeTeamDriveRedZone), 2)
    avg_ht_RedZoneConv = round(sum(homeTeamRedZoneConv)/len(homeTeamRedZoneConv), 2)
    avg_ht_OpponentDrives = round(sum(homeTeamOpponentDriveCountArray)/len(homeTeamOpponentDriveCountArray), 2)
    avg_ht_OpponentDrivesRedZone = round(sum(homeTeamOpponentDriveRedZone)/len(homeTeamOpponentDriveRedZone), 2)
    avg_ht_OpponentRedZoneConv = round(sum(homeTeamOpponentRedZoneConv)/len(homeTeamOpponentRedZoneConv), 2)


    team1TotalOffensiveYardsPerGame     = homeTeamTotalOffenseYards/homeTeamGamesPlayed
    team1TotalYardsPerPoint             = homeTeamTotalOffenseYards/homeTeamTotalPoints
    team1TotalDefensiveYardsPerGame     = homeTeamTotalYardsAllowed/homeTeamGamesPlayed
    team1TotalDefensiveYardsPerPoint    = homeTeamTotalYardsAllowed/homeTeamTotalPointsAllowed

    



    awayTeamEspnId = gameData['competitions'][0]['competitors'][1]['id']
    awayTeamObject = nflTeam.objects.get(espnId = awayTeamEspnId)
    awayTeamPastGames = nflMatch.objects.filter(homeTeamEspnId = awayTeamEspnId, weekOfSeason__lt = seasonWeek, yearOfSeason = seasonYear, completed = True) | nflMatch.objects.filter(awayTeamEspnId = awayTeamEspnId, weekOfSeason__lt = seasonWeek, yearOfSeason = seasonYear, completed = True)
    
    awayTeamGamesPlayed = awayTeamPastGames.count()

    awayTeamTotalOffenseYards = 0
    awayTeamTotalPoints = 0

    awayTeamTotalYardsAllowed = 0
    awayTeamTotalPointsAllowed = 0
    awayTeamName = awayTeamObject.abbreviation
    
    awayTeamOffensiveDriveCountArray = []
    awayTeamDriveRedZone = []
    awayTeamRedZoneConv = []
    awayTeamOpponentDriveCountArray = []
    awayTeamOpponentDriveRedZone = []
    awayTeamOpponentRedZoneConv = []

    for awayTeamPastMatch in awayTeamPastGames:
        if int(awayTeamEspnId) == int(awayTeamPastMatch.homeTeamEspnId):
            awayTeamTotalOffenseYards   += awayTeamPastMatch.homeTeamTotalYards
            awayTeamTotalPoints         += awayTeamPastMatch.homeTeamPoints
            awayTeamTotalYardsAllowed   += awayTeamPastMatch.homeTeamYardsAllowed
            awayTeamTotalPointsAllowed  += awayTeamPastMatch.homeTeamPointsAllowed
 
        else:
            awayTeamTotalOffenseYards   += awayTeamPastMatch.awayTeamTotalYards
            awayTeamTotalPoints         += awayTeamPastMatch.awayTeamPoints
            awayTeamTotalYardsAllowed   += awayTeamPastMatch.awayTeamYardsAllowed
            awayTeamTotalPointsAllowed  += awayTeamPastMatch.awayTeamPointsAllowed
        
        at_offensiveDrivesInGame = driveOfPlay.objects.filter(nflMatch = awayTeamPastMatch, teamOnOffense = awayTeamObject)
        awayTeamOffensiveDriveCountArray.append(len(at_offensiveDrivesInGame))

        at_redZoneDrives = at_offensiveDrivesInGame.filter(reachedRedZone = True)
        awayTeamDriveRedZone.append(len(at_redZoneDrives))

        at_redZoneDrivesConverted = at_redZoneDrives.filter(driveResult = 1)
        awayTeamRedZoneConv.append(len(at_redZoneDrivesConverted))


        at_opponentDrivesInGame = driveOfPlay.objects.filter(nflMatch = awayTeamPastMatch).exclude(teamOnOffense = awayTeamObject)
        awayTeamOpponentDriveCountArray.append(len(at_opponentDrivesInGame))

        at_opponentRedZoneDrives = at_opponentDrivesInGame.filter(reachedRedZone = True)
        awayTeamOpponentDriveRedZone.append(len(at_opponentRedZoneDrives))

        at_opponentRedZoneDrivesConverted = at_opponentRedZoneDrives.filter(driveResult = 1)
        awayTeamOpponentRedZoneConv.append(len(at_opponentRedZoneDrivesConverted))

    avg_at_OffenseDrives = round(sum(awayTeamOffensiveDriveCountArray)/len(awayTeamOffensiveDriveCountArray), 2)
    avg_at_DrivesRedZone = round(sum(awayTeamDriveRedZone)/len(awayTeamDriveRedZone), 2)
    avg_at_RedZoneConv = round(sum(awayTeamRedZoneConv)/len(awayTeamRedZoneConv), 2)
    avg_at_OpponentDrives = round(sum(awayTeamOpponentDriveCountArray)/len(awayTeamOpponentDriveCountArray), 2)
    avg_at_OpponentDrivesRedZone = round(sum(awayTeamOpponentDriveRedZone)/len(awayTeamOpponentDriveRedZone), 2)
    avg_at_OpponentRedZoneConv = round(sum(awayTeamOpponentRedZoneConv)/len(awayTeamOpponentRedZoneConv), 2)
    
    team2TotalOffensiveYardsPerGame     = awayTeamTotalOffenseYards/awayTeamGamesPlayed
    team2TotalYardsPerPoint             = awayTeamTotalOffenseYards/awayTeamTotalPoints
    team2TotalDefensiveYardsPerGame     = awayTeamTotalYardsAllowed/awayTeamGamesPlayed
    team2TotalDefensiveYardsPerPoint    = awayTeamTotalYardsAllowed/awayTeamTotalPointsAllowed
    
   

    modelResult = individualV2ModelResult(homeTeamName, team1TotalOffensiveYardsPerGame, team1TotalYardsPerPoint, team1TotalDefensiveYardsPerGame, team1TotalDefensiveYardsPerPoint, awayTeamName, team2TotalOffensiveYardsPerGame, team2TotalYardsPerPoint, team2TotalDefensiveYardsPerGame, team2TotalDefensiveYardsPerPoint)

    modelResult.avg_t1_OffenseDrives = avg_ht_OffenseDrives
    modelResult.avg_t1_DrivesRedZone = avg_ht_DrivesRedZone
    modelResult.avg_t1_RedZoneConv = avg_ht_RedZoneConv
    modelResult.avg_t1_OpponentDrives = avg_ht_OpponentDrives
    modelResult.avg_t1_OpponentDrivesRedZone = avg_ht_OpponentDrivesRedZone
    modelResult.avg_t1_OpponentRedZoneConv = avg_ht_OpponentRedZoneConv

    modelResult.avg_t2_OffenseDrives = avg_at_OffenseDrives
    modelResult.avg_t2_DrivesRedZone = avg_at_DrivesRedZone
    modelResult.avg_t2_RedZoneConv = avg_at_RedZoneConv
    modelResult.avg_t2_OpponentDrives = avg_at_OpponentDrives
    modelResult.avg_t2_OpponentDrivesRedZone = avg_at_OpponentDrivesRedZone
    modelResult.avg_t2_OpponentRedZoneConv = avg_at_OpponentRedZoneConv

    

    modelResult.calculateExpectedResult()

    return modelResult

def generateBettingModelHistV2(gameData, week1 = False):
    
    homeTeamEspnId = gameData.homeTeamEspnId
    homeTeamObject = nflTeam.objects.get(espnId = homeTeamEspnId)
    homeTeamPastGames = None
    
    if week1:
        getSeasonYear = gameData.yearOfSeason - 1
        homeTeamPastGames = nflMatch.objects.filter(homeTeamEspnId = homeTeamEspnId, weekOfSeason__lt = 19, yearOfSeason = getSeasonYear, completed = True) | nflMatch.objects.filter(awayTeamEspnId = homeTeamEspnId, weekOfSeason__lt = 19, yearOfSeason = getSeasonYear, completed = True) 
    else:
        homeTeamPastGames = nflMatch.objects.filter(homeTeamEspnId = homeTeamEspnId, weekOfSeason__lt = gameData.weekOfSeason, yearOfSeason = gameData.yearOfSeason, completed = True) | nflMatch.objects.filter(awayTeamEspnId = homeTeamEspnId, weekOfSeason__lt = gameData.weekOfSeason, yearOfSeason = gameData.yearOfSeason, completed = True)
    
    homeTeamGamesPlayed = homeTeamPastGames.count()

    homeTeamTotalOffenseYards = 0
    homeTeamTotalPoints = 0

    homeTeamTotalYardsAllowed = 0
    homeTeamTotalPointsAllowed = 0

    homeTeamOffensiveDriveCountArray = []
    homeTeamDriveRedZone = []
    homeTeamRedZoneConv = []
    homeTeamOpponentDriveCountArray = []
    homeTeamOpponentDriveRedZone = []
    homeTeamOpponentRedZoneConv = []

    homeTeamName = homeTeamObject.abbreviation
    
    for homeTeamPastMatch in homeTeamPastGames:
        if int(homeTeamEspnId) == int(homeTeamPastMatch.homeTeamEspnId):
            homeTeamTotalOffenseYards   += homeTeamPastMatch.homeTeamTotalYards
            homeTeamTotalPoints         += homeTeamPastMatch.homeTeamPoints
            homeTeamTotalYardsAllowed   += homeTeamPastMatch.homeTeamYardsAllowed
            homeTeamTotalPointsAllowed  += homeTeamPastMatch.homeTeamPointsAllowed
            
        else:
            homeTeamTotalOffenseYards   += homeTeamPastMatch.awayTeamTotalYards
            homeTeamTotalPoints         += homeTeamPastMatch.awayTeamPoints
            homeTeamTotalYardsAllowed   += homeTeamPastMatch.awayTeamYardsAllowed
            homeTeamTotalPointsAllowed  += homeTeamPastMatch.awayTeamPointsAllowed

        ht_offensiveDrivesInGame = driveOfPlay.objects.filter(nflMatch = homeTeamPastMatch, teamOnOffense = homeTeamObject)
        homeTeamOffensiveDriveCountArray.append(len(ht_offensiveDrivesInGame))

        ht_redZoneDrives = ht_offensiveDrivesInGame.filter(reachedRedZone = True)
        homeTeamDriveRedZone.append(len(ht_redZoneDrives))

        ht_redZoneDrivesConverted = ht_redZoneDrives.filter(driveResult = 1)
        homeTeamRedZoneConv.append(len(ht_redZoneDrivesConverted))

        ht_opponentDrivesInGame = driveOfPlay.objects.filter(nflMatch = homeTeamPastMatch).exclude(teamOnOffense = homeTeamObject)
        homeTeamOpponentDriveCountArray.append(len(ht_opponentDrivesInGame))

        ht_opponentRedZoneDrives = ht_opponentDrivesInGame.filter(reachedRedZone = True)
        homeTeamOpponentDriveRedZone.append(len(ht_opponentRedZoneDrives))

        ht_opponentRedZoneDrivesConverted = ht_opponentRedZoneDrives.filter(driveResult = 1)
        homeTeamOpponentRedZoneConv.append(len(ht_opponentRedZoneDrivesConverted))

        
    avg_ht_OffenseDrives = round(sum(homeTeamOffensiveDriveCountArray)/len(homeTeamOffensiveDriveCountArray), 2)
    avg_ht_DrivesRedZone = round(sum(homeTeamDriveRedZone)/len(homeTeamDriveRedZone), 2)
    avg_ht_RedZoneConv = round(sum(homeTeamRedZoneConv)/len(homeTeamRedZoneConv), 2)
    avg_ht_OpponentDrives = round(sum(homeTeamOpponentDriveCountArray)/len(homeTeamOpponentDriveCountArray), 2)
    avg_ht_OpponentDrivesRedZone = round(sum(homeTeamOpponentDriveRedZone)/len(homeTeamOpponentDriveRedZone), 2)
    avg_ht_OpponentRedZoneConv = round(sum(homeTeamOpponentRedZoneConv)/len(homeTeamOpponentRedZoneConv), 2)


    team1TotalOffensiveYardsPerGame     = homeTeamTotalOffenseYards/homeTeamGamesPlayed
    team1TotalYardsPerPoint             = homeTeamTotalOffenseYards/homeTeamTotalPoints
    team1TotalDefensiveYardsPerGame     = homeTeamTotalYardsAllowed/homeTeamGamesPlayed
    team1TotalDefensiveYardsPerPoint    = homeTeamTotalYardsAllowed/homeTeamTotalPointsAllowed

    



    awayTeamEspnId = gameData.awayTeamEspnId
    awayTeamObject = nflTeam.objects.get(espnId = awayTeamEspnId)
    awayTeamPastGames = None

    if week1:
        getSeasonYear = gameData.yearOfSeason - 1
        awayTeamPastGames = nflMatch.objects.filter(homeTeamEspnId = awayTeamEspnId, weekOfSeason__lt = 19, yearOfSeason = getSeasonYear, completed = True) | nflMatch.objects.filter(awayTeamEspnId = awayTeamEspnId, weekOfSeason__lt = 19, yearOfSeason = getSeasonYear, completed = True)
    else:
        awayTeamPastGames = nflMatch.objects.filter(homeTeamEspnId = awayTeamEspnId, weekOfSeason__lt = gameData.weekOfSeason, yearOfSeason = gameData.yearOfSeason, completed = True) | nflMatch.objects.filter(awayTeamEspnId = awayTeamEspnId, weekOfSeason__lt = gameData.weekOfSeason, yearOfSeason = gameData.yearOfSeason, completed = True)
    
    awayTeamGamesPlayed = awayTeamPastGames.count()

    awayTeamTotalOffenseYards = 0
    awayTeamTotalPoints = 0

    awayTeamTotalYardsAllowed = 0
    awayTeamTotalPointsAllowed = 0
    awayTeamName = awayTeamObject.abbreviation
    
    awayTeamOffensiveDriveCountArray = []
    awayTeamDriveRedZone = []
    awayTeamRedZoneConv = []
    awayTeamOpponentDriveCountArray = []
    awayTeamOpponentDriveRedZone = []
    awayTeamOpponentRedZoneConv = []

    for awayTeamPastMatch in awayTeamPastGames:
        if int(awayTeamEspnId) == int(awayTeamPastMatch.homeTeamEspnId):
            awayTeamTotalOffenseYards   += awayTeamPastMatch.homeTeamTotalYards
            awayTeamTotalPoints         += awayTeamPastMatch.homeTeamPoints
            awayTeamTotalYardsAllowed   += awayTeamPastMatch.homeTeamYardsAllowed
            awayTeamTotalPointsAllowed  += awayTeamPastMatch.homeTeamPointsAllowed
 
        else:
            awayTeamTotalOffenseYards   += awayTeamPastMatch.awayTeamTotalYards
            awayTeamTotalPoints         += awayTeamPastMatch.awayTeamPoints
            awayTeamTotalYardsAllowed   += awayTeamPastMatch.awayTeamYardsAllowed
            awayTeamTotalPointsAllowed  += awayTeamPastMatch.awayTeamPointsAllowed
        
        at_offensiveDrivesInGame = driveOfPlay.objects.filter(nflMatch = awayTeamPastMatch, teamOnOffense = awayTeamObject)
        awayTeamOffensiveDriveCountArray.append(len(at_offensiveDrivesInGame))

        at_redZoneDrives = at_offensiveDrivesInGame.filter(reachedRedZone = True)
        awayTeamDriveRedZone.append(len(at_redZoneDrives))

        at_redZoneDrivesConverted = at_redZoneDrives.filter(driveResult = 1)
        awayTeamRedZoneConv.append(len(at_redZoneDrivesConverted))


        at_opponentDrivesInGame = driveOfPlay.objects.filter(nflMatch = awayTeamPastMatch).exclude(teamOnOffense = awayTeamObject)
        awayTeamOpponentDriveCountArray.append(len(at_opponentDrivesInGame))

        at_opponentRedZoneDrives = at_opponentDrivesInGame.filter(reachedRedZone = True)
        awayTeamOpponentDriveRedZone.append(len(at_opponentRedZoneDrives))

        at_opponentRedZoneDrivesConverted = at_opponentRedZoneDrives.filter(driveResult = 1)
        awayTeamOpponentRedZoneConv.append(len(at_opponentRedZoneDrivesConverted))

    avg_at_OffenseDrives = round(sum(awayTeamOffensiveDriveCountArray)/len(awayTeamOffensiveDriveCountArray), 2)
    avg_at_DrivesRedZone = round(sum(awayTeamDriveRedZone)/len(awayTeamDriveRedZone), 2)
    avg_at_RedZoneConv = round(sum(awayTeamRedZoneConv)/len(awayTeamRedZoneConv), 2)
    avg_at_OpponentDrives = round(sum(awayTeamOpponentDriveCountArray)/len(awayTeamOpponentDriveCountArray), 2)
    avg_at_OpponentDrivesRedZone = round(sum(awayTeamOpponentDriveRedZone)/len(awayTeamOpponentDriveRedZone), 2)
    avg_at_OpponentRedZoneConv = round(sum(awayTeamOpponentRedZoneConv)/len(awayTeamOpponentRedZoneConv), 2)
    
    team2TotalOffensiveYardsPerGame     = awayTeamTotalOffenseYards/awayTeamGamesPlayed
    team2TotalYardsPerPoint             = awayTeamTotalOffenseYards/awayTeamTotalPoints
    team2TotalDefensiveYardsPerGame     = awayTeamTotalYardsAllowed/awayTeamGamesPlayed
    team2TotalDefensiveYardsPerPoint    = awayTeamTotalYardsAllowed/awayTeamTotalPointsAllowed
    
   

    modelResult = individualV2ModelResult(homeTeamName, team1TotalOffensiveYardsPerGame, team1TotalYardsPerPoint, team1TotalDefensiveYardsPerGame, team1TotalDefensiveYardsPerPoint, awayTeamName, team2TotalOffensiveYardsPerGame, team2TotalYardsPerPoint, team2TotalDefensiveYardsPerGame, team2TotalDefensiveYardsPerPoint)

    modelResult.avg_t1_OffenseDrives = avg_ht_OffenseDrives
    modelResult.avg_t1_DrivesRedZone = avg_ht_DrivesRedZone
    modelResult.avg_t1_RedZoneConv = avg_ht_RedZoneConv
    modelResult.avg_t1_OpponentDrives = avg_ht_OpponentDrives
    modelResult.avg_t1_OpponentDrivesRedZone = avg_ht_OpponentDrivesRedZone
    modelResult.avg_t1_OpponentRedZoneConv = avg_ht_OpponentRedZoneConv

    modelResult.avg_t2_OffenseDrives = avg_at_OffenseDrives
    modelResult.avg_t2_DrivesRedZone = avg_at_DrivesRedZone
    modelResult.avg_t2_RedZoneConv = avg_at_RedZoneConv
    modelResult.avg_t2_OpponentDrives = avg_at_OpponentDrives
    modelResult.avg_t2_OpponentDrivesRedZone = avg_at_OpponentDrivesRedZone
    modelResult.avg_t2_OpponentRedZoneConv = avg_at_OpponentRedZoneConv

    

    modelResult.calculateExpectedResult()
    
    return modelResult

def checkModelBets(bookOverUnder, bookLineHometeam, individualModelResult, team1_abr, team2_abr):
    if bookOverUnder != 0 and bookOverUnder != None:
        individualModelResult.bookProvidedSpread = bookLineHometeam
        individualModelResult.bookProvidedTotal = bookOverUnder

        if(individualModelResult.calculatedTotal > bookOverUnder):
                individualModelResult.overUnderBet = "OVER"
                if individualModelResult.actualTotal > bookOverUnder:
                    individualModelResult.overUnderBetIsCorrect = 'True'
                elif individualModelResult.actualTotal < bookOverUnder:
                    individualModelResult.overUnderBetIsCorrect = 'False'
                else:
                    individualModelResult.overUnderBetIsCorrect = 'Push'

        elif(individualModelResult.calculatedTotal < bookOverUnder):
            individualModelResult.overUnderBet = "UNDER"
            if individualModelResult.actualTotal < bookOverUnder:
                individualModelResult.overUnderBetIsCorrect = 'True'
            elif individualModelResult.actualTotal > bookOverUnder:
                    individualModelResult.overUnderBetIsCorrect = 'False'
            else:
                individualModelResult.overUnderBetIsCorrect = 'Push'
        else:
            individualModelResult.overUnderBet = 'N/A'

        if individualModelResult.calculatedSpread > bookLineHometeam:
            if bookLineHometeam > 0:
                individualModelResult.lineBet = team2_abr + " -" + str(bookLineHometeam)
            elif bookLineHometeam < 0:
                individualModelResult.lineBet = team2_abr + " +" + str(bookLineHometeam*-1)
            else:
                individualModelResult.lineBet = team2_abr + " ML"


            if individualModelResult.actualSpread > bookLineHometeam:
                individualModelResult.lineBetIsCorrect = "True"
            elif individualModelResult.actualSpread < bookLineHometeam:
                individualModelResult.lineBetIsCorrect = "False"
            else:
                individualModelResult.lineBetIsCorrect = "Push"

        elif(individualModelResult.calculatedSpread < bookLineHometeam):
            if bookLineHometeam > 0:
                individualModelResult.lineBet = team1_abr + " +" + str(bookLineHometeam)
            elif bookLineHometeam < 0:
                individualModelResult.lineBet = team1_abr + " -" + str(bookLineHometeam*-1)
            else:
                individualModelResult.lineBet = team1_abr + " ML"
            
            if individualModelResult.actualSpread < bookLineHometeam:
                individualModelResult.lineBetIsCorrect = "True"
            elif individualModelResult.actualSpread > bookLineHometeam:
                individualModelResult.lineBetIsCorrect = "False"
            else: 
                individualModelResult.lineBetIsCorrect = "Push"
        else:
            individualModelResult.lineBet = "N/A"
            
    return individualModelResult

def checkIfCurrentSeason(yearOfSeason, weekOfSeason = 0):
    currentYear = datetime.now().year
    currentMonth = datetime.now().month
    
    print(weekOfSeason)
    print(int(weekOfSeason))
    if yearOfSeason == currentYear and int(weekOfSeason) == 1:
        return False
    elif yearOfSeason == currentYear or (currentMonth >= 1 and currentMonth <= 2 and yearOfSeason + 1 == currentYear):
        return True
    else:
        return False

def resetAllMatchAssociationsForClearing():
    for match in models.nflMatch.objects.all():
        match.homeTeam.clear()
        match.awayTeam.clear()
    
    for teamPerf in models.teamMatchPerformance.objects.all():
        teamPerf.nflMatch.clear()
        teamPerf.team.clear()
        teamPerf.opponent.clear()

    deleteMatchMessage = models.nflMatch.objects.all().delete()
    deletePerfMessage = models.teamMatchPerformance.objects.all().delete()

    return ('Objects deleted. Matches - ', deleteMatchMessage, '; Performances - ', deletePerfMessage)

def resetAllPerformanceAssociationsForClearing():
    for teamPerf in models.teamMatchPerformance.objects.all():
        teamPerf.nflMatch.clear()
        teamPerf.team.clear()
        teamPerf.opponent.clear()
    
    deletePerfMessage = models.teamMatchPerformance.objects.all().delete()

    return('Performances deleted - ', deletePerfMessage)
