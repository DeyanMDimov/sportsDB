from nfl_db import models
from nfl_db.models import nflMatch
from nfl_db.models import teamMatchPerformance
from nfl_db.models import nflTeam
from nfl_db.models import driveOfPlay
from nfl_db.models import playByPlay
import json

# nflTeam, 
# nflMatch, 
# teamMatchPerformance, 
# player, 
# driveOfPlay, 
# playByPlay, 
# playerMatchOffense, 
# playerWeekStatus

def createOrUpdateFinishedNflMatch(nflMatchObject, gameData, gameCompleted, gameOvertime, homeTeamScore, homeTeamStats, awayTeamScore, awayTeamStats, oddsData, playsData, drivesData, weekOfSeason, seasonYear):
    
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
                        temperature = gameData['competitions'][0]['weather']['temperature'],
                        precipitation = gameData['competitions'][0]['weather']['precipitation'],
                        windSpeed = gameData['competitions'][0]['weather']['windSpeed'],
                        
                        preseason= True if int(weekOfSeason) < 0 else False,
                        
                        #-----homeTeam Stats
                        homeTeamPoints = homeTeamScore['value'],
                        homeTeamPointsAllowed = awayTeamScore['value'],
                        homeTeamTotalYards = homeTeamStats['splits']['categories'][1]['stats'][32]['value'],
                        homeTeamYardsAllowed = awayTeamStats['splits']['categories'][1]['stats'][32]['value'],
                        homeTeamRushingYards = homeTeamStats['splits']['categories'][2]['stats'][12]['value'],
                        homeTeamRushYardsAllowed= awayTeamStats['splits']['categories'][2]['stats'][12]['value'],
                        homeTeamReceivingYards= homeTeamStats['splits']['categories'][3]['stats'][12]['value'],
                        homeTeamReceivingYardsAllowed= awayTeamStats['splits']['categories'][3]['stats'][12]['value'],
                        homeTeamGiveaways= homeTeamStats['splits']['categories'][10]['stats'][33]['value'],
                        homeTeamTakeaways= homeTeamStats['splits']['categories'][10]['stats'][37]['value'],
                        homeTeamRushingTDScored= homeTeamStats['splits']['categories'][9]['stats'][7]['value'],
                        homeTeamRushingTDAllowed= awayTeamStats['splits']['categories'][9]['stats'][7]['value'],
                        homeTeamReceivingTDScored= homeTeamStats['splits']['categories'][9]['stats'][5]['value'],
                        homeTeamReceivingTDAllowed= awayTeamStats['splits']['categories'][9]['stats'][8]['value'],
                        homeTeamFGScored= homeTeamStats['splits']['categories'][9]['stats'][1]['value'],
                        homeTeamFGAllowed= awayTeamStats['splits']['categories'][9]['stats'][1]['value'],
                        homeTeamSpecialTeamsPointsScored= homeTeamStats['splits']['categories'][9]['stats'][3]['value'],
                        homeTeamDefensePointsScored= int((homeTeamStats['splits']['categories'][5]['stats'][1]['value']+homeTeamStats['splits']['categories'][0]['stats'][9]['value'])*6),
                        
                        #-----awayTeam stuff
                        awayTeamPoints= awayTeamScore['value'],
                        awayTeamPointsAllowed= homeTeamScore['value'],
                        awayTeamTotalYards= awayTeamStats['splits']['categories'][1]['stats'][32]['value'],
                        awayTeamYardsAllowed= homeTeamStats['splits']['categories'][1]['stats'][32]['value'],
                        awayTeamRushingYards= awayTeamStats['splits']['categories'][2]['stats'][12]['value'],
                        awayTeamRushYardsAllowed= homeTeamStats['splits']['categories'][2]['stats'][12]['value'],
                        awayTeamReceivingYards= awayTeamStats['splits']['categories'][3]['stats'][12]['value'],
                        awayTeamReceivingYardsAllowed= homeTeamStats['splits']['categories'][3]['stats'][12]['value'],
                        awayTeamGiveaways= awayTeamStats['splits']['categories'][10]['stats'][33]['value'],
                        awayTeamTakeaways= awayTeamStats['splits']['categories'][10]['stats'][37]['value'],
                        awayTeamRushingTDScored= awayTeamStats['splits']['categories'][9]['stats'][7]['value'],
                        awayTeamRushingTDAllowed= homeTeamStats['splits']['categories'][9]['stats'][7]['value'],
                        awayTeamReceivingTDScored= awayTeamStats['splits']['categories'][9]['stats'][5]['value'],
                        awayTeamReceivingTDAllowed= homeTeamStats['splits']['categories'][9]['stats'][5]['value'],
                        awayTeamFGScored= awayTeamStats['splits']['categories'][9]['stats'][1]['value'],
                        awayTeamFGAllowed= homeTeamStats['splits']['categories'][9]['stats'][1]['value'],
                        awayTeamSpecialTeamsPointsScored= awayTeamStats['splits']['categories'][9]['stats'][3]['value'],
                        awayTeamDefensePointsScored= int((awayTeamStats['splits']['categories'][5]['stats'][1]['value']+awayTeamStats['splits']['categories'][0]['stats'][9]['value'])*6),
                        
                    )

        homeTeamEspnId = gameData['competitions'][0]['competitors'][0]['id']
        awayTeamEspnId = gameData['competitions'][0]['competitors'][1]['id']
        matchData.homeTeam.add(models.nflTeam.objects.get(espnId=homeTeamEspnId))
        matchData.awayTeam.add(models.nflTeam.objects.get(espnId=awayTeamEspnId))
        
        if len(oddsData['items']) > 2:
            try:
                matchData.overUnderLine= oddsData['items'][0]['overUnder']
                matchData.homeTeamMoneyLine = oddsData['items'][0]['homeTeamOdds']['moneyLine']
                matchData.awayTeamMoneyLine = oddsData['items'][0]['awayTeamOdds']['moneyLine']
                matchData.matchLineHomeTeam = oddsData['items'][0]['spread']
            except: 
                pass
        
        #matchData.homeTeamDefensePointsScored= (int(homeTeamStats['splits']['categories'][5]['stats'][1]['value'])+int(homeTeamStats['splits']['categories'][0]['stats'][9]['value']))*6
        #matchData.awayTeamDefensePointsScored= (int(awayTeamStats['splits']['categories'][5]['stats'][1]['value'])+int(awayTeamStats['splits']['categories'][0]['stats'][9]['value']))*6
        
    else:
        matchData = nflMatchObject
        
        
        matchData.completed = gameCompleted
        matchData.overtime= gameOvertime
        matchData.homeTeamPoints= homeTeamScore['value']
        matchData.homeTeamPointsAllowed= awayTeamScore['value']
        matchData.homeTeamTotalYards= homeTeamStats['splits']['categories'][1]['stats'][32]['value']
        matchData.homeTeamYardsAllowed= awayTeamStats['splits']['categories'][1]['stats'][32]['value']
        matchData.homeTeamRushingYards= homeTeamStats['splits']['categories'][2]['stats'][12]['value']
        matchData.homeTeamRushYardsAllowed= awayTeamStats['splits']['categories'][2]['stats'][12]['value']
        matchData.homeTeamReceivingYards= homeTeamStats['splits']['categories'][3]['stats'][12]['value']
        matchData.homeTeamReceivingYardsAllowed= awayTeamStats['splits']['categories'][3]['stats'][12]['value']
        matchData.homeTeamGiveaways= homeTeamStats['splits']['categories'][10]['stats'][33]['value']
        matchData.homeTeamTakeaways= homeTeamStats['splits']['categories'][10]['stats'][37]['value']
        matchData.homeTeamRushingTDScored= homeTeamStats['splits']['categories'][9]['stats'][7]['value']
        matchData.homeTeamRushingTDAllowed= awayTeamStats['splits']['categories'][9]['stats'][7]['value']
        matchData.homeTeamReceivingTDScored= homeTeamStats['splits']['categories'][9]['stats'][5]['value']
        matchData.homeTeamReceivingTDAllowed= awayTeamStats['splits']['categories'][9]['stats'][8]['value']
        matchData.homeTeamFGScored= homeTeamStats['splits']['categories'][9]['stats'][1]['value']
        matchData.homeTeamFGAllowed= awayTeamStats['splits']['categories'][9]['stats'][1]['value']
        matchData.homeTeamSpecialTeamsPointsScored= homeTeamStats['splits']['categories'][9]['stats'][3]['value']
        matchData.homeTeamDefensePointsScored= int((homeTeamStats['splits']['categories'][5]['stats'][1]['value']+homeTeamStats['splits']['categories'][0]['stats'][9]['value'])*6)
        #awayTeam stuff
        matchData.awayTeamPoints= awayTeamScore['value']
        matchData.awayTeamPointsAllowed= homeTeamScore['value']
        matchData.awayTeamTotalYards= awayTeamStats['splits']['categories'][1]['stats'][32]['value']
        matchData.awayTeamYardsAllowed= homeTeamStats['splits']['categories'][1]['stats'][32]['value']
        matchData.awayTeamRushingYards= awayTeamStats['splits']['categories'][2]['stats'][12]['value']
        matchData.awayTeamRushYardsAllowed= homeTeamStats['splits']['categories'][2]['stats'][12]['value']
        matchData.awayTeamReceivingYards= awayTeamStats['splits']['categories'][3]['stats'][12]['value']
        matchData.awayTeamReceivingYardsAllowed= homeTeamStats['splits']['categories'][3]['stats'][12]['value']
        matchData.awayTeamGiveaways= awayTeamStats['splits']['categories'][10]['stats'][33]['value']
        matchData.awayTeamTakeaways= awayTeamStats['splits']['categories'][10]['stats'][37]['value']
        matchData.awayTeamRushingTDScored= awayTeamStats['splits']['categories'][9]['stats'][7]['value']
        matchData.awayTeamRushingTDAllowed= homeTeamStats['splits']['categories'][9]['stats'][7]['value']
        matchData.awayTeamReceivingTDScored= awayTeamStats['splits']['categories'][9]['stats'][5]['value']
        matchData.awayTeamReceivingTDAllowed= homeTeamStats['splits']['categories'][9]['stats'][5]['value']
        matchData.awayTeamFGScored= awayTeamStats['splits']['categories'][9]['stats'][1]['value']
        matchData.awayTeamFGAllowed= homeTeamStats['splits']['categories'][9]['stats'][1]['value']
        matchData.awayTeamSpecialTeamsPointsScored= awayTeamStats['splits']['categories'][9]['stats'][3]['value']
        matchData.awayTeamDefensePointsScored= int((awayTeamStats['splits']['categories'][5]['stats'][1]['value']+awayTeamStats['splits']['categories'][0]['stats'][9]['value'])*6)
        
        print(awayTeamStats['splits']['categories'][5]['stats'][1]['value'])
        print(awayTeamStats['splits']['categories'][0]['stats'][9]['value'])
    
        if len(oddsData['items']) > 2:
            try:
                matchData.overUnderLine= oddsData['items'][0]['overUnder']
                matchData.homeTeamMoneyLine = oddsData['items'][0]['homeTeamOdds']['moneyLine']
                matchData.awayTeamMoneyLine = oddsData['items'][0]['awayTeamOdds']['moneyLine']
                matchData.matchLineHomeTeam = oddsData['items'][0]['spread']
            except: 
                pass

    
    for individualDrive in drivesData['items']: 
        createDriveOfPlay(individualDrive, matchData)

        


    homeTeamExplosivePlays = getExplosivePlays(playsData, matchData.homeTeamEspnId)
    awayTeamExplosivePlays = getExplosivePlays(playsData, matchData.awayTeamEspnId)

    matchData.homeTeamExplosivePlays = homeTeamExplosivePlays
    matchData.awayTeamExplosivePlays = awayTeamExplosivePlays

    matchData.save()    
    return matchData

