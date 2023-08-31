from nfl_db import models
from nfl_db.models import nflMatch, teamMatchPerformance, nflTeam, driveOfPlay
import json


# def createOrUpdateNflMatch(nflMatchObject, gameData, gameCompleted, gameOvertime, homeTeamScore, homeTeamStats, awayTeamScore, awayTeamStats, oddsData, playsData, drivesData, weekOfSeason, seasonYear):
    
    
#     if nflMatchObject == None:
#         matchData = nflMatch.objects.create(
#                         espnId = gameData['id'],
#                         datePlayed = gameData['date'],
#                         homeTeamEspnId = gameData['competitions'][0]['competitors'][0]['id'],
#                         awayTeamEspnId = gameData['competitions'][0]['competitors'][1]['id'],
#                         completed = gameCompleted,
#                         weekOfSeason = weekOfSeason,
#                         yearOfSeason = seasonYear,
#                         neutralStadium = gameData['competitions'][0]['neutralSite'],
#                         playoffs= False,
#                         indoorStadium = gameData['competitions'][0]['venue']['indoor'],
                        
#                         overtime= gameOvertime,
#                         # temperature = 70,
#                         # precipitation = 0, 
#                         # windSpeed=0,
#                         preseason= True if int(weekOfSeason) < 0 else False,
#                         homeTeamPoints= homeTeamScore['value'],
#                         homeTeamPointsAllowed= awayTeamScore['value'],
#                         homeTeamTotalYards= homeTeamStats['splits']['categories'][1]['stats'][32]['value'],
#                         homeTeamYardsAllowed= awayTeamStats['splits']['categories'][1]['stats'][32]['value'],
#                         homeTeamRushingYards= homeTeamStats['splits']['categories'][2]['stats'][12]['value'],
#                         homeTeamRushYardsAllowed= awayTeamStats['splits']['categories'][2]['stats'][12]['value'],
#                         homeTeamReceivingYards= homeTeamStats['splits']['categories'][3]['stats'][12]['value'],
#                         homeTeamReceivingYardsAllowed= awayTeamStats['splits']['categories'][3]['stats'][12]['value'],
#                         homeTeamGiveaways= homeTeamStats['splits']['categories'][10]['stats'][33]['value'],
#                         homeTeamTakeaways= homeTeamStats['splits']['categories'][10]['stats'][37]['value'],
#                         homeTeamRushingTDScored= homeTeamStats['splits']['categories'][9]['stats'][7]['value'],
#                         homeTeamRushingTDAllowed= awayTeamStats['splits']['categories'][9]['stats'][7]['value'],
#                         homeTeamReceivingTDScored= homeTeamStats['splits']['categories'][9]['stats'][5]['value'],
#                         homeTeamReceivingTDAllowed= awayTeamStats['splits']['categories'][9]['stats'][8]['value'],
#                         homeTeamFGScored= homeTeamStats['splits']['categories'][9]['stats'][1]['value'],
#                         homeTeamFGAllowed= awayTeamStats['splits']['categories'][9]['stats'][1]['value'],
#                         homeTeamSpecialTeamsPointsScored= homeTeamStats['splits']['categories'][9]['stats'][3]['value'],
#                         homeTeamDefensePointsScored= int((homeTeamStats['splits']['categories'][5]['stats'][1]['value']+homeTeamStats['splits']['categories'][0]['stats'][9]['value'])*6),
#                         #awayTeam stuff
#                         awayTeamPoints= awayTeamScore['value'],
#                         awayTeamPointsAllowed= homeTeamScore['value'],
#                         awayTeamTotalYards= awayTeamStats['splits']['categories'][1]['stats'][32]['value'],
#                         awayTeamYardsAllowed= homeTeamStats['splits']['categories'][1]['stats'][32]['value'],
#                         awayTeamRushingYards= awayTeamStats['splits']['categories'][2]['stats'][12]['value'],
#                         awayTeamRushYardsAllowed= homeTeamStats['splits']['categories'][2]['stats'][12]['value'],
#                         awayTeamReceivingYards= awayTeamStats['splits']['categories'][3]['stats'][12]['value'],
#                         awayTeamReceivingYardsAllowed= homeTeamStats['splits']['categories'][3]['stats'][12]['value'],
#                         awayTeamGiveaways= awayTeamStats['splits']['categories'][10]['stats'][33]['value'],
#                         awayTeamTakeaways= awayTeamStats['splits']['categories'][10]['stats'][37]['value'],
#                         awayTeamRushingTDScored= awayTeamStats['splits']['categories'][9]['stats'][7]['value'],
#                         awayTeamRushingTDAllowed= homeTeamStats['splits']['categories'][9]['stats'][7]['value'],
#                         awayTeamReceivingTDScored= awayTeamStats['splits']['categories'][9]['stats'][5]['value'],
#                         awayTeamReceivingTDAllowed= homeTeamStats['splits']['categories'][9]['stats'][5]['value'],
#                         awayTeamFGScored= awayTeamStats['splits']['categories'][9]['stats'][1]['value'],
#                         awayTeamFGAllowed= homeTeamStats['splits']['categories'][9]['stats'][1]['value'],
#                         awayTeamSpecialTeamsPointsScored= awayTeamStats['splits']['categories'][9]['stats'][3]['value'],
#                         awayTeamDefensePointsScored= int((awayTeamStats['splits']['categories'][5]['stats'][1]['value']+awayTeamStats['splits']['categories'][0]['stats'][9]['value'])*6),
#                         #matchLineHomeTeam= (-1 * oddsData['items'][0]['spread']) if Boolean(oddsData['items'][0]['homeTeamOdds']['favorite']) else (oddsData['items'][0]['spread'])
#                     )
#         homeTeamEspnId = gameData['competitions'][0]['competitors'][0]['id']
#         awayTeamEspnId = gameData['competitions'][0]['competitors'][1]['id']
#         matchData.homeTeam.add(models.nflTeam.objects.get(espnId=homeTeamEspnId))
#         matchData.awayTeam.add(models.nflTeam.objects.get(espnId=awayTeamEspnId))
#         if len(oddsData['items']) > 2:
#             try:
#                 matchData.overUnderLine= oddsData['items'][0]['overUnder']
#                 matchData.homeTeamMoneyLine = oddsData['items'][0]['homeTeamOdds']['moneyLine']
#                 matchData.awayTeamMoneyLine = oddsData['items'][0]['awayTeamOdds']['moneyLine']
#                 matchData.matchLineHomeTeam = oddsData['items'][0]['spread']
#             except: 
#                 pass
#         #matchData.homeTeamDefensePointsScored= (int(homeTeamStats['splits']['categories'][5]['stats'][1]['value'])+int(homeTeamStats['splits']['categories'][0]['stats'][9]['value']))*6
#         #matchData.awayTeamDefensePointsScored= (int(awayTeamStats['splits']['categories'][5]['stats'][1]['value'])+int(awayTeamStats['splits']['categories'][0]['stats'][9]['value']))*6
#         print("about to get Explosive Plays")
        
