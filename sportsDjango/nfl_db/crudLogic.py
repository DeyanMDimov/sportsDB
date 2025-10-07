from nfl_db import models, players
from nfl_db.models import nflTeam, nflMatch, teamMatchPerformance, driveOfPlay, playByPlay, player, playerTeamTenure, playerMatchPerformance, playerMatchOffense, playerMatchDefense, playerWeekStatus
from django.db import IntegrityError
from datetime import datetime, date, time, timezone, timedelta
from zoneinfo import ZoneInfo

import json, requests, traceback

def processGameData(gameData, weekOfSeason, yearOfSeason):
    exceptionCollection = []

    matchEspnId = gameData['id']
    dateOfGameFromApi = gameData['date']
    dateOfGame = datetime.fromisoformat(dateOfGameFromApi.replace("Z", ":00"))

    homeTeamEspnId = gameData['competitions'][0]['competitors'][0]['id']
    awayTeamEspnId = gameData['competitions'][0]['competitors'][1]['id']
    homeTeamAbbr = nflTeam.objects.get(espnId = homeTeamEspnId).abbreviation
    awayTeamAbbr = nflTeam.objects.get(espnId = awayTeamEspnId).abbreviation
    
    print()
    print("Processing " + homeTeamAbbr + " vs. " + awayTeamAbbr)

    gameStatusUrl = gameData['competitions'][0]['status']['$ref']
    gameStatusResponse = requests.get(gameStatusUrl)
    gameStatus = gameStatusResponse.json()

    gameCompleted = (gameStatus['type']['completed'] == True)
    gameOvertime = ("OT" in gameStatus['type']['detail']) 

    oddsUrl = gameData['competitions'][0]['odds']['$ref']
    print(oddsUrl)
    oddsResponse = requests.get(oddsUrl)
    oddsData = oddsResponse.json()

    existingMatch = None
    existingHomeTeamPerf = None
    existingAwayTeamPerf = None

    try:
        existingMatch = nflMatch.objects.get(espnId = matchEspnId)
    except Exception as e:
        print("Match ID: " + str(matchEspnId))
        print("Home Team ID: " + str(homeTeamEspnId))
        print(e)

    try:
        existingHomeTeamPerf = teamMatchPerformance.objects.get(matchEspnId = matchEspnId, teamEspnId = homeTeamEspnId)
    except Exception as e:
        print("Match ID: " + str(matchEspnId))
        print("Home Team ID: " + str(homeTeamEspnId))
        print(e)

    try:    
        existingAwayTeamPerf = teamMatchPerformance.objects.get(matchEspnId = matchEspnId, teamEspnId = awayTeamEspnId)
    except Exception as e:
        print("Match ID: " + str(matchEspnId))

        print("Away Team ID: " + str(awayTeamEspnId))

        print(e)                        

    if datetime.now()<dateOfGame or gameCompleted==False:
        createOrUpdateScheduledNflMatch(existingMatch, gameData, oddsData, str(weekOfSeason), str(yearOfSeason))

    else:
        homeTeamStatsUrl = gameData['competitions'][0]['competitors'][0]['statistics']['$ref']
        homeTeamStatsResponse = requests.get(homeTeamStatsUrl)
        homeTeamStats = homeTeamStatsResponse.json()

        homeTeamScoreUrl = gameData['competitions'][0]['competitors'][0]['score']['$ref']
        homeTeamScoreResponse = requests.get(homeTeamScoreUrl)
        homeTeamScore = homeTeamScoreResponse.json()

        awayTeamStatsUrl = gameData['competitions'][0]['competitors'][1]['statistics']['$ref']
        awayTeamStatsResponse = requests.get(awayTeamStatsUrl)
        awayTeamStats = awayTeamStatsResponse.json()
        
        awayTeamScoreUrl = gameData['competitions'][0]['competitors'][1]['score']['$ref']
        awayTeamScoreResponse = requests.get(awayTeamScoreUrl)
        awayTeamScore = awayTeamScoreResponse.json()

        drivesDataUrl = gameData['competitions'][0]['drives']['$ref']
        drivesData = drivesDataObj(drivesDataUrl)

        playsDataUrl = gameData['competitions'][0]['details']['$ref']
        playsDataResponse = requests.get(playsDataUrl)
        playsData = playsDataResponse.json()

        playByPlayOfGame = playByPlayData(playsData)
        
        pagesOfPlaysData = playsData['pageCount']
        if pagesOfPlaysData > 1:
            for page in range(2, pagesOfPlaysData+1):
                multiPagePlaysDataUrl = playsDataUrl+"&page="+str(page)
                pagePlaysDataResponse = requests.get(multiPagePlaysDataUrl)
                pagePlaysData = pagePlaysDataResponse.json()
                playByPlayOfGame.addJSON(pagePlaysData)
        
        try:
            matchData = createOrUpdateFinishedNflMatch(existingMatch, gameData, gameCompleted, gameOvertime, homeTeamScore, homeTeamStats, awayTeamScore, awayTeamStats, oddsData, playsData, drivesData, str(weekOfSeason), str(yearOfSeason))
        except Exception as e:
            matchData = nflMatch.objects.get(espnId = matchEspnId)
            print("There was an exception")
            game_exception = []
            if len(e.args) > 1:
                game_exception.append("There were multiple exceptions when pulling game " + str(matchEspnId) + " from week " + str(weekOfSeason) + " of year " + str(yearOfSeason) + ".")
                print("Multiple exceptions in one game")
                game_exception.append(e.args[0][0][0])
                game_exception.append(e.args[0][0][1])
            else:
                game_exception.append("There was an exception when pulling game " + str(matchEspnId) + " from week " + str(weekOfSeason) + " of year " + str(yearOfSeason) + ".")
                game_exception.append(e.args[0][0][0])
                game_exception.append(e.args[0][0][1])
                game_exception.append(matchEspnId)
            exceptionCollection.append(game_exception)

 
        try:
            createOrUpdateTeamMatchPerformance(existingHomeTeamPerf, homeTeamScore, homeTeamStats, matchData.espnId, matchData.homeTeamEspnId, matchData.awayTeamEspnId, awayTeamStats, playsData, playByPlayOfGame, drivesData, seasonWeek=str(weekOfSeason), seasonYear=str(yearOfSeason))                        
        except Exception as e: 
            print("Problem with creating home team Match performance")
            game_exception = []
            game_exception.append("There was an exception when pulling game " + str(matchEspnId) + " from week " + str(weekOfSeason) + " of year " + str(yearOfSeason) + ".")
            game_exception.append(e.args[0][0][0])
            game_exception.append(e.args[0][0][1])
            game_exception.append(str(matchEspnId)+str(homeTeamEspnId))
            exceptionCollection.append(game_exception)
            
        try:
            createOrUpdateTeamMatchPerformance(existingAwayTeamPerf, awayTeamScore, awayTeamStats, matchData.espnId, matchData.awayTeamEspnId, matchData.homeTeamEspnId, homeTeamStats, playsData, playByPlayOfGame, drivesData, seasonWeek=str(weekOfSeason), seasonYear=str(yearOfSeason))    
        except Exception as e:
            print("Problem with creating away team Match performance")
            game_exception = []
            game_exception.append("There was an exception when pulling game " + str(matchEspnId) + " from week " + str(weekOfSeason) + " of year " + str(yearOfSeason) + ".")
            game_exception.append(e.args[0][0][0])
            game_exception.append(e.args[0][0][1])
            game_exception.append(str(matchEspnId)+str(awayTeamEspnId))
            exceptionCollection.append(game_exception)
        
        print("Completed.")    

        if len(exceptionCollection) > 0:
            raise Exception(exceptionCollection)

