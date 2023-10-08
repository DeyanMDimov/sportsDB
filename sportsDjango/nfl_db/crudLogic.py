from nfl_db import models
from nfl_db.models import nflTeam, nflMatch, teamMatchPerformance, driveOfPlay, playByPlay, player, playerTeamTenure, playerMatchPerformance, playerMatchOffense, playerMatchDefense, playerWeekStatus
from django.db import IntegrityError
from datetime import datetime, date, timezone, timedelta
from zoneinfo import ZoneInfo
import json, requests, traceback

def createOrUpdateFinishedNflMatch(nflMatchObject, gameData, gameCompleted, gameOvertime, homeTeamScore, homeTeamStats, awayTeamScore, awayTeamStats, oddsData, playsData, drivesData, weekOfSeason, seasonYear):
    
    exceptionThrown = False
    exceptions = []

    mappedHomeTeamStats = teamStatsJsonMap(homeTeamStats)
    
    mappedAwayTeamStats = teamStatsJsonMap(awayTeamStats)

    homeTeamAbrv = nflTeam.objects.get(espnId = gameData['competitions'][0]['competitors'][0]['id']).abbreviation
    awayTeamAbrv = nflTeam.objects.get(espnId = gameData['competitions'][0]['competitors'][1]['id']).abbreviation

    # for catName, statsdict in mappedHomeTeamStats.items():
    #     print("----Category: " + catName)
    #     for statName, statValue in statsdict.items():
    #         print("--------Stat: " + statName)

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
        
        if len(oddsData['items']) > 2:
            if seasonYear == 2023:
                for i in range(1, len(oddsData['items'])):
                    if oddsData[i]['provider']['name'] == "DraftKings":
                        if 'spread' in oddsData['items'][i]:
                            matchData.matchLineHomeTeam = oddsData['items'][i]['spread']
                        else:
                            print("No Spread Data found for DraftKings for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                        
                        if 'overUnder' in oddsData['items'][i]:
                            matchData.overUnderLine = oddsData['items'][i]['overUnder']
                        else:
                            print("No O/U Data found for DraftKings for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                        
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
        

        print("Oddsdata items count:" + str(len(oddsData['items'])))
        if len(oddsData['items']) > 2:
            if seasonYear == 2023:
                for i in range(1, len(oddsData['items'])):
                    if oddsData[i]['provider']['name'] == "DraftKings":
                        if 'spread' in oddsData['items'][i]:
                            matchData.matchLineHomeTeam = oddsData['items'][i]['spread']
                        else:
                            print("No Spread Data found for DraftKings for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                        
                        if 'overUnder' in oddsData['items'][i]:
                            matchData.overUnderLine = oddsData['items'][i]['overUnder']
                        else:
                            print("No O/U Data found for DraftKings for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                        
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

    if exceptionThrown:
        raise Exception(exceptions)
    
    try:
        for individualDrive in drivesData['items']: 
            createDriveOfPlay(individualDrive, matchData)
    except Exception as e:
        tback = traceback.extract_tb(e.__traceback__)
        problem_text = "Line " + str(tback[-1].lineno) + ":" + tback[-1].line
        exceptions.append([problem_text, drivesData])
        raise Exception(exceptions)


    # homeTeamExplosivePlays = getExplosivePlays(playsData, matchData.homeTeamEspnId)
    # awayTeamExplosivePlays = getExplosivePlays(playsData, matchData.awayTeamEspnId)

    # matchData.homeTeamExplosivePlays = homeTeamExplosivePlays
    # matchData.awayTeamExplosivePlays = awayTeamExplosivePlays

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
        
        if len(oddsData['items']) > 2:
            if seasonYear == 2023:
                for i in range(1, len(oddsData['items'])):
                    if oddsData[i]['provider']['name'] == "DraftKings":
                        if 'spread' in oddsData['items'][i]:
                            matchData.matchLineHomeTeam = oddsData['items'][i]['spread']
                        else:
                            print("No Spread Data found for DraftKings for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                        
                        if 'overUnder' in oddsData['items'][i]:
                            matchData.overUnderLine = oddsData['items'][i]['overUnder']
                        else:
                            print("No O/U Data found for DraftKings for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                        
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
        if len(oddsData['items']) > 2:
            if int(seasonYear) == 2023:
                for i in range(1, len(oddsData['items'])):
                    if oddsData['items'][i]['provider']['name'] == "DraftKings":
                        print()
                        print("Odds Data from Draft Kings for " + homeTeamAbrv + " vs. " + awayTeamAbrv)
                        print(oddsData['items'][i])
                        print()

                        if 'spread' in oddsData['items'][i]:
                            matchData.matchLineHomeTeam = oddsData['items'][i]['spread']
                        else:
                            print("No Spread Data found for DraftKings for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                        
                        if 'overUnder' in oddsData['items'][i]:
                            matchData.overUnderLine = oddsData['items'][i]['overUnder']
                        else:
                            print("No O/U Data found for DraftKings for " + homeTeamAbrv + " vs. " +awayTeamAbrv)
                        
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
        print()
        print("Team Perf saved. MatchID: " + str(teamPerf.matchEspnId) + " Team ID: " + str(teamPerf.teamEspnId))

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
        existingTeamPerformance.twoPtReturns                = mappedTeamStats['defensive']['twoPtReturns']
        existingTeamPerformance.onePtSafetiesMade           = mappedTeamStats['defensive']['onePtSafetiesMade']
        
        
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
        print()
        print("Team Perf saved. MatchID: " + str(existingTeamPerformance.matchEspnId) + " Team ID: " + str(existingTeamPerformance.teamEspnId))

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
                            teamRushingTenPlus += 1
                        elif (play['type']['text'] == "Pass Reception" and play['statYardage']>=25):
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

    # for play in individualDrive['plays']['items']:
    #     createPlayByPlay(play, addedDrive.espnId)

    addedDrive.save()

def updateDriveOfPlay ():
    pass

def deleteDriveOfPlay ():
    driveOfPlay.objects.all().delete()
    return "All drives deleted"

def setResultOfDrive(inputResult, matchEspnId = ""):
    def switch(inputResult):
        if inputResult == "TD":
            return 1
        elif inputResult == "FG":
            return 2
        elif inputResult == "MISSED FG":
            return 3
        elif inputResult == "PUNT":
            return 4
        elif inputResult == "BLOCKED PUNT":
            return 5
        elif inputResult == "BLOCKED PUNT TD":
            return 6
        elif inputResult == "INT":
            return 7
        elif inputResult == "INT TD":
            return 8
        elif inputResult == "FUMBLE":
            return 9
        elif inputResult == "FUMBLE RETURN TD" or "FUMBLE TD":
            return 10
        elif inputResult == "DOWNS":
            return 12
        elif inputResult == "END OF HALF":
            return 13
        elif inputResult == "END OF GAME":
            return 14
        elif inputResult == "SAFETY" or inputResult == "SF":
            return 16
        elif inputResult == "BLOCKED FG TD" : 
            return 18
        elif inputResult == "BLOCKED FG" : 
            return 19
        else:
            print("UNEXPECTED DRIVE RESULT - ", inputResult, "Match ID: ", matchEspnId)
            return 17
    
    return switch(inputResult)

def createPlayByPlay (individualPlay, driveEspnId):
    createdPlay = playByPlay.objects.create(
        espnId = individualPlay['id'],
        playType = setPlayType(individualPlay['type']['text']),
        yardsFromEndzone = individualPlay['start']['yardsToEndzone'],
        yardsOnPlay = individualPlay['startYardage'],
        playDown = individualPlay['start']['down'],
        scoringPlay = individualPlay['scoringPlay'],
        driveOfPlay = models.driveOfPlay.objects.get(espnId = driveEspnId),
        teamOnOffense = models.nflTeam.objects.get(espnId = checkTeamFromRefUrl(individualPlay['start']['team']['$ref'])),
        pointsScored = individualPlay['scoreValue'],
        
    )

    if createdPlay.playType in ['INTERCEPTION', 'INTERCEPTION RETURN TOUCHDOWN', 'DEFENSIVE FUMBLE RECOVERY ','DEFENSIVE FUMBLE RECOVERY TOUCHDOWN']:
        createdPlay.turnover = True

    if createdPlay.scoringPlay:
        if createdPlay.teamOnOffense.espnId == checkTeamFromRefUrl(individualPlay['start']['team']['$ref']):
            createdPlay.offenseScored = True
        else:
            createdPlay.offenseScored = False
    
    
    

    
        # penaltyOnPlay = models.BooleanField()
        # penaltyIsOnOffense = models.BooleanField(null = True, blank = True)
        # yardsGainedOrLostOnPenalty = models.SmallIntegerField(null = True, blank = True)
        
        # nflMatch = models.ForeignKey(nflMatch, on_delete = models.CASCADE)
        
        
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
       
    if individualPlay['scoringType']['abbreviation'] == "TD":
        try:
            extraPointOutcome = individualPlay['pointAfterAttempt']['text']
        
        except:
            pass

def setPlayType(inputType):
    
    def switch(inputType):
        if inputType == "Rush":
            return 1
        elif inputType == "Pass Reception":
            return 2
        elif inputType == "Pass Incompletion":
            return 3
        elif inputType == "Sack":
            return 4
        elif inputType == "INTERCEPTION":
            return 5
        elif inputType == "INTERCEPTION RETURN TOUCHDOWN":
            return 6
        elif inputType == "OFFENSIVE FUMBLE RECOVERY":
            return 7
        elif inputType == "OFFENSIVE FUMBLE RECOVERY TOUCHDOWN":
            return 8
        elif inputType == "DEFENSIVE FUMBLE RECOVERY":
            return 9
        elif inputType == "DEFENSIVE FUMBLE RECOVERY TOUCHDOWN":
            return 10
        elif inputType == "SAFETY":
            return 11
        elif inputType == "PUNT":
            return 12
        elif inputType == "Blocked Punt":
            return 13
        elif inputType == "PUNT MUFFED PUNTING TEAM RECOVERY":
            return 14
        elif inputType == "PUNT MUFFED RECEIVING TEAM RECOVERY":
            return 15
        elif inputType == "Field Goal Good":
            return 16
        elif inputType == "FG KICK MISSED":
            return 17
        elif inputType == "Kickoff Return (Offense)" or inputType == "Kickoff":
            return 18
        elif inputType == "KICKOFF RECOVERY KICKING TEAM":
            return 19
        elif inputType == "PAT KICK MADE":
            return 20
        elif inputType == "PAT KICK MISSED":
            return 21
        elif inputType == "2PT CONVERSION SUCCESS RUSH":
            return 22
        elif inputType == "2PT CONVERSION SUCCESS PASS":
            return 23
        elif inputType == "2PT CONVERSION FAILED RUSH":
            return 24
        elif inputType == "2PT CONVERSION FAILED PASS":
            return 25
        elif inputType == "2PT CONVERSION SUCCESS OTHER":
            return 26
        elif inputType == "2PT CONVERSION FAILED OTHER":
            return 27
        elif inputType == "KNEEL":
            return 28
        elif inputType == "SPIKE":
            return 29
        elif inputType == "NO PLAY/BLOWN DEAD":
            return 30
        elif inputType == "Timeout":
            return 31
        
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

    #print(str(thisDayUTC))

    thisDay = thisDayUTC.astimezone(central_zone)

    yesterday = thisDay + timedelta(days=-1)

    #print(str(thisDay))

    daysToCheck = [0, 3, 4, 5, 6]

    yearOfSeason = thisDay.year if thisDay.month > 4 else thisDay.year - 1 
    weekOfSeason = 1
    
    print("today.weekday() = " + str(thisDay.weekday()))
    print()
    print()
    print("Step1: ")
    print(str(thisDay.date()))
    print("Step 2: ")
    print()
    print()

    if thisDay.weekday() in daysToCheck:

        print("today is " + thisDay.strftime('%A') + ".")

        #gamesPlayedToday = nflMatch.objects.filter(completed = False).filter(datePlayed = thisDay.date())

        gamesPlayedToday = nflMatch.objects.filter(completed = False).filter(datePlayed__lt =  thisDay).filter(datePlayed__gt = yesterday)

        print(" and there are " + str(gamesPlayedToday) + " finished games at the moment.")        
        

        if len(list(gamesPlayedToday)) > 0:
            print("Today is " + thisDay.strftime('%A') + " " + str(thisDay.date()) + " and " + str(len(list(gamesPlayedToday))) + " are played today.")
            weekOfSeason = gamesPlayedToday[0].weekOfSeason

            if (thisDay.weekday() == 0 or thisDay.weekday() == 3) and thisDay.time > datetime(hour = 23, minute = 30, second = 00, tzinfo = central_zone):
                #find Monday or Thursday games and get scores
                print("Looking for Monday and Thursday games")
                for unfinishedGame in gamesPlayedToday:
                    matchId = unfinishedGame.espnId
                    matchURL = "http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/" + str(matchId) + "?lang=en&region=us"
                    gameDataResponse = requests.get(matchURL)
                    gameData=gameDataResponse.json()

                    processGameData(gameData, weekOfSeason, yearOfSeason)
                    
                return    
                        
            elif thisDay.weekday() == 4 and thisDay.time > datetime(hour = 18, minute = 30, second = 00, tzinfo = central_zone):
                
                for fridayGame in gamesPlayedToday:
                    matchId = fridayGame.espnId
                    matchURL = "http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/" + str(matchId) + "?lang=en&region=us"
                    gameDataResponse = requests.get(matchURL)
                    gameData=gameDataResponse.json()

                    processGameData(gameData, weekOfSeason, yearOfSeason)
                
                return     
            
            else:
                print("Where my Sunday games at?")
                for sundayGame in gamesPlayedToday:
                    matchId = sundayGame.espnId
                    matchURL = "http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/" + str(matchId) + "?lang=en&region=us"
                    gameDataResponse = requests.get(matchURL)
                    gameData=gameDataResponse.json()
        
                    processGameData(gameData, weekOfSeason, yearOfSeason)
                
                return       
        else: 
            print("Today is " + thisDay.strftime('%A') + " " + thisDay.date + " and no games were updated at " + thisDay.strftime('%H:%M:%S'))
            return

    else:
        print("Today is " + thisDay.strftime('%A') + " " + thisDay.date + " and we did not check for games.")
        return

def processGameData(gameData, weekOfSeason, yearOfSeason):
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
    oddsResponse = requests.get(oddsUrl)
    oddsData = oddsResponse.json()

    existingMatch = None
    existingHomeTeamPerf = None
    existingAwayTeamPerf = None

    try:
        existingMatch = nflMatch.objects.get(espnId = matchEspnId)
    except Exception as e:
        print(e)

    try:
        existingHomeTeamPerf = teamMatchPerformance.objects.get(matchEspnId = matchEspnId, teamEspnId = homeTeamEspnId)
    except Exception as e:
        print(e)

    try:    
        existingAwayTeamPerf = teamMatchPerformance.objects.get(matchEspnId = matchEspnId, teamEspnId = awayTeamEspnId)
    except Exception as e:
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
        drivesDataResponse = requests.get(drivesDataUrl)
        drivesData = drivesDataResponse.json()

        playsDataUrl = gameData['competitions'][0]['details']['$ref']
        playsDataResponse = requests.get(playsDataUrl)
        playsData = playsDataResponse.json()

        playByPlayOfGame = playByPlayData(playsData)
        
        pagesOfPlaysData = playsData['pageCount']
        if pagesOfPlaysData > 1:
            print("Multiple pages of Data in game")
            for page in range(2, pagesOfPlaysData+1):
                multiPagePlaysDataUrl = playsDataUrl+"&page="+str(page)
                pagePlaysDataResponse = requests.get(multiPagePlaysDataUrl)
                pagePlaysData = pagePlaysDataResponse.json()
                playByPlayOfGame.addJSON(pagePlaysData)
        
        try:
            matchData = createOrUpdateFinishedNflMatch(existingMatch, gameData, gameCompleted, gameOvertime, homeTeamScore, homeTeamStats, awayTeamScore, awayTeamStats, oddsData, playsData, drivesData, str(weekOfSeason), str(yearOfSeason))
        except Exception as e:
            matchData = nflMatch.objects.get(espnId = matchEspnId)
            print("There was an exception updating MatchEspnId: " + str(matchEspnId))
            print(e)

        try:
            existingHomeTeamPerf = teamMatchPerformance.objects.get(matchEspnId = matchData.espnId, teamEspnId = matchData.homeTeamEspnId)
        except Exception as e:
            print("There was an exception getting homeTeamPerformance for MatchEspnId: " + str(matchEspnId))
            print(e)        
        
        try:
            createOrUpdateTeamMatchPerformance(existingHomeTeamPerf, homeTeamScore, homeTeamStats, matchData.espnId, matchData.homeTeamEspnId, matchData.awayTeamEspnId, awayTeamStats, playsData, playByPlayOfGame, drivesData, seasonWeek=str(weekOfSeason), seasonYear=str(yearOfSeason))                        
        except Exception as e: 
            print("Problem with creating home team Match performance for MatchEspnId: " + str(matchEspnId))
            print(e)
            
        try:
            createOrUpdateTeamMatchPerformance(existingAwayTeamPerf, awayTeamScore, awayTeamStats, matchData.espnId, matchData.awayTeamEspnId, matchData.homeTeamEspnId, homeTeamStats, playsData, playByPlayOfGame, drivesData, seasonWeek=str(weekOfSeason), seasonYear=str(yearOfSeason))    
        except Exception as e:
            print("Problem with creating away team Match performance for MatchEspnId: " + str(matchEspnId))
            print(e)
            
def organizeRosterAvailabilityArrays(seasonAvailability, weekAvailability, weekNum):
    if len(seasonAvailability) == 0:
        for playerRecord in weekAvailability:
            seasonAvailability.append([playerRecord[0], [playerRecord[1]]])
        
        return seasonAvailability
    else:
        seasonAvailability.sort(key= lambda x: x[0].name)
        
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
            playerObj = createPlayerAthletesFromGameRoster(athlete, team.espnId)
        
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
    
    return athletesAndAvailability

def scheduledInjuryPull():
    thisDayUTC = datetime.now()
    
    utc_zone = ZoneInfo('UTC')
    central_zone = ZoneInfo('America/Chicago')  

    thisDayUTC = thisDayUTC.replace(tzinfo = utc_zone)

    thisDay = thisDayUTC.astimezone(central_zone)

    if (thisDay.weekday() == 6 and (thisDay.hour == 11 or thisDay.hour == 14 or thisDay.hour == 18)) or thisDayUTC.hour == 15:
        activeTeams = nflTeam.objects.all()
        for team in activeTeams:
            getCurrentWeekAthletesStatus(team.espnId)
    else:
        print("Ran at " + str(thisDay.hour) + ":" + str(thisDay.minute) + " and did not pull the injuries as it was not the right time.") 
    

    

def getCurrentWeekAthletesStatus(teamId):
    
    print("Running at " + str(datetime.now()))
    print("Get here")
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

                if thisPlayerWeekStatus == None:
                    thisPlayerWeekStatus = playerWeekStatus.objects.create(
                        player = playerObj,
                        weekOfSeason = currentWeekOfSeason,
                        yearOfSeason = currentYear
                    )
                    thisPlayerWeekStatus.team = nflTeam.objects.get(espnId = teamId)
                    thisPlayerWeekStatus.reportDate = currentDate
                if 'injuries' in athlete:
                    if len(athlete['injuries']) != 0:
                        if 'status' in athlete['injuries'][0]:
                            if athlete['injuries'][0]['status'] == "Injured Reserve":
                                thisPlayerWeekStatus.playerStatus = 6
                            elif athlete['injuries'][0]['status'] == "Out":
                                thisPlayerWeekStatus.playerStatus = 4
                            elif athlete['injuries'][0]['status'] == "Questionable":
                                thisPlayerWeekStatus.playerStatus = 2
                            elif athlete['injuries'][0]['status'] == "Doubtful":
                                thisPlayerWeekStatus.playerStatus = 3
                    else:
                        if 'status' in athlete:
                            if athlete['status']['id'] == '1':
                                thisPlayerWeekStatus.playerStatus = 1
                            else:
                                print("Player w/ ID: " + str(playerObj.espnId) + " has an unexpected status. Status ID: " + str(athlete['status']['id']) + "  Status Name: " + athlete['status']['name'])
                                athleteJSON = athlete
                                athleteJSON['links'] = ""
                                print(athleteJSON)
                else:
                    if 'status' in athlete:
                            if athlete['status']['id'] == '1':
                                thisPlayerWeekStatus.playerStatus = 1

                    

                thisPlayerWeekStatus.save()

            else:
                print("PlayerObj not found in system. Player ID: " + str(athlete['id']) + " Details: ")
                athleteJSON = athlete
                athleteJSON['links'] = ""
                print(athleteJSON)
    

    
def createPlayerAthletesFromTeamRoster(rosterData, teamId):
    print(str(teamId))
    for athlete in rosterData['items']:
        playerObj = None
        try:
            playerObj = player.objects.get(espnId = athlete['id'])
        except:
            pass
        if playerObj == None:
            playerObj = player.objects.create(
                    espnId = athlete['id'],
                    name = athlete['displayName'],
                    firstSeason = getFirstSeasonYear(athlete['experience']['years']),
                    team = nflTeam.objects.get(espnId = teamId),
                    playerHeightInches = athlete['height'],
                    playerWeightPounds = athlete['weight'],
                    playerPosition = getAthletePosition(athlete['position']['abbreviation']), 
                    sideOfBall = getAthleteSideOfBall(athlete['position'])
                )
            # try: 
            #     playerObj.sideOfBall = getAthleteSideOfBall(athlete['position']['parent']['name'])
            #     playerObj.save()
            # except KeyError as e:
            #     if playerObj.playerPosition == "G" or playerObj.playerPosition == "OT" or playerObj.playerPosition == "WR" or playerObj.playerPosition == "RB" or playerObj.playerPosition == "QB":
            #         playerObj.sideOfBall = 1
            #         playerObj.save()
            #     else:
            #         raise Exception("parent not in athlete[position]")
            if athlete['experience']['years'] == 0:
                playerTeamTenure.objects.create(
                    player = playerObj,
                    team = nflTeam.objects.get(espnId = teamId),
                    startDate = datetime(2023, 9, 8)
                )
                print("Player tenure created for ROOKIE.")
            print("Successfully loaded player " + str(playerObj.espnId))
        else:
            print("Player " + str(playerObj.espnId) + " already in system.")
            playerObj.firstSeason = getFirstSeasonYear(athlete['experience']['years'])
            playerObj.save()
            
            playerTenures = playerTeamTenure.objects.filter(player = playerObj)
            currentSeasonTenures = list(filter(lambda x: x.startDate.year == 2023, playerTenures))
            if athlete['experience']['years'] == 0:    
                if len(list(currentSeasonTenures)) == 0:
                    playerTeamTenure.objects.create(
                        player = playerObj,
                        team = nflTeam.objects.get(espnId = teamId),
                        startDate = datetime(2023, 9, 8)
                    )
                    print()
                    print("Player tenure created for rookie.")
                    print()
            else:
               getPlayerTenures(playerObj)
               
def createPlayerAthletesFromGameRoster(athleteRosterData, teamId):
    
    url = athleteRosterData['athlete']['$ref']
    response = requests.get(url)
    athleteData = response.json()
    

    playerObj = player.objects.create(
            espnId = athleteData['id'],
            name = athleteData['displayName'],
            firstSeason = getFirstSeasonYear(athleteData['experience']['years']),
            team = nflTeam.objects.get(espnId = teamId),
            playerHeightInches = athleteData['height'],
            playerWeightPounds = athleteData['weight'],
            playerPosition = getAthletePosition(athleteData['position']['abbreviation']), 
            sideOfBall = getAthleteSideOfBall(athleteData['position'])
        )
    
    if athleteData['experience']['years'] == 0:
        playerTeamTenure.objects.create(
            player = playerObj,
            team = nflTeam.objects.get(espnId = teamId),
            startDate = datetime(2023, 9, 8)
        )
        print("Player tenure created for ROOKIE.")
    print("Successfully loaded player w/ ESPN ID: " + str(playerObj.espnId) + " - " + playerObj.name)

    return playerObj
    
def getPlayerTenures(playerObj):
    yearToStart = playerObj.firstSeason
    playerTenures = playerTeamTenure.objects.filter(player = playerObj)
    latestPlayerTenure = None
    playerName = playerObj.name
    print()
    print("Getting Tenures for " + playerObj.name)
    print()
    
    if len(playerTenures) == 0:
        try:
            for yr in range(yearToStart, 2023):
                seasonGameLogUrl = "http://site.web.api.espn.com/apis/common/v3/sports/football/nfl/athletes/"+str(playerObj.espnId)+"/gamelog?season="+str(yr)
                response = requests.get(seasonGameLogUrl)
                responseData = response.json()

                if 'events' in responseData:
                    gamesInSeason = responseData['events']

                    gamesData = list(gamesInSeason.values())

                    gamesAndDates = []
                    for g in gamesData:
                        dateOfGame = datetime.fromisoformat(g['gameDate'][0:10]).astimezone(datetime.now().tzinfo)
                        gamesAndDates.append([dateOfGame, g])
                    
                    sortedGames = sorted(gamesAndDates, key=lambda x: x[0])            
                    
                    for i in range(0, len(sortedGames)):
                        
                        game = sortedGames[i][1]
                        teamId = game['team']['id']
                        if yr == yearToStart and i == 0:
                            print("Processing first game of first tenure. Season: " + str(yr))
                            if len(playerTenures) == 0:
                                tenureStartDate = sortedGames[i][0]
                                try:
                                    playerTeamTenure.objects.create(
                                        player = playerObj,
                                        team = nflTeam.objects.get(espnId = teamId),
                                        startDate = tenureStartDate,
                                        endDate = tenureStartDate
                                    )
                                except Exception as e:
                                    print("Exception: cannot find team for teamId: " + str(teamId) + " in year: " + str(yr))
                                    raise Exception(e)
                                
                                latestPlayerTenure = playerTeamTenure.objects.get(player = playerObj)
                            else:
                                print()
                                print("OOPSIE")
                                print("Some tenure already exists.")
                                print()
                                print()
                        else:
                            #print("Processing game " + str(game['week']) + " of " + str(yr))
                            if int(teamId) != latestPlayerTenure.team.espnId:
                                if('eventNote' not in game):
                                    try:
                                        playerTeamTenure.objects.create(
                                            player = playerObj,
                                            team = nflTeam.objects.get(espnId = teamId),
                                            startDate = sortedGames[i][0],
                                            endDate = sortedGames[i][0]
                                        )
                                    except Exception as e:
                                        print("Exception: cannot find team for teamId: " + str(teamId) + " in year: " + str(yr))
                                        allTeams = nflTeam.objects.all().order_by('espnId')
                                        for tm in allTeams:
                                            print(tm.fullName + " - ID: " + str(tm.espnId))
                                        raise Exception(e)
                                
                                    playerTenures = playerTeamTenure.objects.filter(player = playerObj).filter(team__espnId = teamId)
                                    numberOfTenures = len(playerTenures)
                                    latestPlayerTenure = playerTenures[numberOfTenures-1]
                            else:
                                latestPlayerTenure.endDate = sortedGames[i][0]
                                latestPlayerTenure.save()
                else:
                    pass
        except Exception as e :
            print("Player - " + playerObj.name + " could not be loaded.")
            print(e)
    else: 
        return

def getAthletePosition(abbreviation):
    if abbreviation == "QB":
        return 1
    elif abbreviation == "WR":
        return 2
    elif abbreviation == "TE":
        return 3
    elif abbreviation == "RB":
        return 4
    elif abbreviation == "FB":
        return 5
    elif abbreviation == "OT" or abbreviation == "C" or abbreviation == "G":
        return 6
    elif abbreviation == "DE" or abbreviation == "DT" :
        return 7
    elif abbreviation == "LB":
        return 8
    elif abbreviation == "CB":
        return 9
    elif abbreviation == "S":
        return 10
    elif abbreviation == "PK":
        return 11
    elif abbreviation == "P":
        return 12
    else:
        return 13
    
def getAthleteSideOfBall(positionData):
    if 'parent' in positionData:
        if 'name' in positionData['parent']:
            if positionData['parent']['name'] == "Offense":
                return 1
            elif positionData['parent']['name'] == "Defense":
                return 2
            elif positionData['parent']['name'] == "Special Teams":
                return 3
            else:
                return 4
        else:
            if getAthletePosition(positionData['abbreviation']) in range(1,7):
                return 1
            elif getAthletePosition(positionData['abbreviation']) in range(7,11):
                return 2
            elif getAthletePosition(positionData['abbreviation']) in range(11,13):
                return 3
            else:
                return 4
    else:
        if getAthletePosition(positionData['abbreviation']) in range(1,7):
            return 1
        elif getAthletePosition(positionData['abbreviation']) in range(7,11):
            return 2
        elif getAthletePosition(positionData['abbreviation']) in range(11,13):
            return 3
        else:
            return 4
    # playerPositions = (
                #     (1, "QB"),
                #     (2, "WR"),
                #     (3, "TE"),
                #     (4, "RB"),
                #     (5, "FB"),
                #     (6, "O-Line"),
                #     (7, "D-Line"),
                #     (8, "LB"),
                #     (9, "CB"),
                #     (10, "S"),
                #     (11, "K"),
                #     (12, "P"),
                #     (13, "Other")
                # )

def getFirstSeasonYear(yearsOfExperience):
    numYears = int(yearsOfExperience)
    currentYear = datetime.now().year

    firstSeasonYear = 0

    if numYears == 0:
        firstSeasonYear = currentYear
    else:
        firstSeasonYear = currentYear-numYears+1
    return firstSeasonYear

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