#         homeTeamExplosivePlays = getExplosivePlays(playsData, homeTeamEspnId)
#         awayTeamExplosivePlays = getExplosivePlays(playsData, awayTeamEspnId)
        
#         matchData.homeTeamExplosivePlays = homeTeamExplosivePlays
#         matchData.awayTeamExplosivePlays = awayTeamExplosivePlays

#         matchData.save()
#     else:
#         matchData = nflMatchObject
        
#         if gameCompleted:
            
#             matchData.completed = gameCompleted
#             matchData.overtime= gameOvertime
#             matchData.homeTeamPoints= homeTeamScore['value']
#             matchData.homeTeamPointsAllowed= awayTeamScore['value']
#             matchData.homeTeamTotalYards= homeTeamStats['splits']['categories'][1]['stats'][32]['value']
#             matchData.homeTeamYardsAllowed= awayTeamStats['splits']['categories'][1]['stats'][32]['value']
#             matchData.homeTeamRushingYards= homeTeamStats['splits']['categories'][2]['stats'][12]['value']
#             matchData.homeTeamRushYardsAllowed= awayTeamStats['splits']['categories'][2]['stats'][12]['value']
#             matchData.homeTeamReceivingYards= homeTeamStats['splits']['categories'][3]['stats'][12]['value']
#             matchData.homeTeamReceivingYardsAllowed= awayTeamStats['splits']['categories'][3]['stats'][12]['value']
#             matchData.homeTeamGiveaways= homeTeamStats['splits']['categories'][10]['stats'][33]['value']
#             matchData.homeTeamTakeaways= homeTeamStats['splits']['categories'][10]['stats'][37]['value']
#             #homeTeamExplosivePlays= 
#             matchData.homeTeamRushingTDScored= homeTeamStats['splits']['categories'][9]['stats'][7]['value']
#             matchData.homeTeamRushingTDAllowed= awayTeamStats['splits']['categories'][9]['stats'][7]['value']
#             matchData.homeTeamReceivingTDScored= homeTeamStats['splits']['categories'][9]['stats'][5]['value']
#             matchData.homeTeamReceivingTDAllowed= awayTeamStats['splits']['categories'][9]['stats'][8]['value']
#             matchData.homeTeamFGScored= homeTeamStats['splits']['categories'][9]['stats'][1]['value']
#             matchData.homeTeamFGAllowed= awayTeamStats['splits']['categories'][9]['stats'][1]['value']
#             matchData.homeTeamSpecialTeamsPointsScored= homeTeamStats['splits']['categories'][9]['stats'][3]['value']
#             matchData.homeTeamDefensePointsScored= int((homeTeamStats['splits']['categories'][5]['stats'][1]['value']+homeTeamStats['splits']['categories'][0]['stats'][9]['value'])*6)
#             #awayTeam stuff
#             matchData.awayTeamPoints= awayTeamScore['value']
#             matchData.awayTeamPointsAllowed= homeTeamScore['value']
#             matchData.awayTeamTotalYards= awayTeamStats['splits']['categories'][1]['stats'][32]['value']
#             matchData.awayTeamYardsAllowed= homeTeamStats['splits']['categories'][1]['stats'][32]['value']
#             matchData.awayTeamRushingYards= awayTeamStats['splits']['categories'][2]['stats'][12]['value']
#             matchData.awayTeamRushYardsAllowed= homeTeamStats['splits']['categories'][2]['stats'][12]['value']
#             matchData.awayTeamReceivingYards= awayTeamStats['splits']['categories'][3]['stats'][12]['value']
#             matchData.awayTeamReceivingYardsAllowed= homeTeamStats['splits']['categories'][3]['stats'][12]['value']
#             matchData.awayTeamGiveaways= awayTeamStats['splits']['categories'][10]['stats'][33]['value']
#             matchData.awayTeamTakeaways= awayTeamStats['splits']['categories'][10]['stats'][37]['value']
#             #awayTeamExplosivePlays= 
#             matchData.awayTeamRushingTDScored= awayTeamStats['splits']['categories'][9]['stats'][7]['value']
#             matchData.awayTeamRushingTDAllowed= homeTeamStats['splits']['categories'][9]['stats'][7]['value']
#             matchData.awayTeamReceivingTDScored= awayTeamStats['splits']['categories'][9]['stats'][5]['value']
#             matchData.awayTeamReceivingTDAllowed= homeTeamStats['splits']['categories'][9]['stats'][5]['value']
#             matchData.awayTeamFGScored= awayTeamStats['splits']['categories'][9]['stats'][1]['value']
#             matchData.awayTeamFGAllowed= homeTeamStats['splits']['categories'][9]['stats'][1]['value']
#             matchData.awayTeamSpecialTeamsPointsScored= awayTeamStats['splits']['categories'][9]['stats'][3]['value']
#             matchData.awayTeamDefensePointsScored= int((awayTeamStats['splits']['categories'][5]['stats'][1]['value']+awayTeamStats['splits']['categories'][0]['stats'][9]['value'])*6)
            