def createOrUpdateScheduledNflMatch(nflMatchObject, gameData, oddsData, weekOfSeason, seasonYear):
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
            try:
                matchData.overUnderLine= oddsData['items'][0]['overUnder']
                matchData.homeTeamMoneyLine = oddsData['items'][0]['homeTeamOdds']['moneyLine']
                matchData.awayTeamMoneyLine = oddsData['items'][0]['awayTeamOdds']['moneyLine']
                matchData.matchLineHomeTeam = oddsData['items'][0]['spread']
            except Exception as e:
                print(e)

            matchData.save()   

    return matchData



def updateNflMatch():
    pass

def updateNflMatchOdds():
    pass

def deleteNflMatchesId(matchId):
    pass

def deleteNflMatchesByWeek(yearOfSeason, weekOfSeason):
    pass

def deleteNflMatchesByYear(yearOfSeason):
    pass




def createTeamMatchPerformance():
    pass
def updateTeamMatchPerformance ():
    pass
def deleteTeamMatchPerformance ():
    pass


def createDriveOfPlay (individualDrive, matchData):
    

    addedDrive = driveOfPlay.objects.create(
        espnId = individualDrive['id'],
        sequenceNumber = individualDrive['sequenceNumber'],
        nflMatch = matchData,
       

        timeElapsedInSeconds = individualDrive['timeElapsed']['value'],

        driveResult = setResultOfDrive(individualDrive['result']),
        
        startOfDriveYardLine = individualDrive['start']['yardLine'],
        endOfDriveYardLine = individualDrive['end']['yardLine'],
        numberOffensivePlays = individualDrive['offensivePlays'],
        
        reachedRedZone = True if (individualDrive['end']['yardLine'] >= 75) else False

    )

    teamOnOffenseUrl = individualDrive['team']['$ref']

    if(checkTeamFromRefUrl(teamOnOffenseUrl) == matchData.homeTeam.espnId):
        addedDrive.teamOnOffense = matchData.homeTeam
    else:
        addedDrive.teamOnOffense = matchData.awayTeam

    addedDrive.save()

    # for play in individualDrive['plays']['items']:
    #     createPlayByPlay(play, addedDrive.espnId)



