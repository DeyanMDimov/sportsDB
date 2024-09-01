from nfl_db.models import nflTeam, nflMatch, teamMatchPerformance, driveOfPlay, player, playerTeamTenure, playerWeekStatus, playByPlay
import time, requests, traceback
from datetime import datetime, date, time, timezone, timedelta


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
                    startDate = datetime(2024, 9, 8)
                )
                print("Player tenure created for ROOKIE.")
            print("Successfully loaded player " + str(playerObj.espnId))
        else:
            print("Player " + str(playerObj.espnId) + " already in system.")
            playerObj.firstSeason = getFirstSeasonYear(athlete['experience']['years'])
            playerObj.team = nflTeam.objects.get(espnId = teamId)
            playerObj.save()
            
            playerTenures = playerTeamTenure.objects.filter(player = playerObj)
            currentSeasonTenures = list(filter(lambda x: x.startDate.year == 2024, playerTenures))
            if athlete['experience']['years'] == 0:    
                if len(list(currentSeasonTenures)) == 0:
                    playerTeamTenure.objects.create(
                        player = playerObj,
                        team = nflTeam.objects.get(espnId = teamId),
                        startDate = datetime(2024, 9, 8)
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
            startDate = datetime(2024, 9, 8)
        )
        print("Player tenure created for ROOKIE.")
    print("Successfully loaded player w/ ESPN ID: " + str(playerObj.espnId) + " - " + playerObj.name)

    return playerObj

def updatePlayerAthletesFromTeamRoster(rosterData, teamId):
    
    athlete_ids = []

    for athlete in rosterData['items']:
        athlete_ids.append(athlete['id'])
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
            

            if athlete['experience']['years'] == 0:
                playerTeamTenure.objects.create(
                    player = playerObj,
                    team = nflTeam.objects.get(espnId = teamId),
                    startDate = datetime(2024, 9, 8)
                )
                print("Player tenure created for ROOKIE.")
            print("Successfully loaded player " + str(playerObj.espnId))

        else:
            print("Player " + str(playerObj.espnId) + " already in system.")
            playerObj.firstSeason = getFirstSeasonYear(athlete['experience']['years'])
            currentPlayerTeam = nflTeam.objects.get(espnId = teamId)
            
            if playerObj.team != currentPlayerTeam:
                updatePlayerTenure(playerObj, teamId)   
                playerObj.team = currentPlayerTeam
                playerObj.save()    

            latestPlayerTenure = None
            latestPlayerTenureList = playerTeamTenure.objects.filter(player = playerObj, endDate = None)
            
            if len(latestPlayerTenureList) != 0:
                latestPlayerTenure = latestPlayerTenureList[0]
            else:
                latestPlayerTenureList = playerTeamTenure.objects.filter(player = playerObj).order_by('-endDate')
                if len(latestPlayerTenureList) != 0:
                    latestPlayerTenure = latestPlayerTenureList[0]
                
            if latestPlayerTenure != None:
                latestplayerTenureTeam = latestPlayerTenure.team
                if latestplayerTenureTeam.espnId != teamId:
                    #latestPlayerTenure.endDate = datetime(2024, 2, 12)
                    playerTeamTenure.objects.create(
                            player = playerObj,
                            team = nflTeam.objects.get(espnId = teamId),
                            startDate = datetime(2024, 9, 1)
                    )
           

            playerTenures = playerTeamTenure.objects.filter(player = playerObj)
            currentSeasonTenures = list(filter(lambda x: x.startDate.year == 2024, playerTenures))
            if athlete['experience']['years'] == 0:    
                if len(list(currentSeasonTenures)) == 0:
                    playerTeamTenure.objects.create(
                        player = playerObj,
                        team = nflTeam.objects.get(espnId = teamId),
                        startDate = datetime(2024, 9, 8)
                    )
                    print()
                    print("Player tenure created for rookie.")
                    print()
            else:
               getPlayerTenures(playerObj)
    
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
            for yr in range(yearToStart, 2024):
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

def updatePlayerTenure(playerObj, teamId):
    latestPlayerTenure = None
    latestPlayerTenureList = playerTeamTenure.objects.filter(player = playerObj, endDate = None)

    if len(latestPlayerTenureList) != 0:
        latestPlayerTenure = playerTeamTenure.objects.filter(player = playerObj, endDate = None)[0]
    else:
        latestPlayerTenure = playerTeamTenure.objects.filter(player = playerObj).order_by('-endDate')[0]

    if len(latestPlayerTenure) != 0:
        playerTenureTeam = latestPlayerTenure.team

        lastPlayerStatus = playerWeekStatus.objects.filter(player = playerObj, team = playerTenureTeam).order_by('-yearOfSeason', '-weekOfSeason')[0]

        if lastPlayerStatus.weekOfSeason == 18:
            latestPlayerTenure.endDate = datetime(2024, 2, 12)
        else:    
            lastDayOfSeasonWeek = nflMatch.objects.filter(weekOfSeason = lastPlayerStatus.weekOfSeason).order_by('-date')[0].date
            latestPlayerTenure.endDate = lastDayOfSeasonWeek
        latestPlayerTenure.save()

        if teamId != None:
            playerTeamTenure.objects.create(
                        player = playerObj,
                        team = nflTeam.objects.get(espnId = teamId),
                        startDate = datetime.now().date
                    )

    



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