#             print(awayTeamStats['splits']['categories'][5]['stats'][1]['value'])
#             print(awayTeamStats['splits']['categories'][0]['stats'][9]['value'])
        
#         if len(oddsData['items']) > 2:
#             try:
#                 matchData.overUnderLine= oddsData['items'][0]['overUnder']
#                 matchData.homeTeamMoneyLine = oddsData['items'][0]['homeTeamOdds']['moneyLine']
#                 matchData.awayTeamMoneyLine = oddsData['items'][0]['awayTeamOdds']['moneyLine']
#                 matchData.matchLineHomeTeam = oddsData['items'][0]['spread']
#             except: 
#                 pass
        
#         homeTeamExplosivePlays = getExplosivePlays(playsData, matchData.homeTeamEspnId)
#         awayTeamExplosivePlays = getExplosivePlays(playsData, matchData.awayTeamEspnId)

#         matchData.homeTeamExplosivePlays = homeTeamExplosivePlays
#         matchData.awayTeamExplosivePlays = awayTeamExplosivePlays

#         matchData.save()    
#     return matchData

# def createOrUpdateScheduledNflMatch(nflMatchObject, gameData, oddsData, weekOfSeason, seasonYear):
#     if nflMatchObject == None:
#         matchData = nflMatch.objects.create(
#                         espnId = gameData['id'],
#                         datePlayed = gameData['date'],
#                         #homeTeam = nflTeam.objects.get(espnId=gameData['competitions'][0]['competitors'][0]['id']),
#                         homeTeamEspnId = gameData['competitions'][0]['competitors'][0]['id'],
#                         #awayTeam = nflTeam.objects.get(espnId=gameData['competitions'][0]['competitors'][1]['id']),
#                         awayTeamEspnId = gameData['competitions'][0]['competitors'][1]['id'],
#                         completed = (gameData['competitions'][0]['boxscoreSource']['state'] == "full"),
#                         weekOfSeason = weekOfSeason,
#                         yearOfSeason = seasonYear,
#                         neutralStadium = gameData['competitions'][0]['neutralSite'],
#                         playoffs= False,
#                         indoorStadium = gameData['competitions'][0]['venue']['indoor'],
                        