def updateDriveOfPlay ():
    pass
def deleteDriveOfPlay ():
    pass


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
    
    if individualPlay['scoringType']['abbreviation'] == "TD":
        try:
            extraPointOutcome = individualPlay['pointAfterAttempt']['text']
        
        except:
            pass

    

    
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
       
        
        
    
def updatePlayByPlay ():
    pass
def deletePlayByPlay ():
    pass

def createOrUpdateNflMatch(nflMatchObject, gameData, gameCompleted, gameOvertime, homeTeamScore, homeTeamStats, awayTeamScore, awayTeamStats, oddsData, playsData, drivesData, weekOfSeason, seasonYear):
    
    
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
                        playoffs= False,
                        indoorStadium = gameData['competitions'][0]['venue']['indoor'],
                        
                        overtime= gameOvertime,
                        # temperature = 70,
                        # precipitation = 0, 
                        # windSpeed=0,
                        preseason= True if int(weekOfSeason) < 0 else False,
                        homeTeamPoints= homeTeamScore['value'],
                        homeTeamPointsAllowed= awayTeamScore['value'],
                        homeTeamTotalYards= homeTeamStats['splits']['categories'][1]['stats'][32]['value'],
                        homeTeamYardsAllowed= awayTeamStats['splits']['categories'][1]['stats'][32]['value'],
                        homeTeamRushingYards= homeTeamStats['splits']['categories'][2]['stats'][12]['value'],
                        homeTeamRushYardsAllowed= awayTeamStats['splits']['categories'][2]['stats'][12]['value'],
                        homeTeamReceivingYards= homeTeamStats['splits']['categories'][3]['stats'][12]['value'],
                        homeTeamReceivingYardsAllowed= awayTeamStats['splits']['categories'][3]['stats'][12]['value'],
                        homeTeamGiveaways= homeTeamStats['splits']['categories'][10]['stats'][33]['value'],
                        homeTeamTakeaways= homeTeamStats['splits']['categories'][10]['stats'][37]['value'],
                        homeTeamRushingTDScored= homeTeamStats['splits']['categories'][9]['stats'][7]['value'],
                        homeTeamRushingTDAllowed= awayTeamStats['splits']['categories'][9]['stats'][7]['value'],
                        homeTeamReceivingTDScored= homeTeamStats['splits']['categories'][9]['stats'][5]['value'],
                        homeTeamReceivingTDAllowed= awayTeamStats['splits']['categories'][9]['stats'][8]['value'],
                        homeTeamFGScored= homeTeamStats['splits']['categories'][9]['stats'][1]['value'],
                        homeTeamFGAllowed= awayTeamStats['splits']['categories'][9]['stats'][1]['value'],
                        homeTeamSpecialTeamsPointsScored= homeTeamStats['splits']['categories'][9]['stats'][3]['value'],
                        homeTeamDefensePointsScored= int((homeTeamStats['splits']['categories'][5]['stats'][1]['value']+homeTeamStats['splits']['categories'][0]['stats'][9]['value'])*6),
                        #awayTeam stuff
                        awayTeamPoints= awayTeamScore['value'],
                        awayTeamPointsAllowed= homeTeamScore['value'],
                        awayTeamTotalYards= awayTeamStats['splits']['categories'][1]['stats'][32]['value'],
                        awayTeamYardsAllowed= homeTeamStats['splits']['categories'][1]['stats'][32]['value'],
                        awayTeamRushingYards= awayTeamStats['splits']['categories'][2]['stats'][12]['value'],
                        awayTeamRushYardsAllowed= homeTeamStats['splits']['categories'][2]['stats'][12]['value'],
                        awayTeamReceivingYards= awayTeamStats['splits']['categories'][3]['stats'][12]['value'],
                        awayTeamReceivingYardsAllowed= homeTeamStats['splits']['categories'][3]['stats'][12]['value'],
                        awayTeamGiveaways= awayTeamStats['splits']['categories'][10]['stats'][33]['value'],
                        awayTeamTakeaways= awayTeamStats['splits']['categories'][10]['stats'][37]['value'],
                        awayTeamRushingTDScored= awayTeamStats['splits']['categories'][9]['stats'][7]['value'],
                        awayTeamRushingTDAllowed= homeTeamStats['splits']['categories'][9]['stats'][7]['value'],
                        awayTeamReceivingTDScored= awayTeamStats['splits']['categories'][9]['stats'][5]['value'],
                        awayTeamReceivingTDAllowed= homeTeamStats['splits']['categories'][9]['stats'][5]['value'],
                        awayTeamFGScored= awayTeamStats['splits']['categories'][9]['stats'][1]['value'],
                        awayTeamFGAllowed= homeTeamStats['splits']['categories'][9]['stats'][1]['value'],
                        awayTeamSpecialTeamsPointsScored= awayTeamStats['splits']['categories'][9]['stats'][3]['value'],
                        awayTeamDefensePointsScored= int((awayTeamStats['splits']['categories'][5]['stats'][1]['value']+awayTeamStats['splits']['categories'][0]['stats'][9]['value'])*6),
                        #matchLineHomeTeam= (-1 * oddsData['items'][0]['spread']) if Boolean(oddsData['items'][0]['homeTeamOdds']['favorite']) else (oddsData['items'][0]['spread'])
                    )
        homeTeamEspnId = gameData['competitions'][0]['competitors'][0]['id']
        awayTeamEspnId = gameData['competitions'][0]['competitors'][1]['id']
        matchData.homeTeam.add(models.nflTeam.objects.get(espnId=homeTeamEspnId))
        matchData.awayTeam.add(models.nflTeam.objects.get(espnId=awayTeamEspnId))
        if len(oddsData['items']) > 2:
            try:
                matchData.overUnderLine= oddsData['items'][0]['overUnder']
                matchData.homeTeamMoneyLine = oddsData['items'][0]['homeTeamOdds']['moneyLine']
                matchData.awayTeamMoneyLine = oddsData['items'][0]['awayTeamOdds']['moneyLine']
                matchData.matchLineHomeTeam = oddsData['items'][0]['spread']
            except: 
                pass
        #matchData.homeTeamDefensePointsScored= (int(homeTeamStats['splits']['categories'][5]['stats'][1]['value'])+int(homeTeamStats['splits']['categories'][0]['stats'][9]['value']))*6
        #matchData.awayTeamDefensePointsScored= (int(awayTeamStats['splits']['categories'][5]['stats'][1]['value'])+int(awayTeamStats['splits']['categories'][0]['stats'][9]['value']))*6
        print("about to get Explosive Plays")
        
        # homeTeamExplosivePlays = getExplosivePlays(playsData, homeTeamEspnId)
        # awayTeamExplosivePlays = getExplosivePlays(playsData, awayTeamEspnId)
        
        # matchData.homeTeamExplosivePlays = homeTeamExplosivePlays
        # matchData.awayTeamExplosivePlays = awayTeamExplosivePlays

        # matchData.save()
    else:
        matchData = nflMatchObject
        
        if gameCompleted:
            
            matchData.completed = gameCompleted
            matchData.overtime= gameOvertime
            matchData.homeTeamPoints= homeTeamScore['value']
            matchData.homeTeamPointsAllowed= awayTeamScore['value']
            matchData.homeTeamTotalYards= homeTeamStats['splits']['categories'][1]['stats'][32]['value']
            matchData.homeTeamYardsAllowed= awayTeamStats['splits']['categories'][1]['stats'][32]['value']
            matchData.homeTeamRushingYards= homeTeamStats['splits']['categories'][2]['stats'][12]['value']
            matchData.homeTeamRushYardsAllowed= awayTeamStats['splits']['categories'][2]['stats'][12]['value']
            matchData.homeTeamReceivingYards= homeTeamStats['splits']['categories'][3]['stats'][12]['value']
            matchData.homeTeamReceivingYardsAllowed= awayTeamStats['splits']['categories'][3]['stats'][12]['value']
            matchData.homeTeamGiveaways= homeTeamStats['splits']['categories'][10]['stats'][33]['value']
            matchData.homeTeamTakeaways= homeTeamStats['splits']['categories'][10]['stats'][37]['value']
            #homeTeamExplosivePlays= 
            matchData.homeTeamRushingTDScored= homeTeamStats['splits']['categories'][9]['stats'][7]['value']
            matchData.homeTeamRushingTDAllowed= awayTeamStats['splits']['categories'][9]['stats'][7]['value']
            matchData.homeTeamReceivingTDScored= homeTeamStats['splits']['categories'][9]['stats'][5]['value']
            matchData.homeTeamReceivingTDAllowed= awayTeamStats['splits']['categories'][9]['stats'][8]['value']
            matchData.homeTeamFGScored= homeTeamStats['splits']['categories'][9]['stats'][1]['value']
            matchData.homeTeamFGAllowed= awayTeamStats['splits']['categories'][9]['stats'][1]['value']
            matchData.homeTeamSpecialTeamsPointsScored= homeTeamStats['splits']['categories'][9]['stats'][3]['value']
            matchData.homeTeamDefensePointsScored= int((homeTeamStats['splits']['categories'][5]['stats'][1]['value']+homeTeamStats['splits']['categories'][0]['stats'][9]['value'])*6)
            #awayTeam stuff
            matchData.awayTeamPoints= awayTeamScore['value']
            matchData.awayTeamPointsAllowed= homeTeamScore['value']
            matchData.awayTeamTotalYards= awayTeamStats['splits']['categories'][1]['stats'][32]['value']
            matchData.awayTeamYardsAllowed= homeTeamStats['splits']['categories'][1]['stats'][32]['value']
            matchData.awayTeamRushingYards= awayTeamStats['splits']['categories'][2]['stats'][12]['value']
            matchData.awayTeamRushYardsAllowed= homeTeamStats['splits']['categories'][2]['stats'][12]['value']
            matchData.awayTeamReceivingYards= awayTeamStats['splits']['categories'][3]['stats'][12]['value']
            matchData.awayTeamReceivingYardsAllowed= homeTeamStats['splits']['categories'][3]['stats'][12]['value']
            matchData.awayTeamGiveaways= awayTeamStats['splits']['categories'][10]['stats'][33]['value']
            matchData.awayTeamTakeaways= awayTeamStats['splits']['categories'][10]['stats'][37]['value']
            #awayTeamExplosivePlays= 
            matchData.awayTeamRushingTDScored= awayTeamStats['splits']['categories'][9]['stats'][7]['value']
            matchData.awayTeamRushingTDAllowed= homeTeamStats['splits']['categories'][9]['stats'][7]['value']
            matchData.awayTeamReceivingTDScored= awayTeamStats['splits']['categories'][9]['stats'][5]['value']
            matchData.awayTeamReceivingTDAllowed= homeTeamStats['splits']['categories'][9]['stats'][5]['value']
            matchData.awayTeamFGScored= awayTeamStats['splits']['categories'][9]['stats'][1]['value']
            matchData.awayTeamFGAllowed= homeTeamStats['splits']['categories'][9]['stats'][1]['value']
            matchData.awayTeamSpecialTeamsPointsScored= awayTeamStats['splits']['categories'][9]['stats'][3]['value']
            matchData.awayTeamDefensePointsScored= int((awayTeamStats['splits']['categories'][5]['stats'][1]['value']+awayTeamStats['splits']['categories'][0]['stats'][9]['value'])*6)
            
            print(awayTeamStats['splits']['categories'][5]['stats'][1]['value'])
            print(awayTeamStats['splits']['categories'][0]['stats'][9]['value'])
        
        if len(oddsData['items']) > 2:
            try:
                matchData.overUnderLine= oddsData['items'][0]['overUnder']
                matchData.homeTeamMoneyLine = oddsData['items'][0]['homeTeamOdds']['moneyLine']
                matchData.awayTeamMoneyLine = oddsData['items'][0]['awayTeamOdds']['moneyLine']
                matchData.matchLineHomeTeam = oddsData['items'][0]['spread']
            except: 
                pass

    
    for individualDrive in drivesData['items']: 
        teamOnOffenseUrl = individualDrive['team']['$ref']

        addedDrive = driveOfPlay.objects.create(
            espnId = individualDrive['id'],
            sequenceNumber = individualDrive['sequenceNumber'],
            nflMatch = matchData,
            #teamOnOffense = individualDrive[]

            timeElapsedInSeconds = individualDrive['timeElapsed']['value'],

            driveResult = setResultOfDrive(individualDrive['result']),
            
            startOfDriveYardLine = individualDrive['start']['yardLine'],
            endOfDriveYardLine = individualDrive['end']['yardLine'],
            numberOffensivePlays = individualDrive['offensivePlays'],
            
            reachedRedZone = True if (individualDrive['end']['yardLine'] >= 75) else False

        )

        if("teams/"+str(matchData.homeTeamEspnId)+"?") in teamOnOffenseUrl:
            addedDrive.teamOnOffense = matchData.homeTeam
        else:
            addedDrive.teamOnOffense = matchData.awayTeam

        


    homeTeamExplosivePlays = getExplosivePlays(playsData, matchData.homeTeamEspnId)
    awayTeamExplosivePlays = getExplosivePlays(playsData, matchData.awayTeamEspnId)

    matchData.homeTeamExplosivePlays = homeTeamExplosivePlays
    matchData.awayTeamExplosivePlays = awayTeamExplosivePlays

    matchData.save()    
    return matchData