def createOrUpdateFinishedNflMatch(nflMatchObject, gameData, gameCompleted, gameOvertime, homeTeamScore, homeTeamStats, awayTeamScore, awayTeamStats, oddsData, playsData, drivesData, weekOfSeason, seasonYear):
    
    exceptionThrown = False
    exceptions = []

    mappedHomeTeamStats = teamStatsJsonMap(homeTeamStats)
    mappedAwayTeamStats = teamStatsJsonMap(awayTeamStats)

    homeTeamAbrv = nflTeam.objects.get(espnId = gameData['competitions'][0]['competitors'][0]['id']).abbreviation
    awayTeamAbrv = nflTeam.objects.get(espnId = gameData['competitions'][0]['competitors'][1]['id']).abbreviation

    homeTeamEspnId = gameData['competitions'][0]['competitors'][0]['id']
    awayTeamEspnId = gameData['competitions'][0]['competitors'][1]['id']


    if nflMatchObject == None:
        matchData = nflMatch.objects.create(
                        espnId = gameData['id'],
                        datePlayed = gameData['date'],
                        homeTeamEspnId = homeTeamEspnId,
                        awayTeamEspnId = awayTeamEspnId,
                        weekOfSeason = weekOfSeason,
                        yearOfSeason = seasonYear,
                        neutralStadium = gameData['competitions'][0]['neutralSite'],
                        playoffs = False,
                        indoorStadium = gameData['competitions'][0]['venue']['indoor'],
                        preseason= True if int(weekOfSeason) < 0 else False,
                    )

        
        
        
        
    else:
        matchData = nflMatchObject
        
    matchData.completed = gameCompleted
    matchData.overtime = gameOvertime
    matchData.homeTeamPoints                = homeTeamScore['value']
    matchData.homeTeamPointsAllowed         = awayTeamScore['value']
    matchData.homeTeamTotalYards            = mappedHomeTeamStats['passing']['totalYards']
    matchData.homeTeamYardsAllowed          = mappedAwayTeamStats['passing']['totalYards']
    matchData.homeTeamRushingYards          = mappedHomeTeamStats['rushing']['rushingYards']
    matchData.homeTeamRushYardsAllowed      = mappedAwayTeamStats['rushing']['rushingYards']
    matchData.homeTeamReceivingYards        = mappedHomeTeamStats['receiving']['receivingYards']
    matchData.homeTeamReceivingYardsAllowed = mappedAwayTeamStats['receiving']['receivingYards']
    matchData.homeTeamGiveaways             = mappedHomeTeamStats['passing']['interceptions'] + mappedHomeTeamStats['general']['fumblesLost']
    matchData.homeTeamTakeaways             = mappedAwayTeamStats['passing']['interceptions'] + mappedHomeTeamStats['general']['fumblesLost']
    matchData.homeTeamRushingTDScored       = mappedHomeTeamStats['scoring']['rushingTouchdowns']
    matchData.homeTeamRushingTDAllowed      = mappedAwayTeamStats['scoring']['rushingTouchdowns']
    matchData.homeTeamReceivingTDScored     = mappedHomeTeamStats['scoring']['receivingTouchdowns']
    matchData.homeTeamReceivingTDAllowed    = mappedAwayTeamStats['scoring']['receivingTouchdowns']
    matchData.homeTeamFGScored              = mappedHomeTeamStats['scoring']['fieldGoals']
    matchData.homeTeamFGAllowed             = mappedAwayTeamStats['scoring']['fieldGoals']
    matchData.homeTeamSpecialTeamsPointsScored  = mappedHomeTeamStats['scoring']['kickExtraPoints']
    matchData.homeTeamDefensePointsScored       = int((mappedHomeTeamStats['defensiveInterceptions']['interceptionTouchdowns']+mappedHomeTeamStats['general']['defensiveFumblesTouchdowns'])*6)
    #awayTeam stuff
    matchData.awayTeamPoints                = awayTeamScore['value']
    matchData.awayTeamPointsAllowed         = homeTeamScore['value']
    matchData.awayTeamTotalYards            = mappedAwayTeamStats['passing']['totalYards']
    matchData.awayTeamYardsAllowed          = mappedHomeTeamStats['passing']['totalYards']
    matchData.awayTeamRushingYards          = mappedAwayTeamStats['rushing']['rushingYards']
    matchData.awayTeamRushYardsAllowed      = mappedHomeTeamStats['rushing']['rushingYards']
    matchData.awayTeamReceivingYards        = mappedAwayTeamStats['receiving']['receivingYards']
    matchData.awayTeamReceivingYardsAllowed = mappedHomeTeamStats['receiving']['receivingYards']
    matchData.awayTeamGiveaways             = mappedAwayTeamStats['passing']['interceptions'] + mappedHomeTeamStats['general']['fumblesLost']
    matchData.awayTeamTakeaways             = mappedHomeTeamStats['passing']['interceptions'] + mappedHomeTeamStats['general']['fumblesLost']
    matchData.awayTeamRushingTDScored       = mappedAwayTeamStats['scoring']['rushingTouchdowns']
    matchData.awayTeamRushingTDAllowed      = mappedHomeTeamStats['scoring']['rushingTouchdowns']
    matchData.awayTeamReceivingTDScored     = mappedAwayTeamStats['scoring']['receivingTouchdowns']
    matchData.awayTeamReceivingTDAllowed    = mappedHomeTeamStats['scoring']['receivingTouchdowns']
    matchData.awayTeamFGScored              = mappedAwayTeamStats['scoring']['fieldGoals']
    matchData.awayTeamFGAllowed             = mappedHomeTeamStats['scoring']['fieldGoals']
    matchData.awayTeamSpecialTeamsPointsScored  = mappedAwayTeamStats['scoring']['kickExtraPoints']
    matchData.awayTeamDefensePointsScored       = int((mappedAwayTeamStats['defensiveInterceptions']['interceptionTouchdowns']+mappedAwayTeamStats['general']['defensiveFumblesTouchdowns'])*6)
   

    theHomeTeam = models.nflTeam.objects.get(espnId=homeTeamEspnId)
    matchData.homeTeam.add(theHomeTeam)

    theAwayTeam = models.nflTeam.objects.get(espnId=awayTeamEspnId)
    matchData.awayTeam.add(theAwayTeam)
        
    if len(oddsData['items']) > 2:
        print(str(seasonYear)) 
        if seasonYear == 2024:
            pass
        else:
            try:
                spreadSet = False
                overUnderSet = False
                homeTeamMLSet = False
                awayTeamMLSet = False
                if 'spread' in oddsData['items'][0]:
                    matchData.matchLineHomeTeam = oddsData['items'][0]['spread']
                else:
                    for i in range(1, len(oddsData['items'])):
                        if 'spread' in oddsData['items'][i]:
                            matchData.matchLineHomeTeam = oddsData['items'][i]['spread']
                            spreadSet = True
                            break
                        else: 
                            pass
                    if not spreadSet:
                        print("No Spread Data Found at all for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                        raise Exception("No spread data?")
                
                if 'overUnder' in oddsData['items'][0]:
                    matchData.overUnderLine = oddsData['items'][0]['overUnder']
                else:
                    for i in range(1, len(oddsData['items'])):
                        if 'overUnder' in oddsData['items'][i]:
                            matchData.overUnderLine = oddsData['items'][i]['overUnder']
                            overUnderSet = True
                            break
                        else: 
                            pass
                    if not overUnderSet:
                        print("No Over/Under Data Found at all for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                        raise Exception("No over/under data?")
                    
                if 'homeTeamOdds' in oddsData['items'][0]:
                    matchData.homeTeamMoneyLine = oddsData['items'][0]['homeTeamOdds']['moneyLine']
                else:
                    for i in range(1, len(oddsData['items'])):
                        if 'homeTeamOdds' in oddsData['items'][i]:
                            matchData.homeTeamMoneyLine = oddsData['items'][i]['homeTeamOdds']['moneyLine']
                            homeTeamMLSet = True
                            break
                        else: 
                            pass
                    if not homeTeamMLSet:
                        print("No Home Team Odds Data Found at all for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                        raise Exception("No home team ML data?")
                
                if 'awayTeamOdds' in oddsData['items'][0]:
                    matchData.awayTeamMoneyLine = oddsData['items'][0]['awayTeamOdds']['moneyLine']
                else:
                    for i in range(1, len(oddsData['items'])):
                        if 'awayTeamOdds' in oddsData['items'][i]:
                            matchData.awayTeamMoneyLine = oddsData['items'][i]['awayTeamOdds']['moneyLine']
                            awayTeamMLSet = True
                            break
                        else: 
                            pass
                    if not awayTeamMLSet:
                        print("No Away Team Odds Data Found at all for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                        raise Exception("No away team ML data?")

            except Exception as e:
                tback = traceback.extract_tb(e.__traceback__)
                problem_text = "Line " + str(tback[-1].lineno) + ":" + tback[-1].line
                print("Odds problem ")
                print(problem_text)
                exceptionThrown = True
                exceptions.append([problem_text, oddsData])

    
    
    try:
        for drivesPage in drivesData.drivesPages:
            for individualDrive in drivesPage['items']: 
                createDriveOfPlay(individualDrive, matchData)
    except Exception as e:
        tback = traceback.extract_tb(e.__traceback__)
        problem_text = "Line " + str(tback[-1].lineno) + ":" + tback[-1].line
        print("Drives problem ")
        print(problem_text)
        exceptions.append([problem_text, drivesPage])
        exceptionThrown = True

    
    if exceptionThrown:
        raise Exception(exceptions)

    matchData.save()    

    return matchData

def teamStatsJsonMap(teamStats):
    teamStatsCategories = teamStats['splits']['categories']
    teamStatsMapped = {}
    for catNum in range(0, len(teamStats['splits']['categories'])):

        teamStatsMapped[teamStatsCategories[catNum]['name']] = {'key': catNum}

        for statNum in range(0, len(teamStatsCategories[catNum]['stats'])):
            teamStatsMapped[teamStatsCategories[catNum]['name']][teamStatsCategories[catNum]['stats'][statNum]['name']] = teamStatsCategories[catNum]['stats'][statNum]['value']
            
    return teamStatsMapped

def createOrUpdateScheduledNflMatch(nflMatchObject, gameData, oddsData, weekOfSeason, seasonYear):

    homeTeamAbrv = nflTeam.objects.get(espnId = gameData['competitions'][0]['competitors'][0]['id']).abbreviation
    awayTeamAbrv = nflTeam.objects.get(espnId = gameData['competitions'][0]['competitors'][1]['id']).abbreviation
    
    if nflMatchObject == None:
        matchData = nflMatch.objects.create(
                        espnId = gameData['id'],
                        datePlayed = gameData['date'],
                        homeTeamEspnId = gameData['competitions'][0]['competitors'][0]['id'],
                        awayTeamEspnId = gameData['competitions'][0]['competitors'][1]['id'],
                        completed = (gameData['competitions'][0]['boxscoreSource']['state'] == "full"),
                        weekOfSeason = weekOfSeason,
                        yearOfSeason = seasonYear,
                        neutralStadium = gameData['competitions'][0]['neutralSite'],
                        playoffs= False,
                        indoorStadium = gameData['competitions'][0]['venue']['indoor'],
                        
                    )
        homeTeamEspnId = gameData['competitions'][0]['competitors'][0]['id']
        awayTeamEspnId = gameData['competitions'][0]['competitors'][1]['id']
        matchData.homeTeam.add(models.nflTeam.objects.get(espnId=homeTeamEspnId))
        matchData.awayTeam.add(models.nflTeam.objects.get(espnId=awayTeamEspnId))
        
        if len(oddsData['items']) >= 1:
            if seasonYear == 2024:
                for i in range(1, len(oddsData['items'])):
                    if oddsData[i]['provider']['name'] == "ESPN BET":
                        if 'spread' in oddsData['items'][i]:
                            matchData.matchLineHomeTeam = oddsData['items'][i]['spread']
                        else:
                            print("No Spread Data found for ESPN BET for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                        
                        if 'overUnder' in oddsData['items'][i]:
                            matchData.overUnderLine = oddsData['items'][i]['overUnder']
                        else:
                            print("No O/U Data found for ESPN BET for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                        
                        if 'homeTeamOdds' in oddsData['items'][i]:
                            matchData.homeTeamMoneyLine = oddsData['items'][i]['homeTeamOdds']['moneyLine']
                        
                        if 'awayTeamOdds' in oddsData['items'][0]:
                            matchData.awayTeamMoneyLine = oddsData['items'][i]['awayTeamOdds']['moneyLine']
            else:
                
                try:
                    matchData.overUnderLine= oddsData['items'][0]['overUnder']
                    matchData.homeTeamMoneyLine = oddsData['items'][0]['homeTeamOdds']['moneyLine']
                    matchData.awayTeamMoneyLine = oddsData['items'][0]['awayTeamOdds']['moneyLine']
                    matchData.matchLineHomeTeam = oddsData['items'][0]['spread']
                except: 
                    pass
        
        matchData.save()    
    else:
        matchData = nflMatchObject
        if len(oddsData['items']) >= 1:
            if int(seasonYear) == 2024:
                

                for i in range(0, len(oddsData['items'])):
                    
                    if oddsData['items'][i]['provider']['name'] == "ESPN BET":
                        print()
                        print("Odds Data from ESPN BET for " + homeTeamAbrv + " vs. " + awayTeamAbrv)
                        print(oddsData['items'][i]['$ref'])
                        #print(oddsData['items'][i])
                        print()

                        if 'spread' in oddsData['items'][i]:
                            matchData.matchLineHomeTeam = oddsData['items'][i]['spread']
                        else:
                            print("No Spread Data found for ESPN BET for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                        
                        if 'overUnder' in oddsData['items'][i]:
                            matchData.overUnderLine = oddsData['items'][i]['overUnder']
                        else:
                            print("No O/U Data found for ESPN BET for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                        
                        if 'homeTeamOdds' in oddsData['items'][i]:
                            matchData.homeTeamMoneyLine = oddsData['items'][i]['homeTeamOdds']['moneyLine']
                        
                        if 'awayTeamOdds' in oddsData['items'][0]:
                            matchData.awayTeamMoneyLine = oddsData['items'][i]['awayTeamOdds']['moneyLine']
                        continue
            else:
                try:

                    matchData.overUnderLine= oddsData['items'][0]['overUnder']
                    matchData.homeTeamMoneyLine = oddsData['items'][0]['homeTeamOdds']['moneyLine']
                    matchData.awayTeamMoneyLine = oddsData['items'][0]['awayTeamOdds']['moneyLine']
                    matchData.matchLineHomeTeam = oddsData['items'][0]['spread']
                    print("Over Under: " + str(matchData.overUnderLine))
                    print("Home Team ML: " + str(matchData.homeTeamMoneyLine))
                    print("Away Team ML: " + str(matchData.awayTeamMoneyLine))
                    print("Match Line: " + str(matchData.matchLineHomeTeam))
                except Exception as e:
                    print(e)

            matchData.save()   

    return matchData

def createOrUpdateTeamMatchPerformance(existingTeamPerformance, teamScore, teamStats, matchEspnId, teamId, opponentId, opponentStats, playByPlayData, playByPlayObj, drivesData, seasonWeek, seasonYear):
    exceptions = [] 

    mappedTeamStats = teamStatsJsonMap(teamStats)

    mappedOpponentStats = teamStatsJsonMap(opponentStats)
    
    if existingTeamPerformance == None:
        
        teamPerf = teamMatchPerformance.objects.create(
            matchEspnId     = matchEspnId,
            teamEspnId      = teamId,
            weekOfSeason    = seasonWeek,
            yearOfSeason    = seasonYear,
            #-----general
            totalPointsScored       = teamScore['value'],
            totalTouchdownsScored   = mappedTeamStats['passing']['totalTouchdowns'],
            totalPenalties          = mappedTeamStats['miscellaneous']['totalPenalties'],
            totalPenaltyYards       = mappedTeamStats['miscellaneous']['totalPenaltyYards'],
            #-----offense
            totalYardsGained            = mappedTeamStats['passing']['totalYards'],
            #totalExplosivePlays         = 
            totalGiveaways              = mappedTeamStats['passing']['interceptions'] + mappedTeamStats['general']['fumblesLost'],
            #redZoneAttempts             = 
            #redZoneTDConversions        = 
            #redZoneFumbles              = 
            #redZoneFumblesLost          = 
            #redZoneInterceptions        = 
            #totalOffensePenalties       = 
            #totalOffensePenaltyYards    = 
            #-----offense-passing
            passCompletions             = mappedTeamStats['passing']['completions'],
            passingAttempts             = mappedTeamStats['passing']['passingAttempts'],
            #passPlaysTwentyFivePlus     = 
            totalPassingYards           = mappedTeamStats['receiving']['receivingYards'],
            #qbHitsTaken                 = 
            sacksTaken                  = mappedTeamStats['passing']['sacks'],
            sackYardsLost               = mappedTeamStats['passing']['sackYardsLost'],
            twoPtPassConversions        = mappedTeamStats['passing']['twoPointPassConvs'],
            twoPtPassAttempts           = mappedTeamStats['passing']['twoPtPassAttempts'],
            #-----offense-rushing
            rushingAttempts             = mappedTeamStats['rushing']['rushingAttempts'],
            rushingYards                = mappedTeamStats['rushing']['rushingYards'],
            stuffsTaken                 = mappedOpponentStats['defensive']['stuffs'],
            stuffYardsLost              = mappedOpponentStats['defensive']['stuffYards'],
            #rushingPlaysTenPlus         = 
            twoPtRushConversions        = mappedTeamStats['rushing']['twoPointRushConvs'],
            twoPtRushAttempts           = mappedTeamStats['rushing']['twoPtRushAttempts'],
            totalReceivingYards         = mappedTeamStats['receiving']['receivingYards'],
            receivingYardsAfterCatch    = mappedTeamStats['receiving']['receivingYardsAfterCatch'],
            interceptionsOnOffense      = mappedTeamStats['passing']['interceptions'],
            passingFumbles              = mappedTeamStats['passing']['passingFumbles'],
            passingFumblesLost          = mappedTeamStats['passing']['passingFumblesLost'],
            rushingFumbles              = mappedTeamStats['rushing']['rushingFumbles'],
            rushingFumblesLost          = mappedTeamStats['rushing']['rushingFumblesLost'],
            #-----defense
            # totalPointsAllowed              = 
            # totalYardsAllowedByDefense      = 
            # totalPassYardsAllowed           = 
            # totalRushYardsAllowed           = 
            defensiveTouchdownsScored       = mappedTeamStats['defensive']['defensiveTouchdowns'] + mappedTeamStats['general']['defensiveFumblesTouchdowns'],
            passesBattedDown                = mappedTeamStats['defensive']['passesBattedDown'],
            #qbHits                          = teamStats['splits']['categories'][4]['stats'][13]['value'],
            defenseSacks                    = mappedTeamStats['defensive']['sacks'],
            sackYardsGained                 = mappedTeamStats['defensive']['sackYards'],
            safetiesScored                  = mappedTeamStats['defensive']['safeties'],
            defenseStuffs                   = mappedTeamStats['defensive']['stuffs'],
            defenseInterceptions            = mappedTeamStats['defensiveInterceptions']['interceptions'],
            defenseInterceptionTouchdowns   = mappedTeamStats['defensiveInterceptions']['interceptionTouchdowns'],
            defenseInterceptionYards        = mappedTeamStats['defensiveInterceptions']['interceptionYards'],
            defenseForcedFumbles            = mappedTeamStats['general']['fumblesForced'],
            #defenseFumblesRecovered         = 
            defenseFumbleTouchdowns         = mappedTeamStats['general']['fumblesTouchdowns'],
            #totalDefensePenalties           = 
            #totalDefensePenaltyYards        = 
            #firstDownsByPenaltyGiven        = 
            #-----specialTeams
            #blockedFieldGoals           = 
            # blockedFieldGoalTouchdowns  = mappedTeamStats['defensive']['blockedFieldGoalTouchdowns'],
            #blockedPunts                = 
            #blockedPuntTouchdowns       = mappedTeamStats['defensive']['blockedPuntTouchdowns'],
            #specialTeamsPenalties       = models.SmallIntegerField(null = True, blank = True)
            #specialTeamsPenaltyYards    = models.SmallIntegerField(null = True, blank = True)
            #-----punting
            
            #opponentPinnedInsideTen     = 
            #opponentPinnedInsideFive    = 
            #-----scoring
            passingTouchdowns           = mappedTeamStats['passing']['passingTouchdowns'],
            rushingTouchdowns           = mappedTeamStats['rushing']['rushingTouchdowns'],
            totalTwoPointConvs          = mappedTeamStats['scoring']['totalTwoPointConvs'],
            fieldGoalAttempts           = mappedTeamStats['kicking']['fieldGoalAttempts'],
            fieldGoalsMade              = mappedTeamStats['kicking']['fieldGoalsMade'],
            extraPointAttempts          = mappedTeamStats['kicking']['extraPointAttempts'],
            extraPointsMade             = mappedTeamStats['kicking']['extraPointsMade'],
            #-----down and distance
            firstDowns                  = mappedTeamStats['miscellaneous']['firstDowns'],
            firstDownsRushing           = mappedTeamStats['miscellaneous']['firstDownsRushing'],
            firstDownsPassing           = mappedTeamStats['miscellaneous']['firstDownsPassing'],
            firstDownsByPenalty         = mappedTeamStats['miscellaneous']['firstDownsPenalty'],
            thirdDownAttempts           = mappedTeamStats['miscellaneous']['thirdDownAttempts'],
            thirdDownConvs              = mappedTeamStats['miscellaneous']['thirdDownConvs'],
            fourthDownAttempts          = mappedTeamStats['miscellaneous']['fourthDownAttempts'],
            fourthDownConvs             = mappedTeamStats['miscellaneous']['fourthDownConvs'],
            #drivePinnedInsideTen        = 
            #drivePinnedInsideFive       = 
            # rushPctFirstDown            = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
            # passPctFirstDown            = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
            # completionPctFirstDown      = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
            # rushPctSecondDown           = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
            # passPctSecondDown           = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
            # completionPctSecondDown     = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
            # rushPctThirdDown            = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
            # passPctThirdDown            = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
            # completionPctThirdDown      = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
            #miscellaneous
            twoPtReturns                = mappedTeamStats['defensive']['twoPtReturns'],
            onePtSafetiesMade           = mappedTeamStats['defensive']['onePtSafetiesMade'],
        )
        
        nflMatchInstance = models.nflMatch.objects.get(espnId=matchEspnId)
        associatedTeamObject = models.nflTeam.objects.get(espnId=teamId)
        opponentTeamObject = models.nflTeam.objects.get(espnId=opponentId)
        
        teamPerf.nflMatch.add(nflMatchInstance)
        teamPerf.team.add(associatedTeamObject)
        teamPerf.opponent.add(opponentTeamObject)

        if 'punting' in mappedTeamStats:
            teamPerf.totalPunts = mappedTeamStats['punting']['punts']
        else:
            teamPerf.totalPunts = 0

        if 'blockedPuntTouchdowns' in mappedTeamStats['defensive']:
            teamPerf.blockedPuntTouchdowns = mappedTeamStats['defensive']['blockedPuntTouchdowns']
        else:
            teamPerf.blockedPuntTouchdowns = 0

        if 'blockedFieldGoalTouchdowns' in mappedTeamStats['defensive']:
            teamPerf.blockedFieldGoalTouchdowns  = mappedTeamStats['defensive']['blockedFieldGoalTouchdowns']
        else:
            teamPerf.blockedFieldGoalTouchdowns = 0

        if 'QBHits' in mappedOpponentStats['defensive']:
            teamPerf.qbHitsTaken = mappedOpponentStats['defensive']['QBHits']
        else:
            teamPerf.qbHitsTaken = 0
        


        if associatedTeamObject.espnId == nflMatchInstance.homeTeamEspnId:
            teamPerf.totalPointsAllowed             = nflMatchInstance.awayTeamPoints
            teamPerf.totalPointsAllowedByDefense    = nflMatchInstance.awayTeamPoints-nflMatchInstance.awayTeamDefensePointsScored
            teamPerf.totalYardsAllowedByDefense     = nflMatchInstance.homeTeamYardsAllowed
            teamPerf.totalPassYardsAllowed          = nflMatchInstance.homeTeamReceivingYardsAllowed
            teamPerf.totalRushYardsAllowed          = nflMatchInstance.homeTeamRushYardsAllowed
            teamPerf.totalExplosivePlays            = nflMatchInstance.homeTeamExplosivePlays
            teamPerf.totalTakeaways                 = nflMatchInstance.homeTeamTakeaways
            if nflMatchInstance.neutralStadium == True:
                teamPerf.atHome = False
            else:
                teamPerf.atHome = True
        elif associatedTeamObject.espnId == nflMatchInstance.awayTeamEspnId:
            teamPerf.totalPointsAllowed             = nflMatchInstance.homeTeamPoints
            teamPerf.totalPointsAllowedByDefense    = nflMatchInstance.homeTeamPoints-nflMatchInstance.homeTeamDefensePointsScored
            teamPerf.totalYardsAllowedByDefense     = nflMatchInstance.awayTeamYardsAllowed
            teamPerf.totalPassYardsAllowed          = nflMatchInstance.awayTeamReceivingYardsAllowed
            teamPerf.totalRushYardsAllowed          = nflMatchInstance.awayTeamRushYardsAllowed
            teamPerf.totalExplosivePlays            = nflMatchInstance.awayTeamExplosivePlays
            teamPerf.totalTakeaways                 = nflMatchInstance.awayTeamTakeaways
            teamPerf.atHome = False

        teamPerf.save()
        #print()
        #print("Team Perf saved. MatchID: " + str(teamPerf.matchEspnId) + " Team ID: " + str(teamPerf.teamEspnId))

    else:
        existingTeamPerformance.matchEspnId     = matchEspnId
        existingTeamPerformance.teamEspnId      = teamId
        existingTeamPerformance.weekOfSeason    = seasonWeek
        existingTeamPerformance.yearOfSeason    = seasonYear
        #-----general
        existingTeamPerformance.totalPointsScored       = teamScore['value']
        existingTeamPerformance.totalTouchdownsScored   = mappedTeamStats['passing']['totalTouchdowns']
        existingTeamPerformance.totalPenalties          = mappedTeamStats['miscellaneous']['totalPenalties']
        existingTeamPerformance.totalPenaltyYards       = mappedTeamStats['miscellaneous']['totalPenaltyYards']

        #-----offense
        existingTeamPerformance.totalYardsGained            = mappedTeamStats['passing']['totalYards']
        #totalExplosivePlays         = 
        existingTeamPerformance.totalGiveaways              = mappedTeamStats['passing']['interceptions'] + mappedTeamStats['general']['fumblesLost']
        #redZoneAttempts             = 
        #redZoneTDConversions        = 
        #redZoneFumbles              = 
        #redZoneFumblesLost          = 
        #redZoneInterceptions        = 
        #totalOffensePenalties       = 
        #totalOffensePenaltyYards    = 
        #-----offense-passing
        existingTeamPerformance.passCompletions             = mappedTeamStats['passing']['completions']
        existingTeamPerformance.passingAttempts             = mappedTeamStats['passing']['passingAttempts']
        #passPlaysTwentyFivePlus     = 
        existingTeamPerformance.totalPassingYards           = mappedTeamStats['receiving']['receivingYards']
        #qbHitsTaken                 = 
        existingTeamPerformance.sacksTaken                  = mappedTeamStats['passing']['sacks']
        existingTeamPerformance.sackYardsLost               = mappedTeamStats['passing']['sackYardsLost']
        existingTeamPerformance.twoPtPassConversions        = mappedTeamStats['passing']['twoPointPassConvs']
        existingTeamPerformance.twoPtPassAttempts           = mappedTeamStats['passing']['twoPtPassAttempts']
        #-----offense-rushing
        existingTeamPerformance.rushingAttempts             = mappedTeamStats['rushing']['rushingAttempts']
        existingTeamPerformance.rushingYards                = mappedTeamStats['rushing']['rushingYards']
        existingTeamPerformance.stuffsTaken                 = mappedOpponentStats['defensive']['stuffs']
        existingTeamPerformance.stuffYardsLost              = mappedOpponentStats['defensive']['stuffYards']
        #rushingPlaysTenPlus         = 
        existingTeamPerformance.twoPtRushConversions        = mappedTeamStats['rushing']['twoPointRushConvs']
        existingTeamPerformance.twoPtRushAttempts           = mappedTeamStats['rushing']['twoPtRushAttempts']
        existingTeamPerformance.totalReceivingYards         = mappedTeamStats['receiving']['receivingYards']
        existingTeamPerformance.receivingYardsAfterCatch    = mappedTeamStats['receiving']['receivingYardsAfterCatch']
        existingTeamPerformance.interceptionsOnOffense      = mappedTeamStats['passing']['interceptions']
        existingTeamPerformance.passingFumbles              = mappedTeamStats['passing']['passingFumbles']
        existingTeamPerformance.passingFumblesLost          = mappedTeamStats['passing']['passingFumblesLost']
        existingTeamPerformance.rushingFumbles              = mappedTeamStats['rushing']['rushingFumbles']
        existingTeamPerformance.rushingFumblesLost          = mappedTeamStats['rushing']['rushingFumblesLost']

        #-----defense
        # totalPointsAllowed              = 
        # totalYardsAllowedByDefense      = 
        # totalPassYardsAllowed           = 
        # totalRushYardsAllowed           = 
        existingTeamPerformance.defensiveTouchdownsScored       = mappedTeamStats['defensive']['defensiveTouchdowns'] + mappedTeamStats['general']['defensiveFumblesTouchdowns']
        existingTeamPerformance.passesBattedDown                = mappedTeamStats['defensive']['passesBattedDown']
        #qbHits                          = teamStats['splits']['categories'][4]['stats'][13]['value'],
        existingTeamPerformance.defenseSacks                    = mappedTeamStats['defensive']['sacks']
        existingTeamPerformance.sackYardsGained                 = mappedTeamStats['defensive']['sackYards']
        existingTeamPerformance.safetiesScored                  = mappedTeamStats['defensive']['safeties']
        existingTeamPerformance.defenseStuffs                   = mappedTeamStats['defensive']['stuffs']
        existingTeamPerformance.defenseInterceptions            = mappedTeamStats['defensiveInterceptions']['interceptions']
        existingTeamPerformance.defenseInterceptionTouchdowns   = mappedTeamStats['defensiveInterceptions']['interceptionTouchdowns']
        existingTeamPerformance.defenseInterceptionYards        = mappedTeamStats['defensiveInterceptions']['interceptionYards']
        existingTeamPerformance.defenseForcedFumbles            = mappedTeamStats['general']['fumblesForced']
        #defenseFumblesRecovered         = 
        existingTeamPerformance.defenseFumbleTouchdowns         = mappedTeamStats['general']['fumblesTouchdowns']
        #totalDefensePenalties           = 
        #totalDefensePenaltyYards        = 
        #firstDownsByPenaltyGiven        = 
        #-----specialTeams
        #blockedFieldGoals           = 
        
        #blockedPunts                = 
        
        #specialTeamsPenalties       = models.SmallIntegerField(null = True, blank = True)
        #specialTeamsPenaltyYards    = models.SmallIntegerField(null = True, blank = True)
        #-----punting
        
        #opponentPinnedInsideTen     = 
        #opponentPinnedInsideFive    = 

        #-----scoring
        existingTeamPerformance.passingTouchdowns           = mappedTeamStats['passing']['passingTouchdowns']
        existingTeamPerformance.rushingTouchdowns           = mappedTeamStats['rushing']['rushingTouchdowns']
        existingTeamPerformance.totalTwoPointConvs          = mappedTeamStats['scoring']['totalTwoPointConvs']
        existingTeamPerformance.fieldGoalAttempts           = mappedTeamStats['kicking']['fieldGoalAttempts']
        existingTeamPerformance.fieldGoalsMade              = mappedTeamStats['kicking']['fieldGoalsMade']
        existingTeamPerformance.extraPointAttempts          = mappedTeamStats['kicking']['extraPointAttempts']
        existingTeamPerformance.extraPointsMade             = mappedTeamStats['kicking']['extraPointsMade']

        #-----down and distance
        existingTeamPerformance.firstDowns                  = mappedTeamStats['miscellaneous']['firstDowns']
        existingTeamPerformance.firstDownsRushing           = mappedTeamStats['miscellaneous']['firstDownsRushing']
        existingTeamPerformance.firstDownsPassing           = mappedTeamStats['miscellaneous']['firstDownsPassing']
        existingTeamPerformance.firstDownsByPenalty         = mappedTeamStats['miscellaneous']['firstDownsPenalty']
        existingTeamPerformance.thirdDownAttempts           = mappedTeamStats['miscellaneous']['thirdDownAttempts']
        existingTeamPerformance.thirdDownConvs              = mappedTeamStats['miscellaneous']['thirdDownConvs']
        existingTeamPerformance.fourthDownAttempts          = mappedTeamStats['miscellaneous']['fourthDownAttempts']
        existingTeamPerformance.fourthDownConvs             = mappedTeamStats['miscellaneous']['fourthDownConvs']

        #drivePinnedInsideTen        = 
        #drivePinnedInsideFive       = 
        # rushPctFirstDown            = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
        # passPctFirstDown            = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
        # completionPctFirstDown      = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
        # rushPctSecondDown           = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
        # passPctSecondDown           = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
        # completionPctSecondDown     = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
        # rushPctThirdDown            = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
        # passPctThirdDown            = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
        # completionPctThirdDown      = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
        #miscellaneous

        if 'twoPtReturns' in mappedTeamStats['defensive']:
            existingTeamPerformance.twoPtReturns                = mappedTeamStats['defensive']['twoPtReturns']
        else:
            existingTeamPerformance.twoPtReturns                = 0

        if 'onePtSafetiesMade' in mappedTeamStats['defensive']:
            existingTeamPerformance.onePtSafetiesMade           = mappedTeamStats['defensive']['onePtSafetiesMade']
        else:
            existingTeamPerformance.onePtSafetiesMade           = 0
        
        
        
        nflMatchInstance = models.nflMatch.objects.get(espnId=matchEspnId)
        associatedTeamObject = models.nflTeam.objects.get(espnId=teamId)
        opponentTeamObject = models.nflTeam.objects.get(espnId=opponentId)
        
        existingTeamPerformance.nflMatch.add(nflMatchInstance)
        existingTeamPerformance.team.add(associatedTeamObject)
        existingTeamPerformance.opponent.add(opponentTeamObject)
    
        if 'punting' in mappedTeamStats:
            existingTeamPerformance.totalPunts = mappedTeamStats['punting']['punts']
        else:
            existingTeamPerformance.totalPunts = 0

        if 'blockedPuntTouchdowns' in mappedTeamStats['defensive']:
            existingTeamPerformance.blockedPuntTouchdowns = mappedTeamStats['defensive']['blockedPuntTouchdowns']
        else:
            existingTeamPerformance.blockedPuntTouchdowns = 0

        if 'blockedFieldGoalTouchdowns' in mappedTeamStats['defensive']:
            existingTeamPerformance.blockedFieldGoalTouchdowns  = mappedTeamStats['defensive']['blockedFieldGoalTouchdowns']
        else:
            existingTeamPerformance.blockedFieldGoalTouchdowns = 0
        
        if 'QBHits' in mappedOpponentStats['defensive']:
            existingTeamPerformance.qbHitsTaken = mappedOpponentStats['defensive']['QBHits']
        else:
            existingTeamPerformance.qbHitsTaken = 0
 
        
        

        
        if associatedTeamObject.espnId == nflMatchInstance.homeTeamEspnId:
            try:

                existingTeamPerformance.totalPointsAllowed             = nflMatchInstance.awayTeamPoints
                existingTeamPerformance.totalPointsAllowedByDefense    = nflMatchInstance.awayTeamPoints-nflMatchInstance.awayTeamDefensePointsScored
                existingTeamPerformance.totalYardsAllowedByDefense     = nflMatchInstance.homeTeamYardsAllowed
                existingTeamPerformance.totalPassYardsAllowed          = nflMatchInstance.homeTeamReceivingYardsAllowed
                existingTeamPerformance.totalRushYardsAllowed          = nflMatchInstance.homeTeamRushYardsAllowed
                existingTeamPerformance.totalExplosivePlays            = nflMatchInstance.homeTeamExplosivePlays
                existingTeamPerformance.totalTakeaways                 = nflMatchInstance.homeTeamTakeaways
                if nflMatchInstance.neutralStadium == True:
                    existingTeamPerformance.atHome = False
                else:
                    existingTeamPerformance.atHome = True
            except:
                print("This has to be it")
                print(nflMatchInstance.awayTeamPoints)
                print(nflMatchInstance.awayTeamDefensePointsScored)

        elif associatedTeamObject.espnId == nflMatchInstance.awayTeamEspnId:
            existingTeamPerformance.totalPointsAllowed             = nflMatchInstance.homeTeamPoints
            existingTeamPerformance.totalPointsAllowedByDefense    = nflMatchInstance.homeTeamPoints-nflMatchInstance.homeTeamDefensePointsScored
            existingTeamPerformance.totalYardsAllowedByDefense     = nflMatchInstance.awayTeamYardsAllowed
            existingTeamPerformance.totalPassYardsAllowed          = nflMatchInstance.awayTeamReceivingYardsAllowed
            existingTeamPerformance.totalRushYardsAllowed          = nflMatchInstance.awayTeamRushYardsAllowed
            existingTeamPerformance.totalExplosivePlays            = nflMatchInstance.awayTeamExplosivePlays
            existingTeamPerformance.totalTakeaways                 = nflMatchInstance.awayTeamTakeaways
            existingTeamPerformance.atHome = False
            existingTeamPerformance.save()
        
        #print()
        #print("Team Perf saved. MatchID: " + str(existingTeamPerformance.matchEspnId) + " Team ID: " + str(existingTeamPerformance.teamEspnId))

        teamPerf = existingTeamPerformance

    try:
        captureStatsFromPlayByPlay(playByPlayData, playByPlayObj, teamId, opponentId, teamPerf)
    except Exception as e:
            tback = traceback.extract_tb(e.__traceback__)
            problem_text = "Line " + str(tback[-1].lineno) + ":" + tback[-1].line
            jsonObject = json.dumps(playByPlayData)
            exceptions.append([problem_text, jsonObject])
            raise Exception(exceptions)
        
    try:
        captureStatsFromDrives(drivesData, matchEspnId, teamId, opponentId, teamPerf)
    except Exception as e:
            tback = traceback.extract_tb(e.__traceback__)
            problem_text = "Line " + str(tback[-1].lineno) + ":" + tback[-1].line
            jsonObject = json.dumps(drivesData)
            exceptions.append([problem_text, jsonObject])
            raise Exception(exceptions)

class playByPlayData:
    playByPlayPages = []

    def __init__(self, playByPlayJSON):
        self.playByPlayPages = []
        self.playByPlayPages.append(playByPlayJSON)
    
    def addJSON(self, playByPlayJSON):
        self.playByPlayPages.append(playByPlayJSON)

class drivesDataObj:
    drivesPages = []

    def __init__(self, drivesUrl):
        self.drivesPages = []
        drivesDataResponse = requests.get(drivesUrl)
        drivesJSON = drivesDataResponse.json()

        self.drivesPages.append(drivesJSON)
        pagesOfDrivesData = drivesJSON['pageCount']

        if pagesOfDrivesData > 1:
            for page in range(2, pagesOfDrivesData+1):
                multiPageDrivesDataUrl = drivesUrl+"&page="+str(page)
                pageDrivesDataResponse = requests.get(multiPageDrivesDataUrl)
                pageDrivesData = pageDrivesDataResponse.json()
                self.drivesPages.append(pageDrivesData)

    



def captureStatsFromPlayByPlay(playByPlayData, playByPlayObj, teamId, opponentId, teamPerf):
    
    exceptions = [] 
    
    teamAbbreviation = nflTeam.objects.get(espnId = teamId).abbreviation
    opponentAbbreviation = nflTeam.objects.get(espnId = opponentId).abbreviation

    teamPenaltyText = ("PENALTY on " + teamAbbreviation)
    opponentPenaltyText = ("PENALTY on " + opponentAbbreviation)
    
    teamRushingTenPlus          = 0
    teamPassPlaysTwentyFivePlus = 0
    redZoneFumbles              = 0
    redZoneFumblesLost          = 0
    redZoneInterceptions        = 0
    totalOffensePenalties       = 0
    totalOffensePenaltyYards    = 0
    defenseFumblesRecovered     = 0
    totalDefensePenalties       = 0
    totalDefensePenaltyYards    = 0
    firstDownsByPenaltyGiven    = 0
    
    rushPctFirstDown            = 0.0
    passPctFirstDown            = 0.0
    completionPctFirstDown      = 0.0
    totalFirstDownPlays         = 0
    totalRushOnFirstDown        = 0
    totalPassOnFirstDown        = 0
    totalCompletionsOnFirstDown = 0
    rushPctSecondDown           = 0.0
    passPctSecondDown           = 0.0
    completionPctSecondDown     = 0.0
    totalSecondDownPlays        = 0
    totalRushOnSecondDown        = 0
    totalPassOnSecondDown        = 0
    totalCompletionsOnSecondDown = 0
    rushPctThirdDown            = 0.0
    passPctThirdDown            = 0.0
    completionPctThirdDown      = 0.0
    totalThirdDownPlays         = 0
    totalRushOnThirdDown        = 0
    totalPassOnThirdDown        = 0
    totalCompletionsOnThirdDown = 0

    listOfPlayTypes = []
    playPages = 0
    
  

    playByPlayPage = 0
    playNumberOnPage = 0
    
    try:
        for playByPlayData in playByPlayObj.playByPlayPages:
            for play in playByPlayData['items']:
                if 'type' not in play:
                    if 'Aborted' in play['text']:
                        if play['start']['down'] == 1:
                            totalFirstDownPlays += 1
                        elif play['start']['down'] == 2:
                            totalSecondDownPlays += 1
                        elif play['start']['down'] == 3:
                            totalThirdDownPlays +=1
                else:
                    playType = play['type']['text']
                    if playType not in listOfPlayTypes:
                        listOfPlayTypes.append(playType)

                    teamRefUrl = ""
                    try:
                        teamRefUrl = play['team']['$ref']
                    except(KeyError):
                        continue
                    
                    teamIdString = "teams/"+str(teamId)+"?"
                    


                    if teamIdString in teamRefUrl:
                        if "No Play" in play['text']: 
                            if teamPenaltyText in play['text']:
                                totalOffensePenalties += 1
                                totalOffensePenaltyYards += abs(play['statYardage'])
                                # print(teamAbbreviation + " penalty: " + str(abs(play['statYardage'])))
                            elif teamAbbreviation == "ARI" and "on ARZ" in play['text']:
                                totalOffensePenalties += 1
                                totalOffensePenaltyYards += abs(play['statYardage'])
                                print(teamAbbreviation + " penalty: " + str(abs(play['statYardage'])))
                        else:
                            if play['start']['down'] == 1:
                                totalFirstDownPlays += 1
                                if(play['type']['text'] == "Rush"):
                                    totalRushOnFirstDown += 1
                                elif (play['type']['text'] == "Pass Reception"):
                                    totalPassOnFirstDown += 1
                                    totalCompletionsOnFirstDown += 1
                                elif (play['type']['text'] == "Pass Incompletion") or (play['type']['text'] == "Sack") or (play['type']['text'] == "Interception Return Touchdown") or (play['type']['text'] == "Interception Return Touchdown"):
                                    totalPassOnFirstDown += 1
                                
                            elif play['start']['down'] == 2:
                                totalSecondDownPlays += 1
                                if(play['type']['text'] == "Rush"):
                                    totalRushOnSecondDown += 1
                                elif (play['type']['text'] == "Pass Reception"):
                                    totalPassOnSecondDown += 1
                                    totalCompletionsOnSecondDown += 1
                                elif (play['type']['text'] == "Pass Incompletion") or (play['type']['text'] == "Sack") or (play['type']['text'] == "Interception Return Touchdown") or (play['type']['text'] == "Interception Return Touchdown"):
                                    totalPassOnSecondDown += 1
                            
                            elif play['start']['down'] == 3:
                                totalThirdDownPlays +=1
                                if(play['type']['text'] == "Rush"):
                                    totalRushOnThirdDown += 1
                                elif (play['type']['text'] == "Pass Reception"):
                                    totalPassOnThirdDown += 1
                                    totalCompletionsOnThirdDown += 1
                                elif (play['type']['text'] == "Pass Incompletion") or (play['type']['text'] == "Sack") or (play['type']['text'] == "Interception Return Touchdown") or (play['type']['text'] == "Interception Return Touchdown"):
                                    totalPassOnThirdDown += 1



                        

                            # if play['type']['text'] != "Punt" and play['type']['text'] != "Kickoff" and "Field goal" not in play['type']['text']:
                            #     if play['statYardage'] < 0:
                            #         totalOffensePenalties +=1
                            #         totalOffensePenaltyYards += play['statYardage']
                            # elif play['start']['down']
                        if 'Aborted' in play['text']:
                            pass
                        elif(play['type']['text'] == "Rush" and play['statYardage']>=10):
                            if 'PENALTY' not in play['text']: 
                                teamRushingTenPlus += 1
                            # else:
                            #     if str('PENALTY on ' + opponentAbbreviation) in play['text']:
                           
                        elif (play['type']['text'] == "Pass Reception" and play['statYardage']>=25):
                            if 'PENALTY' not in play['text']: 
                                teamPassPlaysTwentyFivePlus += 1
                            

                        if(play['start']['yardsToEndzone'] <= 25):
                            if(play['type']['text'] == "Fumble Recovery (Opponent)" or play['type']['text'] == "Fumble Recovery (Opponent)"):
                                redZoneFumbles += 1
                                redZoneFumblesLost += 1
                            elif(play['type']['text'] == "Fumble Recovery (Own)"):
                                redZoneFumbles += 1
                            elif(play['type']['text'] == "Pass Interception Return" or play['type']['text'] == "Interception Return Touchdown"):
                                redZoneInterceptions += 1
                    
                    else:
                        if "No Play" in play['text'] : 
                            if teamPenaltyText in play['text']:
                                totalDefensePenalties += 1
                                totalDefensePenaltyYards += abs(play['statYardage'])
                        else:
                            if "penalty" in play['text'].lower():
                                if teamPenaltyText in play['text']:
                                    totalDefensePenalties += 1
                                    totalDefensePenaltyYards += abs(play['statYardage'])
                                if play['type']['text'] == "Pass Incompletion" and play['end']['down'] == 1:
                                    firstDownsByPenaltyGiven += 1
                            if play['type']['text'] == "Fumble Recovery (Opponent)":
                                defenseFumblesRecovered += 1
                    playNumberOnPage = playNumberOnPage + 1
            
            playByPlayPage = playByPlayPage + 1
        
    except Exception as e:
        print("Play doesn't have type: Play Page: " + str(playByPlayPage) + " Play Number: " + str(playNumberOnPage))
        raise Exception("Play doesn't have type: Play Page: " + str(playByPlayPage) + " Play Number: " + str(playNumberOnPage))


    # for pt in listOfPlayTypes:
    #     print(pt)

    if(totalFirstDownPlays != 0):
        rushPctFirstDown            = totalRushOnFirstDown/totalFirstDownPlays * 100
        passPctFirstDown            = totalPassOnFirstDown/totalFirstDownPlays * 100
        completionPctFirstDown      = totalCompletionsOnFirstDown/totalFirstDownPlays * 100

    if(totalSecondDownPlays != 0):
        rushPctSecondDown           = totalRushOnSecondDown/totalSecondDownPlays * 100
        passPctSecondDown           = totalPassOnSecondDown/totalSecondDownPlays * 100
        completionPctSecondDown     = totalCompletionsOnThirdDown/totalSecondDownPlays * 100

    if(totalThirdDownPlays != 0):
        rushPctThirdDown            = totalRushOnThirdDown/totalThirdDownPlays * 100
        passPctThirdDown            = totalPassOnThirdDown/totalThirdDownPlays * 100
        completionPctThirdDown      = totalCompletionsOnThirdDown/totalThirdDownPlays * 100
    
    
    teamPerf.rushPctFirstDown           = rushPctFirstDown
    teamPerf.passPctFirstDown           = passPctFirstDown
    teamPerf.completionPctFirstDown     = completionPctFirstDown
    
    teamPerf.rushPctSecondDown          = rushPctSecondDown
    teamPerf.passPctSecondDown          = passPctSecondDown
    teamPerf.completionPctSecondDown    = completionPctSecondDown
    
    teamPerf.rushPctThirdDown           = rushPctThirdDown
    teamPerf.passPctThirdDown           = passPctThirdDown
    teamPerf.completionPctThirdDown     = completionPctThirdDown

    teamPerf.rushingPlaysTenPlus        = teamRushingTenPlus
    teamPerf.passPlaysTwentyFivePlus    = teamPassPlaysTwentyFivePlus

    teamPerf.totalOffensePenalties      = totalOffensePenalties
    teamPerf.totalOffensePenaltyYards   = totalOffensePenaltyYards
    teamPerf.totalDefensePenalties      = totalDefensePenalties
    teamPerf.totalDefensePenaltyYards   = totalDefensePenaltyYards
    teamPerf.firstDownsByPenaltyGiven   = firstDownsByPenaltyGiven

    teamPerf.defenseFumblesRecovered    = defenseFumblesRecovered

    teamPerf.redZoneFumbles             = redZoneFumbles
    teamPerf.redZoneFumblesLost         = redZoneFumblesLost
    teamPerf.redZoneInterceptions       = redZoneInterceptions

    teamPerf.save()
    
    # except Exception as e:
    #     pass
        # tback = traceback.extract_tb(e.__traceback__)
        # problem_text = "Line " + str(tback[-1].lineno) + ":" + tback[-1].line
        # jsonObject = json.dumps(playByPlayData)
        # exceptions.append([problem_text, jsonObject])
        # raise Exception(exceptions)

def captureStatsFromDrives(drivesData, matchEspnId, teamId, opponentId, teamPerf):
    redZoneAttempts             = 0
    redZoneTDConversions        = 0
    opponentPinnedInsideTen     = 0
    opponentPinnedInsideFive    = 0
    drivePinnedInsideTen        = 0
    drivePinnedInsideFive       = 0

    listOfOffensiveDrives = driveOfPlay.objects.filter(nflMatch__espnId = matchEspnId).filter(teamOnOffense__espnId = teamId)

    for individualDrive in listOfOffensiveDrives:
        if individualDrive.reachedRedZone:
            redZoneAttempts += 1
            if individualDrive.driveResult == 1:
                redZoneTDConversions += 1
        if individualDrive.startOfDriveYardLine <=10:
            drivePinnedInsideTen += 1
            if individualDrive.startOfDriveYardLine <=5:
                drivePinnedInsideFive += 1
    
    listOfDefensiveDrives = driveOfPlay.objects.filter(nflMatch__espnId = matchEspnId).filter(teamOnOffense__espnId = opponentId)
    
    for individualDrive in listOfDefensiveDrives:
        if individualDrive.startOfDriveYardLine <=10:
            opponentPinnedInsideTen += 1
            if individualDrive.startOfDriveYardLine <=5:
                opponentPinnedInsideFive += 1
    
    teamPerf.redZoneAttempts = redZoneAttempts
    teamPerf.redZoneTDConversions = redZoneTDConversions
    teamPerf.opponentPinnedInsideTen = opponentPinnedInsideTen
    teamPerf.opponentPinnedInsideFive = opponentPinnedInsideFive
    teamPerf.drivePinnedInsideTen = drivePinnedInsideTen
    teamPerf.drivePinnedInsideFive = drivePinnedInsideFive

    teamPerf.save()

def createDriveOfPlay (individualDrive, matchData):
    
    try:
        teamOnOffenseUrl = individualDrive['team']['$ref']
    except:
        return
    teamOnOffenseId = checkTeamFromRefUrl(teamOnOffenseUrl)
    offenseTeam = nflTeam.objects.get(espnId = teamOnOffenseId)

    resultOfDrive = setResultOfDrive(individualDrive['result'], matchData.espnId)



    #print("Drive " + str(individualDrive['sequenceNumber']) + ": " + individualDrive['result'] + "     - Recorded Result: " + str(resultOfDrive))


    try:
        addedDrive = driveOfPlay.objects.create(
            espnId = individualDrive['id'],
            sequenceNumber = individualDrive['sequenceNumber'],
            nflMatch = matchData,
            teamOnOffense = offenseTeam,

            timeElapsedInSeconds = individualDrive['timeElapsed']['value'],

            driveResult = resultOfDrive,
            
            startOfDriveYardLine = individualDrive['start']['yardLine'],
            endOfDriveYardLine = individualDrive['end']['yardLine'],
            numberOffensivePlays = individualDrive['offensivePlays'],
            
            reachedRedZone = True if (individualDrive['plays']['items'][-1]['start']['yardLine'] <= 25) else False

        )
    except IntegrityError:
        addedDrive = driveOfPlay.objects.get(espnId = individualDrive['id'])
        
        addedDrive.sequenceNumber = individualDrive['sequenceNumber']
        addedDrive.nflMatch = matchData
        addedDrive.teamOnOffense = offenseTeam

        addedDrive.timeElapsedInSeconds = individualDrive['timeElapsed']['value']
        addedDrive.driveResult = resultOfDrive

        
        addedDrive.startOfDriveYardLine = individualDrive['start']['yardLine']
        addedDrive.endOfDriveYardLine = individualDrive['end']['yardLine']
        addedDrive.numberOffensivePlays = individualDrive['offensivePlays']
        
        addedDrive.reachedRedZone = True if (individualDrive['plays']['items'][-1]['start']['yardLine'] <= 25) else False
    

    

    for play in individualDrive['plays']['items']:
        if(play['start']['yardsToEndzone'] <= 25):
            addedDrive.reachedRedZone = True
        
        

    for play in individualDrive['plays']['items']:
        createPlayByPlay(play, addedDrive.espnId, matchData, offenseTeam)

    addedDrive.save()

def updateDriveOfPlay ():
    pass

def deleteDriveOfPlay ():
    driveOfPlay.objects.all().delete()
    return "All drives deleted"

def setResultOfDrive(inputResult, matchEspnId = ""):
    def switch(inputResult):
        if str.lower(inputResult) == str.lower("TD"):
            return 1
        elif str.lower(inputResult) == str.lower("FG"):
            return 2
        elif str.lower(inputResult) == str.lower("MISSED FG"):
            return 3
        elif str.lower(inputResult) == str.lower("PUNT"):
            return 4
        elif str.lower(inputResult) == str.lower("PUNT RETURN TD") or str.lower(inputResult) == str.lower("PUNT TD"):
            return 21
        elif str.lower(inputResult) == str.lower("BLOCKED PUNT"):
            return 5
        elif str.lower(inputResult) == str.lower("BLOCKED PUNT TD"):
            return 6
        elif str.lower(inputResult) == str.lower("INT"):
            return 7
        elif str.lower(inputResult) == str.lower("INT TD"):
            return 8
        elif str.lower(inputResult) == str.lower("FUMBLE"):
            return 9
        elif str.lower(inputResult) == str.lower("FUMBLE RETURN TD") or str.lower(inputResult) == str.lower("FUMBLE TD"):
            return 10
        elif str.lower(inputResult) == str.lower("DOWNS"):
            return 12
        elif str.lower(inputResult) == str.lower("END OF HALF"):
            return 13
        elif str.lower(inputResult) == str.lower("END OF GAME"):
            return 14
        elif str.lower(inputResult) == str.lower("SAFETY") or str.lower(inputResult) == str.lower("SF"):
            return 16
        elif str.lower(inputResult) == str.lower("BLOCKED FG TD") : 
            return 18
        elif str.lower(inputResult) == str.lower("BLOCKED FG") or str.lower(inputResult) == str.lower("BLOCKED FG, DOWNS"): 
            return 19
        
        else:
            print("UNEXPECTED DRIVE RESULT - ", inputResult, "Match ID: ", matchEspnId)
            return 17
    
    return switch(inputResult)

def createPlayByPlay (individualPlay, driveEspnId, matchData, offenseTeam):
    playObject = None
    
    try:
        playObject = playByPlay.objects.get(espnId = individualPlay['id'])
    except:
        pass
    
    
    try:
        playType = setPlayType(individualPlay['type']['text'], individualPlay)
    except:
        print(individualPlay['$ref'])
        playType = setPlayType("Unknown", individualPlay)    
        

    if playType == 40:
        print("playType is other. playText is: " + individualPlay['text'])
   
    try:
        if playObject == None:
            createdPlay = playByPlay.objects.create(
                espnId = individualPlay['id'],
                playType = playType,
                yardsFromEndzone = individualPlay['start']['yardsToEndzone'],
                yardsOnPlay = individualPlay['statYardage'],
                playDown = individualPlay['start']['down'],
                distanceTilFirstDown = individualPlay['start']['distance'],
                scoringPlay = individualPlay['scoringPlay'],
                driveOfPlay = models.driveOfPlay.objects.get(espnId = driveEspnId),
                teamOnOffense = offenseTeam,
                pointsScored = individualPlay['scoreValue'],
                turnover = False,
                penaltyOnPlay = False,
                nflMatch = matchData,
                quarter = individualPlay['period']['number'],
                displayClockTime = individualPlay['clock']['displayValue'],
                secondsRemainingInPeriod = int(individualPlay['clock']['value']),
                playDescription = individualPlay['text'],
                sequenceNumber = individualPlay['sequenceNumber']
            )
        else:
            createdPlay = playObject
            createdPlay.playType = playType
            createdPlay.quarter = individualPlay['period']['number']
            createdPlay.displayClockTime = individualPlay['clock']['displayValue']
            createdPlay.secondsRemainingInPeriod = int(individualPlay['clock']['value'])
            createdPlay.distanceTilFirstDown = int(individualPlay['start']['distance'])
            createdPlay.playDown = int(individualPlay['start']['down'])
            createdPlay.sequenceNumber = int(individualPlay['sequenceNumber'])
    except Exception as e:
        print("PLAY TYPE EXCEPTION IN PLAY BY PLAY CREATE: " + str(playType))
        print("The Json value: " + individualPlay['type']['text'])
        print(e)
        print(individualPlay['text'])

        raise(e)



    if createdPlay.playType in ['INTERCEPTION', 'INTERCEPTION RETURN TOUCHDOWN', 'DEFENSIVE FUMBLE RECOVERY ','DEFENSIVE FUMBLE RECOVERY TOUCHDOWN']:
        createdPlay.turnover = True

    if createdPlay.scoringPlay:
        if createdPlay.teamOnOffense.espnId == checkTeamFromRefUrl(individualPlay['start']['team']['$ref']):
            createdPlay.offenseScored = True
        else:
            createdPlay.offenseScored = False
    if 'scoringType' in individualPlay:
        if individualPlay['scoringType']['abbreviation'] == "TD":
            try:
                createdPlay.extraPointOutcome = individualPlay['pointAfterAttempt']['text']
            
            except:
                pass
    
    teamAbbreviation = createdPlay.teamOnOffense.abbreviation
    
    teamPenaltyText = ("PENALTY on " + teamAbbreviation)
    
    if "No Play" in individualPlay['text']: 
        if teamPenaltyText in individualPlay['text']:
            createdPlay.penaltyOnPlay = True
            createdPlay.penaltyIsOnOffense = True
            createdPlay.yardsGainedOrLostOnPenalty = abs(individualPlay['statYardage'])

            # print(teamAbbreviation + " penalty: " + str(abs(play['statYardage'])))
        elif teamAbbreviation == "ARI" and "on ARZ" in individualPlay['text']:
            createdPlay.penaltyOnPlay = True
            createdPlay.penaltyIsOnOffense = True
            createdPlay.yardsGainedOrLostOnPenalty = abs(individualPlay['statYardage'])
        else:
            if "penalty" in individualPlay['text'].lower():               
                createdPlay.penaltyOnPlay = True
                createdPlay.penaltyIsOnOffense = False
                createdPlay.yardsGainedOrLostOnPenalty = abs(individualPlay['statYardage'])
    
    createdPlay.save()
    

    # for athlete in individualPlay['participants']:
        
    
    

    
        
        
        
        # playType = models.SmallIntegerField(choices = playTypes, default = 1)
        # yardsFromEndzone = models.SmallIntegerField(null = True, blank = True)
        # yardsOnPlay = models.SmallIntegerField(null = True, blank = True)
        # playDown = models.SmallIntegerField(validators = [MinValueValidator(1), MaxValueValidator(4)], null = True, blank = True)
        # # rusher = models.ManyToManyField(player, blank = True, related_name = 'ballCarrier')
        # # passer = models.ManyToManyField(player, blank = True, related_name = 'passer')
        # # reciever = models.ManyToManyField(player, blank = True, related_name = 'receiver')
        # # kickReciever = models.ManyToManyField(player, blank = True, related_name = 'kickReceiver')
        # turnover = models.BooleanField()
        # penaltyOnPlay = models.BooleanField()
        # penaltyIsOnOffense = models.BooleanField(null = True, blank = True)
        # yardsGainedOrLostOnPenalty = models.SmallIntegerField(null = True, blank = True)
       


def setPlayType(inputType, indiv_play):
    
    def switch(inputType):
        if str.lower(inputType) == str.lower("Rush") or str.lower(inputType) == str.lower("Rushing Touchdown"):
            return 1
        elif str.lower(inputType) == str.lower("Pass Reception") or str.lower(inputType) == str.lower("Passing Touchdown"):
            return 2
        elif str.lower(inputType) == str.lower("Pass"):
            if indiv_play['statYardage'] > 0:
                return 2
            else:
                return 3
        elif str.lower(inputType) == str.lower("Pass Incompletion"):
            return 3
        elif str.lower(inputType) == str.lower("Sack"):
            return 4
        elif str.lower(inputType) == str.lower("PAT KICK MADE"):
            return 5
        elif str.lower(inputType) == str.lower("PAT KICK MISSED"):
            return 6
        elif str.lower(inputType) == str.lower("2PT CONVERSION SUCCESS RUSH"):
            return 7
        elif str.lower(inputType) == str.lower("2PT CONVERSION SUCCESS PASS"):
            return 8
        elif str.lower(inputType) == str.lower("2PT CONVERSION FAILED RUSH"):
            return 9
        elif str.lower(inputType) == str.lower("2PT CONVERSION FAILED PASS"):
            return 10
        elif str.lower(inputType) == str.lower("2PT CONVERSION SUCCESS OTHER"):
            return 11
        elif str.lower(inputType) == str.lower("2PT CONVERSION FAILED OTHER"):
            return 12
        elif str.lower(inputType) == str.lower("Field Goal Good"):
            return 13
        elif str.lower(inputType) == str.lower("FG KICK MISSED") or str.lower(inputType) == str.lower("Field Goal Missed"):
            return 14
        elif str.lower(inputType) == str.lower("FG KICK Blocked") or str.lower(inputType) == str.lower("Blocked Field Goal") or str.lower(inputType) == str.lower("Blocked Field Goal Touchdown"):
            return 41
        elif str.lower(inputType) == str.lower("INTERCEPTION") or str.lower(inputType) == str.lower("Pass Interception Return"):
            return 15
        elif str.lower(inputType) == str.lower("INTERCEPTION RETURN TOUCHDOWN"):
            return 16
        elif str.lower(inputType) == str.lower("OFFENSIVE FUMBLE RECOVERY") or str.lower(inputType) == str.lower("Fumble Recovery (Own)"):
            return 17
        elif str.lower(inputType) == str.lower("OFFENSIVE FUMBLE RECOVERY TOUCHDOWN"):
            return 18
        elif str.lower(inputType) == str.lower("DEFENSIVE FUMBLE RECOVERY") or str.lower(inputType) == str.lower("Fumble Recovery (Opponent)") or str.lower(inputType) == str.lower("Sack Opp Fumble Recovery"):
            return 19
        elif str.lower(inputType) == str.lower("DEFENSIVE FUMBLE RECOVERY TOUCHDOWN") or str.lower(inputType) == str.lower("Fumble Return Touchdown"):
            return 20
        elif str.lower(inputType) == str.lower("QB FUMBLE (UNCLEAR TYPE) - DEFENSIVE RECOVERY"):
            return 21
        elif str.lower(inputType) == str.lower("QB FUMBLE (UNCLEAR TYPE) - OFFENSIVE RECOVERY"):
            return 22
        elif str.lower(inputType) == str.lower("SAFETY"):
            return 23
        elif str.lower(inputType) == str.lower("PUNT") or str.lower(inputType) == str.lower("Punt Return Touchdown"):
            return 24
        elif str.lower(inputType) == str.lower("Blocked Punt") or str.lower(inputType) == str.lower("Blocked Punt Touchdown"):
            return 25
        elif str.lower(inputType) == str.lower("PUNT MUFFED PUNTING TEAM RECOVERY"):
            return 26
        elif str.lower(inputType) == str.lower("PUNT MUFFED RECEIVING TEAM RECOVERY"):
            return 27
        elif str.lower(inputType) == str.lower("Kickoff Return (Offense)") or str.lower(inputType) == str.lower("Kickoff") or str.lower(inputType) == str.lower("Kickoff Return Touchdown"):
            return 28
        elif str.lower(inputType) == str.lower("KICKOFF RECOVERY KICKING TEAM"): 
            return 29
        elif str.lower(inputType) == str.lower("KNEEL"):
            return 30
        elif str.lower(inputType) == str.lower("SPIKE"):
            return 31
        elif str.lower(inputType) == str.lower("NO PLAY/BLOWN DEAD") or str.lower(inputType) == str.lower("Penalty"):
            return 32
        elif str.lower(inputType) == str.lower("Timeout"):
            return 33
        elif str.lower(inputType) == str.lower("Official Timeout"):
            return 34
        elif str.lower(inputType) == str.lower("End Period"):
            return 35
        elif str.lower(inputType) == str.lower("Two-minute warning") or str.lower(inputType) == str.lower("Two minute warning"):
            return 36
        elif str.lower(inputType) == str.lower("End Of Half"):
            return 37
        elif str.lower(inputType) == str.lower("End Of Game"):
            return 38
        elif str.lower(inputType) == str.lower("End Of Regulation"):
            return 39
        else:
            print("UNEXPECTED PLAY TYPE - ", inputType)
            return 40
        
    return switch(inputType)

def checkTeamFromRefUrl(refUrl):
    teamEspnId = refUrl[refUrl.index('?')-2:refUrl.index('?')]
    
    if '/' in teamEspnId:
        teamEspnId = teamEspnId[1]
    
    return teamEspnId

def createTeamPerformance(teamScore, teamStats, matchEspnId, teamId, opponentId, playByPlayData, drivesData, seasonWeek, seasonYear):
    
    teamPerf = teamMatchPerformance.objects.create(
        matchEspnId      = matchEspnId,
        #nflMatch         = 
        #team             = 
        #opponent        = models.ManyToManyField(nflTeam, related_name = "opponent", blank = True)
        teamEspnId      = teamId,
        weekOfSeason    = seasonWeek,
        yearOfSeason    = seasonYear,
        #atHome
        #-----general
        totalPointsScored       = teamScore['value'],
        totalTouchdownsScored   = teamStats['splits']['categories'][1]['stats'][31]['value'],
        totalPenalties          = teamStats['splits']['categories'][10]['stats'][34]['value'],
        totalPenaltyYards       = teamStats['splits']['categories'][10]['stats'][35]['value'],
        #-----offense
        totalYardsGained            = teamStats['splits']['categories'][1]['stats'][32]['value'],
        totalGiveaways              = teamStats['splits']['categories'][10]['stats'][33]['value'],
        #-----offense-passing
        passCompletions             = teamStats['splits']['categories'][1]['stats'][2]['value'],
        passingAttempts             = teamStats['splits']['categories'][1]['stats'][12]['value'],
        totalPassingYards           = teamStats['splits']['categories'][3]['stats'][12]['value'],
        sacksTaken                  = teamStats['splits']['categories'][1]['stats'][24]['value'],
        sackYardsLost               = teamStats['splits']['categories'][1]['stats'][25]['value'],
        twoPtPassConversions        = teamStats['splits']['categories'][1]['stats'][34]['value'],
        twoPtPassAttempts           = teamStats['splits']['categories'][1]['stats'][36]['value'],
        #-----offense-rushing
        rushingAttempts             = teamStats['splits']['categories'][2]['stats'][6]['value'],
        rushingYards                = teamStats['splits']['categories'][2]['stats'][12]['value'],
        stuffsTaken                 = teamStats['splits']['categories'][2]['stats'][14]['value'],
        stuffYardsLost              = teamStats['splits']['categories'][2]['stats'][15]['value'],
        #rushingPlaysTenPlus         = 
        twoPtRushConversions        = teamStats['splits']['categories'][2]['stats'][23]['value'],
        twoPtRushAttempts           = teamStats['splits']['categories'][2]['stats'][25]['value'],
        totalReceivingYards         = teamStats['splits']['categories'][3]['stats'][12]['value'],
        receivingYardsAfterCatch    = teamStats['splits']['categories'][3]['stats'][13]['value'],
        interceptionsOnOffense      = teamStats['splits']['categories'][1]['stats'][5]['value'],
        passingFumbles              = teamStats['splits']['categories'][3]['stats'][8]['value'],
        passingFumblesLost          = teamStats['splits']['categories'][3]['stats'][9]['value'],
        rushingFumbles              = teamStats['splits']['categories'][2]['stats'][9]['value'],
        rushingFumblesLost          = teamStats['splits']['categories'][2]['stats'][10]['value'],
        #-----defense
        totalTakeaways                  = teamStats['splits']['categories'][10]['stats'][37]['value'],
        defensiveTouchdownsScored       = teamStats['splits']['categories'][5]['stats'][1]['value']+teamStats['splits']['categories'][0]['stats'][9]['value'],
        passesBattedDown                = teamStats['splits']['categories'][4]['stats'][11]['value'],
        qbHits                          = teamStats['splits']['categories'][4]['stats'][13]['value'],
        defenseSacks                    = teamStats['splits']['categories'][4]['stats'][15]['value'],
        sackYardsGained                 = teamStats['splits']['categories'][4]['stats'][18]['value'],
        safetiesScored                  = teamStats['splits']['categories'][4]['stats'][19]['value'],
        defenseStuffs                   = teamStats['splits']['categories'][4]['stats'][21]['value'],
        defenseInterceptions            = teamStats['splits']['categories'][5]['stats'][0]['value'],
        defenseInterceptionTouchdowns   = teamStats['splits']['categories'][5]['stats'][1]['value'],
        defenseInterceptionYards        = teamStats['splits']['categories'][5]['stats'][2]['value'],
        defenseForcedFumbles            = teamStats['splits']['categories'][0]['stats'][2]['value'],
        defenseFumbleTouchdowns         = teamStats['splits']['categories'][0]['stats'][9]['value'],
        #-----specialTeams
        blockedFieldGoalTouchdowns  = teamStats['splits']['categories'][4]['stats'][4]['value'],
        blockedPuntTouchdowns       = teamStats['splits']['categories'][4]['stats'][5]['value'],
        #-----punting
        totalPunts                  = teamStats['splits']['categories'][8]['stats'][7]['value'],
        #-----scoring
        passingTouchdowns           = teamStats['splits']['categories'][1]['stats'][18]['value'],
        rushingTouchdowns           = teamStats['splits']['categories'][2]['stats'][11]['value'],
        totalTwoPointConvs          = teamStats['splits']['categories'][9]['stats'][12]['value'],
        fieldGoalAttempts           = teamStats['splits']['categories'][6]['stats'][9]['value'],
        fieldGoalsMade              = teamStats['splits']['categories'][6]['stats'][21]['value'],
        extraPointAttempts          = teamStats['splits']['categories'][6]['stats'][2]['value'],
        extraPointsMade             = teamStats['splits']['categories'][6]['stats'][6]['value'],
        #-----down and distance
        firstDowns                  = teamStats['splits']['categories'][10]['stats'][0]['value'],
        firstDownsRushing           = teamStats['splits']['categories'][10]['stats'][4]['value'],
        firstDownsPassing           = teamStats['splits']['categories'][10]['stats'][1]['value'],
        firstDownsByPenalty         = teamStats['splits']['categories'][10]['stats'][2]['value'],
        thirdDownAttempts           = teamStats['splits']['categories'][10]['stats'][29]['value'],
        thirdDownConvs              = teamStats['splits']['categories'][10]['stats'][31]['value'],
        fourthDownAttempts          = teamStats['splits']['categories'][10]['stats'][5]['value'],
        fourthDownConvs             = teamStats['splits']['categories'][10]['stats'][7]['value'],
        #miscellaneous
        twoPtReturns                = teamStats['splits']['categories'][4]['stats'][14]['value'],
        onePtSafetiesMade           = teamStats['splits']['categories'][9]['stats'][15]['value'],
    )
    
    nflMatchInstance = models.nflMatch.objects.get(espnId=matchEspnId)
    associatedTeamObject = models.nflTeam.objects.get(espnId=teamId)
    opponentTeamObject = models.nflTeam.objects.get(espnId=opponentId)
    
    teamPerf.nflMatch.add(nflMatchInstance)
    teamPerf.team.add(associatedTeamObject)
    teamPerf.opponent.add(opponentTeamObject)

    if associatedTeamObject.espnId == nflMatchInstance.homeTeamEspnId:
        teamPerf.totalPointsAllowed             = nflMatchInstance.awayTeamPoints
        teamPerf.totalPointsAllowedByDefense    = nflMatchInstance.awayTeamPoints-nflMatchInstance.awayTeamDefensePointsScored
        teamPerf.totalYardsAllowedByDefense     = nflMatchInstance.homeTeamYardsAllowed
        teamPerf.totalPassYardsAllowed          = nflMatchInstance.homeTeamReceivingYardsAllowed
        teamPerf.totalRushYardsAllowed          = nflMatchInstance.homeTeamRushYardsAllowed
        teamPerf.totalExplosivePlays            = nflMatchInstance.homeTeamExplosivePlays
        if nflMatchInstance.neutralStadium == True:
            teamPerf.atHome = False
        else:
            teamPerf.atHome = True
    elif associatedTeamObject.espnId == nflMatchInstance.awayTeamEspnId:
        teamPerf.totalPointsAllowed             = nflMatchInstance.homeTeamPoints
        teamPerf.totalPointsAllowedByDefense    = nflMatchInstance.homeTeamPoints-nflMatchInstance.homeTeamDefensePointsScored
        teamPerf.totalYardsAllowedByDefense     = nflMatchInstance.awayTeamYardsAllowed
        teamPerf.totalPassYardsAllowed          = nflMatchInstance.awayTeamReceivingYardsAllowed
        teamPerf.totalRushYardsAllowed          = nflMatchInstance.awayTeamRushYardsAllowed
        teamPerf.totalExplosivePlays            = nflMatchInstance.awayTeamExplosivePlays
        teamPerf.atHome = False

    teamPerf.save()

    captureStatsFromPlayByPlay(playByPlayData, drivesData, teamId, opponentId, teamPerf)

def getExplosivePlays(playByPlayData, teamId):

    teamExplosivePlays = 0
    for play in playByPlayData['items']:
        
        teamRefUrl = ""
        try:
            teamRefUrl = play['team']['$ref']
        except(KeyError):
            continue
        
        teamIdString = "teams/"+str(teamId)+"?"

        if teamIdString in teamRefUrl:
            if(play['type']['text'] == "Rush" and play['statYardage']>=10):
                teamExplosivePlays += 1
            elif (play['type']['text'] == "Pass Reception" and play['statYardage']>=25):
                teamExplosivePlays += 1
    
    return teamExplosivePlays

def scheduledScorePull():
    thisDayUTC = datetime.now()
    
    utc_zone = ZoneInfo('UTC')
    central_zone = ZoneInfo('America/Chicago')  

    thisDayUTC = thisDayUTC.replace(tzinfo = utc_zone)

    thisDay = thisDayUTC.astimezone(central_zone)

    yesterday = thisDay + timedelta(days=-1)

    daysToCheck = [0, 3, 4, 5, 6]

    yearOfSeason = thisDay.year if thisDay.month > 4 else thisDay.year - 1 
    weekOfSeason = 1
    
    print("today.weekday() = " + str(thisDay.weekday()))
    print()
    print("Step1: ")
    print(str(thisDay.date()))
    print("Step 2: ")
    print()

    if thisDay.weekday() in daysToCheck:

        print("today is " + thisDay.strftime('%A') + ".")

        #gamesPlayedToday = nflMatch.objects.filter(completed = False).filter(datePlayed = thisDay.date())

        gamesPlayedToday = nflMatch.objects.filter(completed = False).filter(datePlayed__lt =  thisDay).filter(datePlayed__gt = yesterday)

        print(" and there are " + str(len(gamesPlayedToday)) + " finished games at the moment.")        
        

        if len(list(gamesPlayedToday)) > 0:
            print("Today is " + thisDay.strftime('%A') + " " + str(thisDay.date()) + " and " + str(len(list(gamesPlayedToday))) + " are played today.")
            weekOfSeason = gamesPlayedToday[0].weekOfSeason

            if (thisDay.weekday() == 0 or thisDay.weekday() == 3) and thisDay.time() > time(hour = 22, minute = 30, second = 00, microsecond = 0, tzinfo = central_zone):
                #find Monday or Thursday games and get scores
                print("Looking for Monday and Thursday games")
                for unfinishedGame in gamesPlayedToday:
                    matchId = unfinishedGame.espnId
                    matchURL = "http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/" + str(matchId) + "?lang=en&region=us"
                    gameDataResponse = requests.get(matchURL)
                    gameData=gameDataResponse.json()

                    processGameData(gameData, weekOfSeason, yearOfSeason)
                
                if thisDay.weekday() == 0:
                    gamesNextWeek = nflMatch.objects.filter(weekOfSeason = weekOfSeason+1)
                    for game in gamesNextWeek:
                        matchURL = "http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/" + str(game.espnId) + "?lang=en&region=us"
                        matchDataResponse = requests.get(matchURL)
                        matchData = matchDataResponse.json()

                        processGameData(matchData, weekOfSeason+1, yearOfSeason)
                
                #nextWeekUrl = ('https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/'+str(yearOfSeason)+'/types/2/weeks/'+str(weekOfSeason)+'/events')
                return    
                        
            elif thisDay.weekday() == 4 and thisDay.time() > time(hour = 18, minute = 30, second = 00, microsecond = 0, tzinfo = central_zone):
                
                for fridayGame in gamesPlayedToday:
                    matchId = fridayGame.espnId
                    matchURL = "http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/" + str(matchId) + "?lang=en&region=us"
                    gameDataResponse = requests.get(matchURL)
                    gameData=gameDataResponse.json()

                    processGameData(gameData, weekOfSeason, yearOfSeason)
                
                return     
            
            else:                
                for sundayGame in gamesPlayedToday:
                    matchId = sundayGame.espnId
                    matchURL = "http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/" + str(matchId) + "?lang=en&region=us"
                    gameDataResponse = requests.get(matchURL)
                    gameData=gameDataResponse.json()
        
                    processGameData(gameData, weekOfSeason, yearOfSeason)
                
                if thisDay.time() > time(hour = 22, minute = 30, second = 00, microsecond = 0, tzinfo = central_zone):
                    gamesNextWeek = nflMatch.objects.filter(weekOfSeason = weekOfSeason+1)
                    for game in gamesNextWeek:
                        matchURL = "http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/" + str(game.espnId) + "?lang=en&region=us"
                        matchDataResponse = requests.get(matchURL)
                        matchData = matchDataResponse.json()

                        processGameData(matchData, weekOfSeason+1, yearOfSeason)

                return       
        else: 
            print("Today is " + thisDay.strftime('%A') + " " + str(thisDay.date()) + " and no games were updated at " + thisDay.strftime('%H:%M:%S'))
            return

    else:
        print("Today is " + thisDay.strftime('%A') + " " + str(thisDay.date()) + " and we did not check for games.")
        return
            
def organizeRosterAvailabilityArrays(seasonAvailability, weekAvailability, weekNum):
    if len(seasonAvailability) == 0:
        for playerRecord in weekAvailability:
            seasonAvailability.append([playerRecord[0], [playerRecord[1]]])
        
        return seasonAvailability
    else:
        #seasonAvailability.sort(key= lambda x: x[0].name)
        
        for player in weekAvailability:
            playerRow = list(filter(lambda y: y[0] == player[0], seasonAvailability))
           
            if len(playerRow) != 0:
                indexOfPlayer = seasonAvailability.index(playerRow[0])
                seasonAvailability[indexOfPlayer][1].append(player[1])
            else:
                availabilityArray = []
                for i in range(1, weekNum):
                    availabilityArray.append("Not in Roster")
                availabilityArray.append(player[1])
                seasonAvailability.append([player[0], availabilityArray])
        
        for player in seasonAvailability:
            if len(player[1]) != weekNum:
                player[1].append("Not in Roster")

        return seasonAvailability
            
def processGameRosterForAvailability(rosterData, team, seasonYear, seasonWeek):
    athletesAndAvailability = []
    print(seasonWeek)
    for athlete in rosterData['entries']:

        playerObj = None
        try:
            playerObj = player.objects.get(espnId = athlete['playerId'])
        except:
                pass
        if playerObj == None:
            playerObj = players.createPlayerAthletesFromGameRoster(athlete, team.espnId)
        
        try:
            playerWeekStatusObj = playerWeekStatus.objects.get(player = playerObj, team = team, yearOfSeason = seasonYear, weekOfSeason = seasonWeek)
        except:
            playerWeekStatusObj = playerWeekStatus.objects.create(
                player = playerObj,
                team = team,
                weekOfSeason = seasonWeek,
                yearOfSeason = seasonYear,
            )
            if athlete['didNotPlay'] == True or athlete['valid'] == False:
                playerWeekStatusObj.playerStatus = 4
                playerWeekStatusObj.save()
        
        athletesAndAvailability.append([playerObj, playerWeekStatusObj])
    
    athletesAndAvailability = sorted(athletesAndAvailability, key = lambda x: x[0].playerPosition)
    return athletesAndAvailability

def scheduledInjuryPull():
    thisDayUTC = datetime.now()
    
    if thisDayUTC.month >= 8 or thisDayUTC.month <= 2:
        utc_zone = ZoneInfo('UTC')
        central_zone = ZoneInfo('America/Chicago')  

        thisDayUTC = thisDayUTC.replace(tzinfo = utc_zone)

        thisDay = thisDayUTC.astimezone(central_zone)

        if (thisDay.weekday() == 6 and (thisDay.hour == 12 or thisDay.hour == 15 or thisDay.hour == 19)) or thisDayUTC.hour == 16:
            activeTeams = nflTeam.objects.all()
            for team in activeTeams:
                getCurrentWeekAthletesStatus(team.espnId)
        else:
            print("Ran at " + str(thisDay.hour) + ":" + str(thisDay.minute) + " and did not pull the injuries as it was not the right time.")
    else:
        pass 
    

    

def getCurrentWeekAthletesStatus(teamId):
    
    print("Running at " + str(datetime.now()))
    #print("Get here")
    url = ('https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/' + str(teamId) + '/roster')
    response = requests.get(url)
    responseData = response.json()
    rosterData = responseData['athletes']

    currentDate = date.today()
    currentYear = currentDate.year
    currentWeekOfSeason = 0
    
    

    countOfPlayers = 0

    teamMatchesInSeason = nflMatch.objects.filter(yearOfSeason = currentYear, homeTeamEspnId = teamId) | nflMatch.objects.filter(yearOfSeason = currentYear, awayTeamEspnId = teamId)
    
    sortedMatchesInSeason = sorted(teamMatchesInSeason, key = lambda x: x.datePlayed)

    completedGames = list(filter(lambda x: x.completed == True, sortedMatchesInSeason))
    

    if len(completedGames) > 0:
        lastCompletedGame = completedGames[-1]

        if lastCompletedGame.weekOfSeason != 18:
            nextGame = list(filter(lambda x: x.completed == False, sortedMatchesInSeason))[0]

            currentWeekOfSeason = nextGame.weekOfSeason
            

    else:
        currentWeekOfSeason = 1    
    
    thisPlayerWeekStatus = None

    for subsection in rosterData:
        #crudLogic.createPlayerAthletes(subsection, teamId)
        for athlete in subsection['items']:
            playerObj = None
            thisPlayerWeekStatus = None
            alreadyCapturedPlayerWeekStatus = None

            try:
                playerObj = player.objects.get(espnId = athlete['id'])
                countOfPlayers += 1
            except:
                pass
            if playerObj != None:
                try:
                    thisPlayerWeekStatus = playerWeekStatus.objects.get(player = playerObj, weekOfSeason = currentWeekOfSeason, yearOfSeason = currentYear, reportDate = currentDate)
                    
                except Exception as e: 
                    print("No player status for today yet.")

                try:
                    alreadyCapturedPlayerWeekStatus = playerWeekStatus.objects.get(player = playerObj, weekOfSeason = currentWeekOfSeason, yearOfSeason = currentYear, reportDate = (currentDate - timedelta(days=1)))
                except Exception as e:
                    pass
                
                thisPlayerWeekStatusDict = {}
                if thisPlayerWeekStatus == None:
                    # thisPlayerWeekStatus = playerWeekStatus.objects.create(
                    #     player = playerObj,
                    #     weekOfSeason = currentWeekOfSeason,
                    #     yearOfSeason = currentYear
                    # )
                    # thisPlayerWeekStatus.team = nflTeam.objects.get(espnId = teamId)
                    # thisPlayerWeekStatus.reportDate = currentDate

                    thisPlayerWeekStatusDict['player'] = playerObj
                    thisPlayerWeekStatusDict['weekOfSeason'] = currentWeekOfSeason
                    thisPlayerWeekStatusDict['yearOfSeason'] = currentYear
                    thisPlayerWeekStatusDict['team'] = nflTeam.objects.get(espnId = teamId)
                    thisPlayerWeekStatusDict['reportDate'] = currentDate
                        
                if 'injuries' in athlete:
                    if len(athlete['injuries']) != 0:
                        if 'status' in athlete['injuries'][0]:
                            if athlete['injuries'][0]['status'] == "Injured Reserve":
                                # thisPlayerWeekStatus.playerStatus = 6
                                thisPlayerWeekStatusDict['playerStatus'] = 6
                            elif athlete['injuries'][0]['status'] == "Out":
                                # thisPlayerWeekStatus.playerStatus = 4
                                thisPlayerWeekStatusDict['playerStatus'] = 4
                            elif athlete['injuries'][0]['status'] == "Questionable":
                                # thisPlayerWeekStatus.playerStatus = 2
                                thisPlayerWeekStatusDict['playerStatus'] = 2
                            elif athlete['injuries'][0]['status'] == "Doubtful":
                                # thisPlayerWeekStatus.playerStatus = 3
                                thisPlayerWeekStatusDict['playerStatus'] = 3
                    else:
                        if 'status' in athlete:
                            if athlete['status']['id'] == '1':
                                # thisPlayerWeekStatus.playerStatus = 1
                                thisPlayerWeekStatusDict['playerStatus'] = 1
                            else:
                                print("Player w/ ID: " + str(playerObj.espnId) + " has an unexpected status. Status ID: " + str(athlete['status']['id']) + "  Status Name: " + athlete['status']['name'])
                                athleteJSON = athlete
                                athleteJSON['links'] = ""
                                print(athleteJSON)
                else:
                    if 'status' in athlete:
                            if athlete['status']['id'] == '1':
                                # thisPlayerWeekStatus.playerStatus = 1
                                thisPlayerWeekStatusDict['playerStatus'] = 1

                    
                if alreadyCapturedPlayerWeekStatus != None:
                    if alreadyCapturedPlayerWeekStatus.playerStatus != thisPlayerWeekStatusDict['playerStatus']:
                        thisPlayerWeekStatus = playerWeekStatus.objects.create(
                            player = thisPlayerWeekStatusDict['player'],
                            weekOfSeason = thisPlayerWeekStatusDict['weekOfSeason'],
                            yearOfSeason = thisPlayerWeekStatusDict['yearOfSeason'],
                            team = thisPlayerWeekStatusDict['team'],
                            reportDate = currentDate,
                            playerStatus = thisPlayerWeekStatusDict['playerStatus']
                        )
                        thisPlayerWeekStatus.save()
                        
                else:
                    thisPlayerWeekStatus = playerWeekStatus.objects.create(
                            player = thisPlayerWeekStatusDict['player'],
                            weekOfSeason = thisPlayerWeekStatusDict['weekOfSeason'],
                            yearOfSeason = thisPlayerWeekStatusDict['yearOfSeason'],
                            team = thisPlayerWeekStatusDict['team'],
                            reportDate = currentDate,
                            playerStatus = thisPlayerWeekStatusDict['playerStatus']
                        )
                    thisPlayerWeekStatus.save()



            else:
                print("PlayerObj not found in system. Player ID: " + str(athlete['id']) + " Details: ")
                athleteJSON = athlete
                athleteJSON['links'] = ""
                print(athleteJSON)
    

    


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

# def updateNflMatch():
#     pass

# def updateNflMatchOdds():
#     pass

# def deleteNflMatchesId(matchId):
#     pass

# def deleteNflMatchesByWeek(yearOfSeason, weekOfSeason):
#     pass

# def deleteNflMatchesByYear(yearOfSeason):
#     pass

# def updateNflMatch():
#     pass

# def updateNflMatchOdds():
#     pass

# def deleteNflMatchesId(matchId):
#     pass

# def deleteNflMatchesByWeek(yearOfSeason, weekOfSeason):
#     pass

# def deleteNflMatchesByYear(yearOfSeason):
#     pass

# def updatePlayByPlay ():
#     pass

# def deletePlayByPlay ():
#     pass

def createOrUpdateFinishedNflMatch_old(nflMatchObject, gameData, gameCompleted, gameOvertime, homeTeamScore, homeTeamStats, awayTeamScore, awayTeamStats, oddsData, playsData, drivesData, weekOfSeason, seasonYear):
    
    exceptionThrown = False
    exceptions = []

    mappedHomeTeamStats = teamStatsJsonMap(homeTeamStats)
    mappedAwayTeamStats = teamStatsJsonMap(awayTeamStats)

    homeTeamAbrv = nflTeam.objects.get(espnId = gameData['competitions'][0]['competitors'][0]['id']).abbreviation
    awayTeamAbrv = nflTeam.objects.get(espnId = gameData['competitions'][0]['competitors'][1]['id']).abbreviation

    if nflMatchObject == None:
        matchData = nflMatch.objects.create(
                        espnId = gameData['id'],
                        datePlayed = gameData['date'],
                        homeTeamEspnId = gameData['competitions'][0]['competitors'][0]['id'],
                        awayTeamEspnId = gameData['competitions'][0]['competitors'][1]['id'],
                        completed = gameCompleted,
                        weekOfSeason = weekOfSeason,
                        yearOfSeason = seasonYear,
                        neutralStadium = gameData['competitions'][0]['neutralSite'],
                        playoffs = False,
                        indoorStadium = gameData['competitions'][0]['venue']['indoor'],
                        
                        overtime = gameOvertime,
                        
                        preseason= True if int(weekOfSeason) < 0 else False,
                        
                        #-----homeTeam Stats
                        homeTeamPoints                  = homeTeamScore['value'],
                        homeTeamPointsAllowed           = awayTeamScore['value'],
                        homeTeamTotalYards              = mappedHomeTeamStats['passing']['totalYards'],
                        homeTeamYardsAllowed            = mappedAwayTeamStats['passing']['totalYards'],
                        homeTeamRushingYards            = mappedHomeTeamStats['rushing']['rushingYards'],
                        homeTeamRushYardsAllowed        = mappedAwayTeamStats['rushing']['rushingYards'],
                        homeTeamReceivingYards          = mappedHomeTeamStats['receiving']['receivingYards'],
                        homeTeamReceivingYardsAllowed   = mappedAwayTeamStats['receiving']['receivingYards'],
                        homeTeamGiveaways               = mappedHomeTeamStats['passing']['interceptions'] + mappedHomeTeamStats['general']['fumblesLost'], 
                        homeTeamTakeaways               = mappedAwayTeamStats['passing']['interceptions'] + mappedHomeTeamStats['general']['fumblesLost'], 
                        homeTeamRushingTDScored         = mappedHomeTeamStats['scoring']['rushingTouchdowns'],
                        homeTeamRushingTDAllowed        = mappedAwayTeamStats['scoring']['rushingTouchdowns'],
                        homeTeamReceivingTDScored       = mappedHomeTeamStats['scoring']['receivingTouchdowns'],
                        homeTeamReceivingTDAllowed      = mappedAwayTeamStats['scoring']['receivingTouchdowns'],
                        homeTeamFGScored                = mappedHomeTeamStats['scoring']['fieldGoals'],
                        homeTeamFGAllowed               = mappedAwayTeamStats['scoring']['fieldGoals'],
                        homeTeamSpecialTeamsPointsScored    = mappedHomeTeamStats['scoring']['kickExtraPoints'],
                        homeTeamDefensePointsScored         = int((mappedHomeTeamStats['defensiveInterceptions']['interceptionTouchdowns']+mappedHomeTeamStats['general']['defensiveFumblesTouchdowns'])*6),
                        
                        #-----awayTeam stuff
                        awayTeamPoints                  = awayTeamScore['value'],
                        awayTeamPointsAllowed           = homeTeamScore['value'],
                        awayTeamTotalYards              = mappedAwayTeamStats['passing']['totalYards'],
                        awayTeamYardsAllowed            = mappedHomeTeamStats['passing']['totalYards'],
                        awayTeamRushingYards            = mappedAwayTeamStats['rushing']['rushingYards'],
                        awayTeamRushYardsAllowed        = mappedHomeTeamStats['rushing']['rushingYards'],
                        awayTeamReceivingYards          = mappedAwayTeamStats['receiving']['receivingYards'],
                        awayTeamReceivingYardsAllowed   = mappedHomeTeamStats['receiving']['receivingYards'],
                        awayTeamGiveaways               = mappedAwayTeamStats['passing']['interceptions'] + mappedAwayTeamStats['general']['fumblesLost'], 
                        awayTeamTakeaways               = mappedHomeTeamStats['passing']['interceptions'] + mappedHomeTeamStats['general']['fumblesLost'], 
                        awayTeamRushingTDScored         = mappedAwayTeamStats['scoring']['rushingTouchdowns'],
                        awayTeamRushingTDAllowed        = mappedHomeTeamStats['scoring']['rushingTouchdowns'],
                        awayTeamReceivingTDScored       = mappedAwayTeamStats['scoring']['receivingTouchdowns'],
                        awayTeamReceivingTDAllowed      = mappedHomeTeamStats['scoring']['receivingTouchdowns'],
                        awayTeamFGScored                = mappedAwayTeamStats['scoring']['fieldGoals'],
                        awayTeamFGAllowed               = mappedHomeTeamStats['scoring']['fieldGoals'],
                        awayTeamSpecialTeamsPointsScored    = mappedAwayTeamStats['scoring']['kickExtraPoints'],
                        awayTeamDefensePointsScored         = int((mappedAwayTeamStats['defensiveInterceptions']['interceptionTouchdowns']+mappedAwayTeamStats['general']['defensiveFumblesTouchdowns'])*6),                        
                    )

        homeTeamEspnId = gameData['competitions'][0]['competitors'][0]['id']
        awayTeamEspnId = gameData['competitions'][0]['competitors'][1]['id']
        matchData.homeTeam.add(models.nflTeam.objects.get(espnId=homeTeamEspnId))
        matchData.awayTeam.add(models.nflTeam.objects.get(espnId=awayTeamEspnId))

        try:
            matchData.temperature = gameData['competitions'][0]['weather']['temperature']
            matchData.precipitation = gameData['competitions'][0]['weather']['precipitation']
            matchData.windSpeed = gameData['competitions'][0]['weather']['windSpeed']
        except Exception as e:
            tback = traceback.extract_tb(e.__traceback__)
            problem_text = "Line " + str(tback[-1].lineno) + ":" + tback[-1].line
            exceptionThrown = True
            exceptions.append([problem_text, gameData])
        
        if len(oddsData['items']) >= 1:
            if seasonYear == 2024:
                for i in range(1, len(oddsData['items'])):
                    if oddsData[i]['provider']['name'] == "ESPN BET":
                        if 'spread' in oddsData['items'][i]:
                            matchData.matchLineHomeTeam = oddsData['items'][i]['spread']
                        else:
                            print("No Spread Data found for ESPN BET for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                        
                        if 'overUnder' in oddsData['items'][i]:
                            matchData.overUnderLine = oddsData['items'][i]['overUnder']
                        else:
                            print("No O/U Data found for ESPN BET for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                        
                        if 'homeTeamOdds' in oddsData['items'][i]:
                            matchData.homeTeamMoneyLine = oddsData['items'][i]['homeTeamOdds']['moneyLine']
                        
                        if 'awayTeamOdds' in oddsData['items'][0]:
                            matchData.awayTeamMoneyLine = oddsData['items'][i]['awayTeamOdds']['moneyLine']
            else:
                try:
                    spreadSet = False
                    overUnderSet = False
                    homeTeamMLSet = False
                    awayTeamMLSet = False
                    if 'spread' in oddsData['items'][0]:
                        matchData.matchLineHomeTeam = oddsData['items'][0]['spread']
                    else:
                        for i in range(1, len(oddsData['items'])):
                            if 'spread' in oddsData['items'][i]:
                                matchData.matchLineHomeTeam = oddsData['items'][i]['spread']
                                spreadSet = True
                                break
                            else:
                                pass 
                        if not spreadSet:
                            print("No Spread Data Found at all for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                            raise Exception("No spread data?")
                    
                    if 'overUnder' in oddsData['items'][0]:
                        matchData.overUnderLine = oddsData['items'][0]['overUnder']
                    else:
                        for i in range(1, len(oddsData['items'])):
                            if 'overUnder' in oddsData['items'][i]:
                                matchData.overUnderLine = oddsData['items'][i]['overUnder']
                                overUnderSet = True
                                break
                            else: 
                                pass
                        if not overUnderSet:
                            print("No Over/Under Data Found at all for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                            raise Exception("No over/under data?")

                    if 'homeTeamOdds' in oddsData['items'][0]:
                        matchData.homeTeamMoneyLine = oddsData['items'][0]['homeTeamOdds']['moneyLine']
                    else:
                        for i in range(1, len(oddsData['items'])):
                            if 'homeTeamOdds' in oddsData['items'][i]:
                                matchData.homeTeamMoneyLine = oddsData['items'][i]['homeTeamOdds']['moneyLine']
                                homeTeamMLSet = True
                                break
                            else: 
                                pass
                        if not homeTeamMLSet:
                            print("No Home Team Odds Data Found at all for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                            raise Exception("No home team ML data?")
                    
                    if 'awayTeamOdds' in oddsData['items'][0]:
                        matchData.awayTeamMoneyLine = oddsData['items'][0]['awayTeamOdds']['moneyLine']
                    else:
                        for i in range(1, len(oddsData['items'])):
                            if 'awayTeamOdds' in oddsData['items'][i]:
                                matchData.awayTeamMoneyLine = oddsData['items'][i]['awayTeamOdds']['moneyLine']
                                awayTeamMLSet = True
                                break
                            else: 
                                pass
                        if not awayTeamMLSet:
                            print("No Away Team Odds Data Found at all for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                            raise Exception("No away team ML data?")
                        
                    
                except Exception as e:
                    tback = traceback.extract_tb(e.__traceback__)
                    problem_text = "Line " + str(tback[-1].lineno) + ":" + tback[-1].line
                    exceptionThrown = True
                    exceptions.append([problem_text, oddsData])
        
        
    else:
        matchData = nflMatchObject
        
        matchData.completed = gameCompleted
        matchData.overtime = gameOvertime
        matchData.homeTeamPoints                = homeTeamScore['value']
        matchData.homeTeamPointsAllowed         = awayTeamScore['value']
        matchData.homeTeamTotalYards            = mappedHomeTeamStats['passing']['totalYards']
        matchData.homeTeamYardsAllowed          = mappedAwayTeamStats['passing']['totalYards']
        matchData.homeTeamRushingYards          = mappedHomeTeamStats['rushing']['rushingYards']
        matchData.homeTeamRushYardsAllowed      = mappedAwayTeamStats['rushing']['rushingYards']
        matchData.homeTeamReceivingYards        = mappedHomeTeamStats['receiving']['receivingYards']
        matchData.homeTeamReceivingYardsAllowed = mappedAwayTeamStats['receiving']['receivingYards']
        matchData.homeTeamGiveaways             = mappedHomeTeamStats['passing']['interceptions'] + mappedHomeTeamStats['general']['fumblesLost']
        matchData.homeTeamTakeaways             = mappedAwayTeamStats['passing']['interceptions'] + mappedHomeTeamStats['general']['fumblesLost']
        matchData.homeTeamRushingTDScored       = mappedHomeTeamStats['scoring']['rushingTouchdowns']
        matchData.homeTeamRushingTDAllowed      = mappedAwayTeamStats['scoring']['rushingTouchdowns']
        matchData.homeTeamReceivingTDScored     = mappedHomeTeamStats['scoring']['receivingTouchdowns']
        matchData.homeTeamReceivingTDAllowed    = mappedAwayTeamStats['scoring']['receivingTouchdowns']
        matchData.homeTeamFGScored              = mappedHomeTeamStats['scoring']['fieldGoals']
        matchData.homeTeamFGAllowed             = mappedAwayTeamStats['scoring']['fieldGoals']
        matchData.homeTeamSpecialTeamsPointsScored  = mappedHomeTeamStats['scoring']['kickExtraPoints']
        matchData.homeTeamDefensePointsScored       = int((mappedHomeTeamStats['defensiveInterceptions']['interceptionTouchdowns']+mappedHomeTeamStats['general']['defensiveFumblesTouchdowns'])*6)
        #awayTeam stuff
        matchData.awayTeamPoints                = awayTeamScore['value']
        matchData.awayTeamPointsAllowed         = homeTeamScore['value']
        matchData.awayTeamTotalYards            = mappedAwayTeamStats['passing']['totalYards']
        matchData.awayTeamYardsAllowed          = mappedHomeTeamStats['passing']['totalYards']
        matchData.awayTeamRushingYards          = mappedAwayTeamStats['rushing']['rushingYards']
        matchData.awayTeamRushYardsAllowed      = mappedHomeTeamStats['rushing']['rushingYards']
        matchData.awayTeamReceivingYards        = mappedAwayTeamStats['receiving']['receivingYards']
        matchData.awayTeamReceivingYardsAllowed = mappedHomeTeamStats['receiving']['receivingYards']
        matchData.awayTeamGiveaways             = mappedAwayTeamStats['passing']['interceptions'] + mappedHomeTeamStats['general']['fumblesLost']
        matchData.awayTeamTakeaways             = mappedHomeTeamStats['passing']['interceptions'] + mappedHomeTeamStats['general']['fumblesLost']
        matchData.awayTeamRushingTDScored       = mappedAwayTeamStats['scoring']['rushingTouchdowns']
        matchData.awayTeamRushingTDAllowed      = mappedHomeTeamStats['scoring']['rushingTouchdowns']
        matchData.awayTeamReceivingTDScored     = mappedAwayTeamStats['scoring']['receivingTouchdowns']
        matchData.awayTeamReceivingTDAllowed    = mappedHomeTeamStats['scoring']['receivingTouchdowns']
        matchData.awayTeamFGScored              = mappedAwayTeamStats['scoring']['fieldGoals']
        matchData.awayTeamFGAllowed             = mappedHomeTeamStats['scoring']['fieldGoals']
        matchData.awayTeamSpecialTeamsPointsScored  = mappedAwayTeamStats['scoring']['kickExtraPoints']
        matchData.awayTeamDefensePointsScored       = int((mappedAwayTeamStats['defensiveInterceptions']['interceptionTouchdowns']+mappedAwayTeamStats['general']['defensiveFumblesTouchdowns'])*6)
        
        homeTeamEspnId = gameData['competitions'][0]['competitors'][0]['id']
        awayTeamEspnId = gameData['competitions'][0]['competitors'][1]['id']

        theHomeTeam = models.nflTeam.objects.get(espnId=homeTeamEspnId)
        matchData.homeTeam.add(theHomeTeam)

        theAwayTeam = models.nflTeam.objects.get(espnId=awayTeamEspnId)
        matchData.awayTeam.add(theAwayTeam)


        #print("Oddsdata items count:" + str(len(oddsData['items'])))
        if len(oddsData['items']) > 2:
            if seasonYear == 2024:
                pass
                # for i in range(1, len(oddsData['items'])):
                #     if oddsData[i]['provider']['name'] == "ESPN BET":
                #         if 'spread' in oddsData['items'][i]:
                #             matchData.matchLineHomeTeam = oddsData['items'][i]['spread']
                #         else:
                #             print("No Spread Data found for ESPN BET for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                        
                #         if 'overUnder' in oddsData['items'][i]:
                #             matchData.overUnderLine = oddsData['items'][i]['overUnder']
                #         else:
                #             print("No O/U Data found for ESPN BET for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                        
                #         if 'homeTeamOdds' in oddsData['items'][i]:
                #             matchData.homeTeamMoneyLine = oddsData['items'][i]['homeTeamOdds']['moneyLine']
                        
                #         if 'awayTeamOdds' in oddsData['items'][0]:
                #             matchData.awayTeamMoneyLine = oddsData['items'][i]['awayTeamOdds']['moneyLine']
            else:
                try:
                    spreadSet = False
                    overUnderSet = False
                    homeTeamMLSet = False
                    awayTeamMLSet = False
                    if 'spread' in oddsData['items'][0]:
                        matchData.matchLineHomeTeam = oddsData['items'][0]['spread']
                    else:
                        for i in range(1, len(oddsData['items'])):
                            if 'spread' in oddsData['items'][i]:
                                matchData.matchLineHomeTeam = oddsData['items'][i]['spread']
                                spreadSet = True
                                break
                            else: 
                                pass
                        if not spreadSet:
                            print("No Spread Data Found at all for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                            raise Exception("No spread data?")
                    
                    if 'overUnder' in oddsData['items'][0]:
                        matchData.overUnderLine = oddsData['items'][0]['overUnder']
                    else:
                        for i in range(1, len(oddsData['items'])):
                            if 'overUnder' in oddsData['items'][i]:
                                matchData.overUnderLine = oddsData['items'][i]['overUnder']
                                overUnderSet = True
                                break
                            else: 
                                pass
                        if not overUnderSet:
                            print("No Over/Under Data Found at all for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                            raise Exception("No over/under data?")
                        
                    if 'homeTeamOdds' in oddsData['items'][0]:
                        matchData.homeTeamMoneyLine = oddsData['items'][0]['homeTeamOdds']['moneyLine']
                    else:
                        for i in range(1, len(oddsData['items'])):
                            if 'homeTeamOdds' in oddsData['items'][i]:
                                matchData.homeTeamMoneyLine = oddsData['items'][i]['homeTeamOdds']['moneyLine']
                                homeTeamMLSet = True
                                break
                            else: 
                                pass
                        if not homeTeamMLSet:
                            print("No Home Team Odds Data Found at all for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                            raise Exception("No home team ML data?")
                    
                    if 'awayTeamOdds' in oddsData['items'][0]:
                        matchData.awayTeamMoneyLine = oddsData['items'][0]['awayTeamOdds']['moneyLine']
                    else:
                        for i in range(1, len(oddsData['items'])):
                            if 'awayTeamOdds' in oddsData['items'][i]:
                                matchData.awayTeamMoneyLine = oddsData['items'][i]['awayTeamOdds']['moneyLine']
                                awayTeamMLSet = True
                                break
                            else: 
                                pass
                        if not awayTeamMLSet:
                            print("No Away Team Odds Data Found at all for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                            raise Exception("No away team ML data?")

                except Exception as e:
                    tback = traceback.extract_tb(e.__traceback__)
                    problem_text = "Line " + str(tback[-1].lineno) + ":" + tback[-1].line
                    exceptionThrown = True
                    exceptions.append([problem_text, oddsData])

    
    
    try:
        for individualDrive in drivesData['items']: 
            createDriveOfPlay(individualDrive, matchData)
    except Exception as e:
        tback = traceback.extract_tb(e.__traceback__)
        problem_text = "Line " + str(tback[-1].lineno) + ":" + tback[-1].line
        exceptions.append([problem_text, drivesData])
        exceptionThrown = True

    
    if exceptionThrown:
        raise Exception(exceptions)

    # homeTeamExplosivePlays = getExplosivePlays(playsData, matchData.homeTeamEspnId)
    # awayTeamExplosivePlays = getExplosivePlays(playsData, matchData.awayTeamEspnId)

    # matchData.homeTeamExplosivePlays = homeTeamExplosivePlays
    # matchData.awayTeamExplosivePlays = awayTeamExplosivePlays

    matchData.save()    

    return matchData