#                     )
#         homeTeamEspnId = gameData['competitions'][0]['competitors'][0]['id']
#         awayTeamEspnId = gameData['competitions'][0]['competitors'][1]['id']
#         matchData.homeTeam.add(models.nflTeam.objects.get(espnId=homeTeamEspnId))
#         matchData.awayTeam.add(models.nflTeam.objects.get(espnId=awayTeamEspnId))
        
#         if len(oddsData['items']) > 2:
#             try:
#                 matchData.overUnderLine= oddsData['items'][0]['overUnder']
#                 matchData.homeTeamMoneyLine = oddsData['items'][0]['homeTeamOdds']['moneyLine']
#                 matchData.awayTeamMoneyLine = oddsData['items'][0]['awayTeamOdds']['moneyLine']
#                 matchData.matchLineHomeTeam = oddsData['items'][0]['spread']
#             except: 
#                 pass
        
#         matchData.save()    
#     else:
#         matchData = nflMatchObject
#         if len(oddsData['items']) > 2:
#             try:
#                 matchData.overUnderLine= oddsData['items'][0]['overUnder']
#                 matchData.homeTeamMoneyLine = oddsData['items'][0]['homeTeamOdds']['moneyLine']
#                 matchData.awayTeamMoneyLine = oddsData['items'][0]['awayTeamOdds']['moneyLine']
#                 matchData.matchLineHomeTeam = oddsData['items'][0]['spread']
#             except Exception as e:
#                 print(e)

#             matchData.save()   

#     return matchData

# def createTeamPerformance(teamScore, teamStats, matchEspnId, teamId, opponentId, playByPlayData, drivesData, seasonWeek, seasonYear):
    