def setResultOfDrive(inputResult):
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
        elif inputResult == "FUMBLE TD":
            return 10
        elif inputResult == "DOWNS":
            return 12
        elif inputResult == "END OF HALF":
            return 13
        elif inputResult == "SAFETY":
            return 16
    
    return switch(inputResult)

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
    
    return teamEspnId
    


def createOrUpdateScheduledNflMatch(nflMatchObject, gameData, oddsData, weekOfSeason, seasonYear):
    if nflMatchObject == None:
        matchData = nflMatch.objects.create(
                        espnId = gameData['id'],
                        datePlayed = gameData['date'],
                        #homeTeam = nflTeam.objects.get(espnId=gameData['competitions'][0]['competitors'][0]['id']),
                        homeTeamEspnId = gameData['competitions'][0]['competitors'][0]['id'],
                        #awayTeam = nflTeam.objects.get(espnId=gameData['competitions'][0]['competitors'][1]['id']),
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
            try:
                matchData.overUnderLine= oddsData['items'][0]['overUnder']
                matchData.homeTeamMoneyLine = oddsData['items'][0]['homeTeamOdds']['moneyLine']
                matchData.awayTeamMoneyLine = oddsData['items'][0]['awayTeamOdds']['moneyLine']
                matchData.matchLineHomeTeam = oddsData['items'][0]['spread']
            except Exception as e:
                print(e)

            matchData.save()   

    return matchData

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
        #totalPointsAllowed
        totalTouchdownsScored   = teamStats['splits']['categories'][1]['stats'][31]['value'],
        totalPenalties          = teamStats['splits']['categories'][10]['stats'][34]['value'],
        totalPenaltyYards       = teamStats['splits']['categories'][10]['stats'][35]['value'],
        #-----offense
        totalYardsGained            = teamStats['splits']['categories'][1]['stats'][32]['value'],
        #totalExplosivePlays         = 
        totalGiveaways              = teamStats['splits']['categories'][10]['stats'][33]['value'],
        #redZoneAttempts             = 
        #redZoneTDConversionPct      = 
        #redZoneFumbles              = 
        #redZoneFumblesLost          = 
        #redZoneInterceptions        = 
        #totalOffensePenalties       = 
        #totalOffensePenaltyYards    = 
        #-----offense-passing
        passCompletions             = teamStats['splits']['categories'][1]['stats'][2]['value'],
        passingAttempts             = teamStats['splits']['categories'][1]['stats'][12]['value'],
        #passPlaysTwentyFivePlus     = 
        totalPassingYards           = teamStats['splits']['categories'][3]['stats'][12]['value'],
        #qbHitsTaken                 = 
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
        # totalPointsAllowed              = 
        # totalYardsAllowedByDefense      = 
        # totalPassYardsAllowed           = 
        # totalRushYardsAllowed           = 
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
        #defenseFumblesRecovered         = 
        defenseFumbleTouchdowns         = teamStats['splits']['categories'][0]['stats'][9]['value'],
        #totalDefensePenalties           = 
        #totalDefensePenaltyYards        = 
        #firstDownsByPenaltyGiven        = 
        #-----specialTeams
        #blockedFieldGoals           = 
        blockedFieldGoalTouchdowns  = teamStats['splits']['categories'][4]['stats'][4]['value'],
        #blockedPunts                = 
        blockedPuntTouchdowns       = teamStats['splits']['categories'][4]['stats'][5]['value'],
        #specialTeamsPenalties       = models.SmallIntegerField(null = True, blank = True)
        #specialTeamsPenaltyYards    = models.SmallIntegerField(null = True, blank = True)
        #-----punting
        totalPunts                  = teamStats['splits']['categories'][8]['stats'][7]['value'],
        #opponentPinnedInsideTen     = 
        #opponentPinnedInsideFive    = 
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




def updateTeamPerformance(teamScore, teamStats, matchEspnId, teamId, opponentId, playByPlayData, seasonWeek, seasonYear):
    teamPerf = teamMatchPerformance.objects.get(matchEspnId = matchEspnId, teamEspnId = teamId)
    nflMatchInstance = models.nflMatch.objects.get(espnId=matchEspnId)
    
    
    if teamId == nflMatchInstance.homeTeamEspnId:
        teamPerf.totalPointsAllowed             = nflMatchInstance.awayTeamPoints
        print("awayTeamPoints: ", nflMatchInstance.awayTeamPoints)
        print("awayTeamDefensePointsScored: ", nflMatchInstance.awayTeamDefensePointsScored)
        teamPerf.totalPointsAllowedByDefense    = nflMatchInstance.awayTeamPoints-nflMatchInstance.awayTeamDefensePointsScored
        teamPerf.totalYardsAllowedByDefense     = nflMatchInstance.homeTeamYardsAllowed
        teamPerf.totalPassYardsAllowed          = nflMatchInstance.homeTeamReceivingYardsAllowed
        teamPerf.totalRushYardsAllowed          = nflMatchInstance.homeTeamRushYardsAllowed
        teamPerf.totalExplosivePlays            = nflMatchInstance.homeTeamExplosivePlays
        if nflMatchInstance.neutralStadium == True:
            teamPerf.atHome = False
        else:
            teamPerf.atHome = True

    elif teamId == nflMatchInstance.awayTeamEspnId:
        teamPerf.totalPointsAllowed             = nflMatchInstance.homeTeamPoints
        teamPerf.totalPointsAllowedByDefense    = nflMatchInstance.homeTeamPoints-nflMatchInstance.homeTeamDefensePointsScored
        teamPerf.totalYardsAllowedByDefense     = nflMatchInstance.awayTeamYardsAllowed
        teamPerf.totalPassYardsAllowed          = nflMatchInstance.awayTeamReceivingYardsAllowed
        teamPerf.totalRushYardsAllowed          = nflMatchInstance.awayTeamRushYardsAllowed
        teamPerf.totalExplosivePlays            = nflMatchInstance.awayTeamExplosivePlays
        teamPerf.atHome = False

    teamPerf.save()

    captureStatsFromPlayByPlay(playByPlayData, teamId, opponentId, teamPerf)


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


def captureStatsFromPlayByPlay(playByPlayData, drivesData, teamId, opponentId, teamPerf):
    
    teamAbbreviation = nflTeam.objects.get(espnId = teamId).abbreviation
    opponentAbbreviation = nflTeam.objects.get(espnId = opponentId).abbreviation

    teamPenaltyText = ("PENALTY on " + teamAbbreviation)
    opponentPenaltyText = ("PENALTY on " + opponentAbbreviation)
    
    teamRushingTenPlus          = 0
    teamPassPlaysTwentyFivePlus = 0
    redZoneAttempts             = 0
    redZoneTDConversionPct      = 0.0
    redZoneFumbles              = 0
    redZoneFumblesLost          = 0
    redZoneInterceptions        = 0
    totalOffensePenalties       = 0
    totalOffensePenaltyYards    = 0
    defenseFumblesRecovered     = 0
    totalDefensePenalties       = 0
    totalDefensePenaltyYards    = 0
    firstDownsByPenaltyGiven    = 0
    opponentPinnedInsideTen     = 0
    opponentPinnedInsideFive    = 0
    drivePinnedInsideTen        = 0
    drivePinnedInsideFive       = 0
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

    
    
    
    for play in playByPlayData['items']:
        
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
            if "No Play" in play['text'] : 
                if teamPenaltyText in play['text']:
                   totalOffensePenalties += 1
                   totalOffensePenaltyYards += abs(play['statYardage'])
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

            if(play['type']['text'] == "Rush" and play['statYardage']>=10):
                teamRushingTenPlus += 1
            elif (play['type']['text'] == "Pass Reception" and play['statYardage']>=25):
                teamPassPlaysTwentyFivePlus += 1
        
        else:
            if "No Play" in play['text'] : 
                if teamPenaltyText in play['text']:
                   totalDefensePenalties += 1
                   totalDefensePenaltyYards += abs(play['statYardage'])
            else:
                if "penalty" in play['shortText'].lower():
                    if teamPenaltyText in play['text']:
                        totalDefensePenalties += 1
                        totalDefensePenaltyYards += abs(play['statYardage'])
                    if play['type']['text'] == "Pass Incompletion" and play['end']['down'] == 1:
                        firstDownsByPenaltyGiven += 1
                if play['type']['text'] == "Fumble Recovery (Opponent)":
                    defenseFumblesRecovered += 1



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

    teamPerf.save()
    