#     teamPerf = teamMatchPerformance.objects.create(
#         matchEspnId      = matchEspnId,
#         #nflMatch         = 
#         #team             = 
#         #opponent        = models.ManyToManyField(nflTeam, related_name = "opponent", blank = True)
#         teamEspnId      = teamId,
#         weekOfSeason    = seasonWeek,
#         yearOfSeason    = seasonYear,
#         #atHome
#         #-----general
#         totalPointsScored       = teamScore['value'],
#         #totalPointsAllowed
#         totalTouchdownsScored   = teamStats['splits']['categories'][1]['stats'][31]['value'],
#         totalPenalties          = teamStats['splits']['categories'][10]['stats'][34]['value'],
#         totalPenaltyYards       = teamStats['splits']['categories'][10]['stats'][35]['value'],
#         #-----offense
#         totalYardsGained            = teamStats['splits']['categories'][1]['stats'][32]['value'],
#         #totalExplosivePlays         = 
#         totalGiveaways              = teamStats['splits']['categories'][10]['stats'][33]['value'],
#         #redZoneAttempts             = 
#         #redZoneTDConversionPct      = 
#         #redZoneFumbles              = 
#         #redZoneFumblesLost          = 
#         #redZoneInterceptions        = 
#         #totalOffensePenalties       = 
#         #totalOffensePenaltyYards    = 
#         #-----offense-passing
#         passCompletions             = teamStats['splits']['categories'][1]['stats'][2]['value'],
#         passingAttempts             = teamStats['splits']['categories'][1]['stats'][12]['value'],
#         #passPlaysTwentyFivePlus     = 
#         totalPassingYards           = teamStats['splits']['categories'][3]['stats'][12]['value'],
#         #qbHitsTaken                 = 
#         sacksTaken                  = teamStats['splits']['categories'][1]['stats'][24]['value'],
#         sackYardsLost               = teamStats['splits']['categories'][1]['stats'][25]['value'],
#         twoPtPassConversions        = teamStats['splits']['categories'][1]['stats'][34]['value'],
#         twoPtPassAttempts           = teamStats['splits']['categories'][1]['stats'][36]['value'],
#         #-----offense-rushing
#         rushingAttempts             = teamStats['splits']['categories'][2]['stats'][6]['value'],
#         rushingYards                = teamStats['splits']['categories'][2]['stats'][12]['value'],
#         stuffsTaken                 = teamStats['splits']['categories'][2]['stats'][14]['value'],
#         stuffYardsLost              = teamStats['splits']['categories'][2]['stats'][15]['value'],
#         #rushingPlaysTenPlus         = 
#         twoPtRushConversions        = teamStats['splits']['categories'][2]['stats'][23]['value'],
#         twoPtRushAttempts           = teamStats['splits']['categories'][2]['stats'][25]['value'],
#         totalReceivingYards         = teamStats['splits']['categories'][3]['stats'][12]['value'],
#         receivingYardsAfterCatch    = teamStats['splits']['categories'][3]['stats'][13]['value'],
#         interceptionsOnOffense      = teamStats['splits']['categories'][1]['stats'][5]['value'],
#         passingFumbles              = teamStats['splits']['categories'][3]['stats'][8]['value'],
#         passingFumblesLost          = teamStats['splits']['categories'][3]['stats'][9]['value'],
#         rushingFumbles              = teamStats['splits']['categories'][2]['stats'][9]['value'],
#         rushingFumblesLost          = teamStats['splits']['categories'][2]['stats'][10]['value'],
#         #-----defense
#         # totalPointsAllowed              = 
#         # totalYardsAllowedByDefense      = 
#         # totalPassYardsAllowed           = 
#         # totalRushYardsAllowed           = 
#         totalTakeaways                  = teamStats['splits']['categories'][10]['stats'][37]['value'],
#         defensiveTouchdownsScored       = teamStats['splits']['categories'][5]['stats'][1]['value']+teamStats['splits']['categories'][0]['stats'][9]['value'],
#         passesBattedDown                = teamStats['splits']['categories'][4]['stats'][11]['value'],
#         qbHits                          = teamStats['splits']['categories'][4]['stats'][13]['value'],
#         defenseSacks                    = teamStats['splits']['categories'][4]['stats'][15]['value'],
#         sackYardsGained                 = teamStats['splits']['categories'][4]['stats'][18]['value'],
#         safetiesScored                  = teamStats['splits']['categories'][4]['stats'][19]['value'],
#         defenseStuffs                   = teamStats['splits']['categories'][4]['stats'][21]['value'],
#         defenseInterceptions            = teamStats['splits']['categories'][5]['stats'][0]['value'],
#         defenseInterceptionTouchdowns   = teamStats['splits']['categories'][5]['stats'][1]['value'],
#         defenseInterceptionYards        = teamStats['splits']['categories'][5]['stats'][2]['value'],
#         defenseForcedFumbles            = teamStats['splits']['categories'][0]['stats'][2]['value'],
#         #defenseFumblesRecovered         = 
#         defenseFumbleTouchdowns         = teamStats['splits']['categories'][0]['stats'][9]['value'],
#         #totalDefensePenalties           = 
#         #totalDefensePenaltyYards        = 
#         #firstDownsByPenaltyGiven        = 
#         #-----specialTeams
#         #blockedFieldGoals           = 
#         blockedFieldGoalTouchdowns  = teamStats['splits']['categories'][4]['stats'][4]['value'],
#         #blockedPunts                = 
#         blockedPuntTouchdowns       = teamStats['splits']['categories'][4]['stats'][5]['value'],
#         #specialTeamsPenalties       = models.SmallIntegerField(null = True, blank = True)
#         #specialTeamsPenaltyYards    = models.SmallIntegerField(null = True, blank = True)
#         #-----punting
#         totalPunts                  = teamStats['splits']['categories'][8]['stats'][7]['value'],
#         #opponentPinnedInsideTen     = 
#         #opponentPinnedInsideFive    = 
#         #-----scoring
#         passingTouchdowns           = teamStats['splits']['categories'][1]['stats'][18]['value'],
#         rushingTouchdowns           = teamStats['splits']['categories'][2]['stats'][11]['value'],
#         totalTwoPointConvs          = teamStats['splits']['categories'][9]['stats'][12]['value'],
#         fieldGoalAttempts           = teamStats['splits']['categories'][6]['stats'][9]['value'],
#         fieldGoalsMade              = teamStats['splits']['categories'][6]['stats'][21]['value'],
#         extraPointAttempts          = teamStats['splits']['categories'][6]['stats'][2]['value'],
#         extraPointsMade             = teamStats['splits']['categories'][6]['stats'][6]['value'],
#         #-----down and distance
#         firstDowns                  = teamStats['splits']['categories'][10]['stats'][0]['value'],
#         firstDownsRushing           = teamStats['splits']['categories'][10]['stats'][4]['value'],
#         firstDownsPassing           = teamStats['splits']['categories'][10]['stats'][1]['value'],
#         firstDownsByPenalty         = teamStats['splits']['categories'][10]['stats'][2]['value'],
#         thirdDownAttempts           = teamStats['splits']['categories'][10]['stats'][29]['value'],
#         thirdDownConvs              = teamStats['splits']['categories'][10]['stats'][31]['value'],
#         fourthDownAttempts          = teamStats['splits']['categories'][10]['stats'][5]['value'],
#         fourthDownConvs             = teamStats['splits']['categories'][10]['stats'][7]['value'],
#         #drivePinnedInsideTen        = 
#         #drivePinnedInsideFive       = 
#         # rushPctFirstDown            = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
#         # passPctFirstDown            = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
#         # completionPctFirstDown      = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
#         # rushPctSecondDown           = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
#         # passPctSecondDown           = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
#         # completionPctSecondDown     = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
#         # rushPctThirdDown            = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
#         # passPctThirdDown            = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
#         # completionPctThirdDown      = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
#         #miscellaneous
#         twoPtReturns                = teamStats['splits']['categories'][4]['stats'][14]['value'],
#         onePtSafetiesMade           = teamStats['splits']['categories'][9]['stats'][15]['value'],
#     )
    
#     nflMatchInstance = models.nflMatch.objects.get(espnId=matchEspnId)
#     associatedTeamObject = models.nflTeam.objects.get(espnId=teamId)
#     opponentTeamObject = models.nflTeam.objects.get(espnId=opponentId)
    
#     teamPerf.nflMatch.add(nflMatchInstance)
#     teamPerf.team.add(associatedTeamObject)
#     teamPerf.opponent.add(opponentTeamObject)

#     if associatedTeamObject.espnId == nflMatchInstance.homeTeamEspnId:
#         teamPerf.totalPointsAllowed             = nflMatchInstance.awayTeamPoints
#         teamPerf.totalPointsAllowedByDefense    = nflMatchInstance.awayTeamPoints-nflMatchInstance.awayTeamDefensePointsScored
#         teamPerf.totalYardsAllowedByDefense     = nflMatchInstance.homeTeamYardsAllowed
#         teamPerf.totalPassYardsAllowed          = nflMatchInstance.homeTeamReceivingYardsAllowed
#         teamPerf.totalRushYardsAllowed          = nflMatchInstance.homeTeamRushYardsAllowed
#         teamPerf.totalExplosivePlays            = nflMatchInstance.homeTeamExplosivePlays
#         if nflMatchInstance.neutralStadium == True:
#             teamPerf.atHome = False
#         else:
#             teamPerf.atHome = True
#     elif associatedTeamObject.espnId == nflMatchInstance.awayTeamEspnId:
#         teamPerf.totalPointsAllowed             = nflMatchInstance.homeTeamPoints
#         teamPerf.totalPointsAllowedByDefense    = nflMatchInstance.homeTeamPoints-nflMatchInstance.homeTeamDefensePointsScored
#         teamPerf.totalYardsAllowedByDefense     = nflMatchInstance.awayTeamYardsAllowed
#         teamPerf.totalPassYardsAllowed          = nflMatchInstance.awayTeamReceivingYardsAllowed
#         teamPerf.totalRushYardsAllowed          = nflMatchInstance.awayTeamRushYardsAllowed
#         teamPerf.totalExplosivePlays            = nflMatchInstance.awayTeamExplosivePlays
#         teamPerf.atHome = False

#     teamPerf.save()

#     captureStatsFromPlayByPlay(playByPlayData, drivesData, teamId, opponentId, teamPerf)




# def updateTeamPerformance(teamScore, teamStats, matchEspnId, teamId, opponentId, playByPlayData, seasonWeek, seasonYear):
#     teamPerf = teamMatchPerformance.objects.get(matchEspnId = matchEspnId, teamEspnId = teamId)
#     nflMatchInstance = models.nflMatch.objects.get(espnId=matchEspnId)
    
    
#     if teamId == nflMatchInstance.homeTeamEspnId:
#         teamPerf.totalPointsAllowed             = nflMatchInstance.awayTeamPoints
#         print("awayTeamPoints: ", nflMatchInstance.awayTeamPoints)
#         print("awayTeamDefensePointsScored: ", nflMatchInstance.awayTeamDefensePointsScored)
#         teamPerf.totalPointsAllowedByDefense    = nflMatchInstance.awayTeamPoints-nflMatchInstance.awayTeamDefensePointsScored
#         teamPerf.totalYardsAllowedByDefense     = nflMatchInstance.homeTeamYardsAllowed
#         teamPerf.totalPassYardsAllowed          = nflMatchInstance.homeTeamReceivingYardsAllowed
#         teamPerf.totalRushYardsAllowed          = nflMatchInstance.homeTeamRushYardsAllowed
#         teamPerf.totalExplosivePlays            = nflMatchInstance.homeTeamExplosivePlays
#         if nflMatchInstance.neutralStadium == True:
#             teamPerf.atHome = False
#         else:
#             teamPerf.atHome = True

#     elif teamId == nflMatchInstance.awayTeamEspnId:
#         teamPerf.totalPointsAllowed             = nflMatchInstance.homeTeamPoints
#         teamPerf.totalPointsAllowedByDefense    = nflMatchInstance.homeTeamPoints-nflMatchInstance.homeTeamDefensePointsScored
#         teamPerf.totalYardsAllowedByDefense     = nflMatchInstance.awayTeamYardsAllowed
#         teamPerf.totalPassYardsAllowed          = nflMatchInstance.awayTeamReceivingYardsAllowed
#         teamPerf.totalRushYardsAllowed          = nflMatchInstance.awayTeamRushYardsAllowed
#         teamPerf.totalExplosivePlays            = nflMatchInstance.awayTeamExplosivePlays
#         teamPerf.atHome = False

#     teamPerf.save()

#     captureStatsFromPlayByPlay(playByPlayData, teamId, opponentId, teamPerf)


# def getExplosivePlays(playByPlayData, teamId):

#     teamExplosivePlays = 0
#     for play in playByPlayData['items']:
        
#         teamRefUrl = ""
#         try:
#             teamRefUrl = play['team']['$ref']
#         except(KeyError):
#             continue
        
#         teamIdString = "teams/"+str(teamId)+"?"

#         if teamIdString in teamRefUrl:
#             if(play['type']['text'] == "Rush" and play['statYardage']>=10):
#                 teamExplosivePlays += 1
#             elif (play['type']['text'] == "Pass Reception" and play['statYardage']>=25):
#                 teamExplosivePlays += 1
    
#     return teamExplosivePlays


# def captureStatsFromPlayByPlay(playByPlayData, drivesData, teamId, opponentId, teamPerf):
    
#     teamAbbreviation = nflTeam.objects.get(espnId = teamId).abbreviation
#     opponentAbbreviation = nflTeam.objects.get(espnId = opponentId).abbreviation

#     teamPenaltyText = ("PENALTY on " + teamAbbreviation)
#     opponentPenaltyText = ("PENALTY on " + opponentAbbreviation)
    
#     teamRushingTenPlus          = 0
#     teamPassPlaysTwentyFivePlus = 0
#     redZoneAttempts             = 0
#     redZoneTDConversionPct      = 0.0
#     redZoneFumbles              = 0
#     redZoneFumblesLost          = 0
#     redZoneInterceptions        = 0
#     totalOffensePenalties       = 0
#     totalOffensePenaltyYards    = 0
#     defenseFumblesRecovered     = 0
#     totalDefensePenalties       = 0
#     totalDefensePenaltyYards    = 0
#     firstDownsByPenaltyGiven    = 0
#     opponentPinnedInsideTen     = 0
#     opponentPinnedInsideFive    = 0
#     drivePinnedInsideTen        = 0
#     drivePinnedInsideFive       = 0
#     rushPctFirstDown            = 0.0
#     passPctFirstDown            = 0.0
#     completionPctFirstDown      = 0.0
#     totalFirstDownPlays         = 0
#     totalRushOnFirstDown        = 0
#     totalPassOnFirstDown        = 0
#     totalCompletionsOnFirstDown = 0
#     rushPctSecondDown           = 0.0
#     passPctSecondDown           = 0.0
#     completionPctSecondDown     = 0.0
#     totalSecondDownPlays        = 0
#     totalRushOnSecondDown        = 0
#     totalPassOnSecondDown        = 0
#     totalCompletionsOnSecondDown = 0
#     rushPctThirdDown            = 0.0
#     passPctThirdDown            = 0.0
#     completionPctThirdDown      = 0.0
#     totalThirdDownPlays         = 0
#     totalRushOnThirdDown        = 0
#     totalPassOnThirdDown        = 0
#     totalCompletionsOnThirdDown = 0

#     listOfPlayTypes = []

    
    
    
#     for play in playByPlayData['items']:
        
#         playType = play['type']['text']
#         if playType not in listOfPlayTypes:
#             listOfPlayTypes.append(playType)

#         teamRefUrl = ""
#         try:
#             teamRefUrl = play['team']['$ref']
#         except(KeyError):
#             continue
        
#         teamIdString = "teams/"+str(teamId)+"?"
        


#         if teamIdString in teamRefUrl:
#             if "No Play" in play['text'] : 
#                 if teamPenaltyText in play['text']:
#                    totalOffensePenalties += 1
#                    totalOffensePenaltyYards += abs(play['statYardage'])
#             else:
#                 if play['start']['down'] == 1:
#                     totalFirstDownPlays += 1
#                     if(play['type']['text'] == "Rush"):
#                         totalRushOnFirstDown += 1
#                     elif (play['type']['text'] == "Pass Reception"):
#                         totalPassOnFirstDown += 1
#                         totalCompletionsOnFirstDown += 1
#                     elif (play['type']['text'] == "Pass Incompletion") or (play['type']['text'] == "Sack") or (play['type']['text'] == "Interception Return Touchdown") or (play['type']['text'] == "Interception Return Touchdown"):
#                         totalPassOnFirstDown += 1
                    
#                 elif play['start']['down'] == 2:
#                     totalSecondDownPlays += 1
#                     if(play['type']['text'] == "Rush"):
#                         totalRushOnSecondDown += 1
#                     elif (play['type']['text'] == "Pass Reception"):
#                         totalPassOnSecondDown += 1
#                         totalCompletionsOnSecondDown += 1
#                     elif (play['type']['text'] == "Pass Incompletion") or (play['type']['text'] == "Sack") or (play['type']['text'] == "Interception Return Touchdown") or (play['type']['text'] == "Interception Return Touchdown"):
#                         totalPassOnSecondDown += 1
                
#                 elif play['start']['down'] == 3:
#                     totalThirdDownPlays +=1
#                     if(play['type']['text'] == "Rush"):
#                         totalRushOnThirdDown += 1
#                     elif (play['type']['text'] == "Pass Reception"):
#                         totalPassOnThirdDown += 1
#                         totalCompletionsOnThirdDown += 1
#                     elif (play['type']['text'] == "Pass Incompletion") or (play['type']['text'] == "Sack") or (play['type']['text'] == "Interception Return Touchdown") or (play['type']['text'] == "Interception Return Touchdown"):
#                         totalPassOnThirdDown += 1



            

#                 # if play['type']['text'] != "Punt" and play['type']['text'] != "Kickoff" and "Field goal" not in play['type']['text']:
#                 #     if play['statYardage'] < 0:
#                 #         totalOffensePenalties +=1
#                 #         totalOffensePenaltyYards += play['statYardage']
#                 # elif play['start']['down']

#             if(play['type']['text'] == "Rush" and play['statYardage']>=10):
#                 teamRushingTenPlus += 1
#             elif (play['type']['text'] == "Pass Reception" and play['statYardage']>=25):
#                 teamPassPlaysTwentyFivePlus += 1
        
#         else:
#             if "No Play" in play['text'] : 
#                 if teamPenaltyText in play['text']:
#                    totalDefensePenalties += 1
#                    totalDefensePenaltyYards += abs(play['statYardage'])
#             else:
#                 if "penalty" in play['shortText'].lower():
#                     if teamPenaltyText in play['text']:
#                         totalDefensePenalties += 1
#                         totalDefensePenaltyYards += abs(play['statYardage'])
#                     if play['type']['text'] == "Pass Incompletion" and play['end']['down'] == 1:
#                         firstDownsByPenaltyGiven += 1
#                 if play['type']['text'] == "Fumble Recovery (Opponent)":
#                     defenseFumblesRecovered += 1



#     # for pt in listOfPlayTypes:
#     #     print(pt)

#     if(totalFirstDownPlays != 0):
#         rushPctFirstDown            = totalRushOnFirstDown/totalFirstDownPlays * 100
#         passPctFirstDown            = totalPassOnFirstDown/totalFirstDownPlays * 100
#         completionPctFirstDown      = totalCompletionsOnFirstDown/totalFirstDownPlays * 100

#     if(totalSecondDownPlays != 0):
#         rushPctSecondDown           = totalRushOnSecondDown/totalSecondDownPlays * 100
#         passPctSecondDown           = totalPassOnSecondDown/totalSecondDownPlays * 100
#         completionPctSecondDown     = totalCompletionsOnThirdDown/totalSecondDownPlays * 100

#     if(totalThirdDownPlays != 0):
#         rushPctThirdDown            = totalRushOnThirdDown/totalThirdDownPlays * 100
#         passPctThirdDown            = totalPassOnThirdDown/totalThirdDownPlays * 100
#         completionPctThirdDown      = totalCompletionsOnThirdDown/totalThirdDownPlays * 100
    
    
#     teamPerf.rushPctFirstDown           = rushPctFirstDown
#     teamPerf.passPctFirstDown           = passPctFirstDown
#     teamPerf.completionPctFirstDown     = completionPctFirstDown
    
#     teamPerf.rushPctSecondDown          = rushPctSecondDown
#     teamPerf.passPctSecondDown          = passPctSecondDown
#     teamPerf.completionPctSecondDown    = completionPctSecondDown
    
#     teamPerf.rushPctThirdDown           = rushPctThirdDown
#     teamPerf.passPctThirdDown           = passPctThirdDown
#     teamPerf.completionPctThirdDown     = completionPctThirdDown

#     teamPerf.rushingPlaysTenPlus        = teamRushingTenPlus
#     teamPerf.passPlaysTwentyFivePlus    = teamPassPlaysTwentyFivePlus

#     teamPerf.totalOffensePenalties      = totalOffensePenalties
#     teamPerf.totalOffensePenaltyYards   = totalOffensePenaltyYards
#     teamPerf.totalDefensePenalties      = totalDefensePenalties
#     teamPerf.totalDefensePenaltyYards   = totalDefensePenaltyYards
#     teamPerf.firstDownsByPenaltyGiven   = firstDownsByPenaltyGiven

#     teamPerf.defenseFumblesRecovered    = defenseFumblesRecovered

#     teamPerf.save()
    
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
    overUnderBetIsCorrect = False

    lineBet = ""
    lineBetIsCorrect = False

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
