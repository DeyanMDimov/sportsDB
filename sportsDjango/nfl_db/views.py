from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.core import serializers
import json
from nfl_db.models import nflTeam, nflMatch, teamMatchPerformance, driveOfPlay, player, playerTeamTenure, playerWeekStatus, playByPlay
from nfl_db.models import passerStatSplit, rusherStatSplit, receiverStatSplit
from django.db import models
from nfl_db import businessLogic, crudLogic, players
import datetime, time, requests, traceback

# Create your views here.

def index(request):
    return render (request, 'nfl/base.html')

def getData(request):

    weeksOnPage = weeksOnPage_Helper()
    yearsOnPage = yearsOnPage_Helper()

    pageDictionary = {}
    pageDictionary['weeks'] = weeksOnPage_Helper()
    pageDictionary['years'] = yearsOnPage_Helper()

    if request.method == 'GET':
        if 'season' in request.GET and 'week' in request.GET:     
            inputReq = request.GET
            yearOfSeason = inputReq['season'].strip()
            weekOfSeason = inputReq['week'].strip()

            pageDictionary['sel_year'] = yearOfSeason
            pageDictionary['start_week'] = weekOfSeason
            
            url = ('https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/'+yearOfSeason+'/types/2/weeks/'+weekOfSeason+'/events')
            response = requests.get(url)
            data = response.json()
            gameLinks = data['items']

            for link in gameLinks:
                
                gameDataResponse = requests.get(link['$ref'])
                gameData = gameDataResponse.json()

                matchEspnId = gameData['id']
                dateOfGameFromApi = gameData['date']
                dateOfGame = datetime.datetime.fromisoformat(dateOfGameFromApi.replace("Z", ":00"))

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
                print(gameData['competitions'][0]['odds'])
                oddsResponse = requests.get(oddsUrl)
                oddsData = oddsResponse.json()

                existingMatch = None
                existingHomeTeamPerf = None
                existingAwayTeamPerf = None
                
                responseMessage = ""

                try:
                    existingMatch = nflMatch.objects.get(espnId = matchEspnId)
                except Exception as e:
                        print(e)
                
                
                if datetime.datetime.now()<dateOfGame or gameCompleted == False:
                    print("updating scheduled match")
                    businessLogic.createOrUpdateScheduledNflMatch(existingMatch, gameData, oddsData, weekOfSeason, yearOfSeason)
                else:
                    print("creating or updating matchData")
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

                    
                    
                    matchData = businessLogic.createOrUpdateNflMatch(existingMatch, gameData, gameCompleted, gameOvertime, homeTeamScore, homeTeamStats, awayTeamScore, awayTeamStats, oddsData, playsData, drivesData, weekOfSeason, yearOfSeason)

                    try:
                        businessLogic.createTeamPerformance(homeTeamScore, homeTeamStats, matchData.espnId, matchData.homeTeamEspnId, matchData.awayTeamEspnId, playsData, drivesData, seasonWeek=weekOfSeason, seasonYear=yearOfSeason)
                        businessLogic.createTeamPerformance(awayTeamScore, awayTeamStats, matchData.espnId, matchData.awayTeamEspnId, matchData.homeTeamEspnId, playsData, drivesData, seasonWeek=weekOfSeason, seasonYear=yearOfSeason)

                        pageDictionary['responseMessage'] = "Successfully pulled in Week " + str(weekOfSeason) + " for " + str(yearOfSeason)
                    except Exception as e: 
                        businessLogic.updateTeamPerformance(homeTeamScore, homeTeamStats, matchData.espnId, matchData.homeTeamEspnId, matchData.awayTeamEspnId, playsData, drivesData, weekOfSeason, yearOfSeason)
                        businessLogic.updateTeamPerformance(awayTeamScore, awayTeamStats, matchData.espnId, matchData.awayTeamEspnId, matchData.homeTeamEspnId, playsData, drivesData, weekOfSeason, yearOfSeason)

            return render (request, 'nfl/pullData.html', pageDictionary)

        elif 'espnGameId' in request.GET:
            print("Hit single game endpoint")
            inputReq = request.GET
            yearOfSeason = inputReq['season'].strip()
            weekOfSeason = inputReq['week'].strip()
        
        elif 'season' in request.GET and 'startWeek' in request.GET and 'endWeek' in request.GET:
            inputReq = request.GET
            
            yearOfSeason = int(inputReq['season'].strip())
            
            startWeek = int(inputReq['startWeek'].strip())
            endWeek = int(inputReq['endWeek'].strip())

            if endWeek < startWeek: 
                endWeek = startWeek

            i = startWeek

            pageDictionary['sel_year'] = yearOfSeason
            pageDictionary['start_week'] = startWeek
            pageDictionary['end_week'] = endWeek

            exceptionCollection = []
            exceptionStrings = []

            while i <= endWeek:
                #time.sleep(1)
                weekOfSeason = i
                
                url = ('https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/'+str(yearOfSeason)+'/types/2/weeks/'+str(weekOfSeason)+'/events')
                
                if(weekOfSeason >= 19):
                    playoffWeekOfSeason = weekOfSeason - 18
                    url = ('https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/'+str(yearOfSeason)+'/types/3/weeks/'+str(playoffWeekOfSeason)+'/events')
                
                response = requests.get(url)
                data = response.json()
                gameLinks = data['items']

                for link in gameLinks:
                    
                    gameDataResponse = requests.get(link['$ref'])
                    gameData = gameDataResponse.json()

                    try:
                        crudLogic.processGameData(gameData, weekOfSeason, yearOfSeason)
                    except Exception as e:
                        print(e)
                        for exceptionObj in e.args[0]:
                            if type(exceptionObj) == str:
                                exceptionStrings.append(exceptionObj)
                            else:
                                exceptionCollection.append(exceptionObj)

                            
                
                print("Week ", str(i), " loaded.")
                i += 1
            if startWeek >= endWeek:
                message = "Games loaded for Week " + str(startWeek) + " of " + str(yearOfSeason) + " season."
            else:
                message = "Games loaded for Week " + str(startWeek) + " through Week " + str(endWeek) + " of " + str(yearOfSeason) + " season."
            pageDictionary['message'] = message
           
            if len(exceptionCollection) > 0:
                pageDictionary['exceptionStrings'] = exceptionStrings
                pageDictionary['exceptionArrays'] = exceptionCollection
                print("There were exceptions.")
            
            return render (request, 'nfl/pullData.html', pageDictionary)

        elif 'season' in request.GET and 'full' in request.GET:
            
            print("Hit full season endpoint")
            inputReq = request.GET
            yearOfSeason = inputReq['season'].strip()
            i = 1
            
            while i <= 18: 
                time.sleep(5)
                weekOfSeason = str(i)
            
                url = ('https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/'+yearOfSeason+'/types/2/weeks/'+weekOfSeason+'/events')
                if(yearOfSeason >= 2021):
                    if(weekOfSeason >= 19):
                        playoffWeekOfSeason = weekOfSeason - 18
                        url = ('https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/'+yearOfSeason+'/types/3/weeks/'+playoffWeekOfSeason+'/events')
                
                # elif(yearOfSeason >= 2010):
                #     if(weekOfSeason >= 18):
                #         playoffWeekOfSeason = weekOfSeason - 17
                #         url = ('https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/'+yearOfSeason+'/types/3/weeks/'+playoffWeekOfSeason+'/events')
                
                
                response = requests.get(url)
                data = response.json()
                gameLinks = data['items']

                for link in gameLinks:
                    gameDataResponse = requests.get(link['$ref'])
                    gameData=gameDataResponse.json()
                    crudLogic.processGameData(gameData, i, yearOfSeason)
                            
                
                print("Week ", str(i), " loaded.")
                i += 1
            
            message = "Full " + str(yearOfSeason) + " season loaded."
            return render (request, 'nfl/pullData.html', {'weeks':weeksOnPage, 'years': yearsOnPage, 'message': message})

        # elif 'reset' in request.GET:
        #     crudLogic.resetAllMatchAssociationsForClearing()
        #     return render (request, 'nfl/pullData.html')

        # elif 'resetPerf' in request.GET:
        #     resetMessage = crudLogic.resetAllPerformanceAssociationsForClearing()
        #     return render(request, 'nfl/pullData.html', {"message": resetMessage})
        
        # elif 'deleteDrives' in request.GET:
        #     deleteDrivesMessage = crudLogic.deleteDriveOfPlay()
        #     return render(request, 'nfl/pullData.html', {"message": deleteDrivesMessage})

        elif 'teams' in request.GET:    
            #return render (request, 'nfl/nflhome.html')
   
            name = request.GET
            url = 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams'
            response = requests.get(url)
            data = response.json()
            #print(data, '\n')
            teams = data['sports'][0]['leagues'][0]['teams']
            teamNames = []
            print('                    ')
            #print(teams)
            for rec in teams:
                print(rec['team']['location'])
                print(rec['team']['name'])
                print(rec['team']['displayName'])
                print(rec['team']['abbreviation'])
                print(rec['team']['id'])
                team_data = nflTeam.objects.create(
                    geography= rec['team']['location'],
                    teamName= rec['team']['name'],
                    fullName= rec['team']['displayName'],
                    #division: models.CharField(max_length=10)
                    abbreviation= rec['team']['abbreviation'],
                    startYear= 2002,
                    espnId= rec['team']['id']
                )
                print(team_data)
                teamNames.append(team_data.fullName)
            
            pageDictionary['teamNames'] = teamNames


            return render (request, 'nfl/pullData.html', pageDictionary)
        else:
            return render (request, 'nfl/pullData.html', pageDictionary)
    else: 
        return HttpResponse('unsuccessful')

def getPlayers(request):
    nflTeams = nflTeam.objects.all().order_by('abbreviation')

    yearsOnPage = yearsOnPage_Helper()
   

    weeksOnPage = weeksOnPage_Helper()
    weeksOnPage.insert(0, ["100", "ALL"])
    
    

    pageDictionary = {}
    pageDictionary['weeks'] = weeksOnPage
    pageDictionary['years'] = yearsOnPage
    pageDictionary['teams'] = nflTeams

    if(request.method == 'GET'):
        
        if 'teamName' in request.GET and 'season' in request.GET:
                inputReq = request.GET
                yearOfSeason = inputReq['season'].strip()
                selectedTeam = nflTeam.objects.get(abbreviation = inputReq['teamName'])
                teamId = selectedTeam.espnId
                
                if yearOfSeason == '2025':
                    url = ('https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/' + str(teamId) + '/roster')
                    response = requests.get(url)
                    responseData = response.json()
                    rosterData = responseData['athletes']

                    for subsection in rosterData:
                        players.updatePlayerAthletesFromTeamRoster(subsection, teamId)


                    playersLoaded = player.objects.filter(team = selectedTeam).order_by('sideOfBall').order_by('playerPosition')

                    playerTenuresLoaded = []
                    for pl in playersLoaded:
                        individualPlayerTenures = playerTeamTenure.objects.filter(player = pl)
                        for ipt in individualPlayerTenures:
                            playerTenuresLoaded.append(ipt)
                    
                    # print(playerTenuresLoaded)

                    return render(request, 'nfl/players.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage, 'selTeam': selectedTeam, 'players': playersLoaded, 'season': inputReq['season'], 'tenures': playerTenuresLoaded})

        elif 'position' in request.GET:
            inputReq = request.GET
            selectedPosition = inputReq['position'].strip()
            listAllStatus = len(playerWeekStatus.objects.all())
            print(listAllStatus)
            playersLoaded = sorted(player.objects.filter(playerPosition = selectedPosition), key = lambda x: x.team.abbreviation)

            return render(request, 'nfl/players.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage, 'allPlayers': playersLoaded})

        elif 'week' in request.GET:
            inputReq = request.GET
            yearOfSeason = inputReq['season'].strip()
            weekOfSeason = int(inputReq['week'].strip())
            if weekOfSeason == 100:
                #print("We Get here")
                endRangeWeek = 19
                if int(yearOfSeason) == 2024:

                    endRangeWeek = 12
                athleteAvailabilitySeason = []
                for wk in range (1, endRangeWeek):
                    if 'team' in inputReq:
                        selectedTeam = nflTeam.objects.get(abbreviation = inputReq['team'])
                        teamId = selectedTeam.espnId
                        selectedMatchQuerySet = nflMatch.objects.filter(weekOfSeason = wk, yearOfSeason = yearOfSeason, homeTeamEspnId = teamId)
                        if(len(selectedMatchQuerySet) == 0):
                            selectedMatchQuerySet = nflMatch.objects.filter(weekOfSeason = wk, yearOfSeason = yearOfSeason, awayTeamEspnId = teamId)
                            if(len(selectedMatchQuerySet) == 0):
                                
                                for plRec in athleteAvailabilitySeason:
                                    plRec[1].append("Bye")
                                continue
                        
                        selectedMatch = selectedMatchQuerySet[0]
                        matchId = selectedMatch.espnId
                        
                        gameRosterUrl='http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/'+str(matchId)+'/competitions/'+str(matchId)+'/competitors/'+str(teamId)+'/roster'
                        gameRosterResponse = requests.get(gameRosterUrl)
                        print(gameRosterUrl)
                        gameRosterData = gameRosterResponse.json()

                        
                        try:
                            athleteAvailability = crudLogic.processGameRosterForAvailability(gameRosterData, selectedTeam, yearOfSeason, wk)
                        except Exception as e:
                            print("Wk: " + str(wk))
                            print("EndRangeWeek" + str(endRangeWeek))
                            break
                            
                        athleteAvailabilitySeason = crudLogic.organizeRosterAvailabilityArrays(athleteAvailabilitySeason, athleteAvailability, wk)


                    
                    else:
                        return render(request, 'nfl/players.html', pageDictionary)
                
                return render(request, 'nfl/players.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage, 'athleteAvailSeason': athleteAvailabilitySeason, 'sel_Team': inputReq['team'], 'sel_Year': yearOfSeason,})
                
            else:
                if 'team' in inputReq:

                    selectedTeam = nflTeam.objects.get(abbreviation = inputReq['team'])
                    teamId = selectedTeam.espnId
                    selectedMatchQuerySet = nflMatch.objects.filter(weekOfSeason = weekOfSeason, yearOfSeason = yearOfSeason, homeTeamEspnId = teamId)
                    if(len(selectedMatchQuerySet) == 0):
                        selectedMatchQuerySet = nflMatch.objects.filter(weekOfSeason = weekOfSeason, yearOfSeason = yearOfSeason, awayTeamEspnId = teamId)
                        if(len(selectedMatchQuerySet) == 0):
                            responseMessage = "Week " + str(weekOfSeason) + " was the Bye week for " + selectedTeam.abbreviation
                            return render(request, 'nfl/players.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage, 'responseMessage': responseMessage})
                    
                    selectedMatch = selectedMatchQuerySet[0]
                    matchId = selectedMatch.espnId
                    
                    gameRosterUrl='http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/'+str(matchId)+'/competitions/'+str(matchId)+'/competitors/'+str(teamId)+'/roster'
                    gameRosterResponse = requests.get(gameRosterUrl)
                    print(gameRosterUrl)
                    gameRosterData = gameRosterResponse.json()

                    athleteAvailability = crudLogic.processGameRosterForAvailability(gameRosterData, selectedTeam, yearOfSeason, weekOfSeason)

                    # print(weekOfSeason)
                    return render(request, 'nfl/players.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage, 'athleteAvail': athleteAvailability, 'sel_Team': inputReq['team'], 'sel_Year': yearOfSeason, 'sel_Week': weekOfSeason})
                
                
        
    return render(request, 'nfl/players.html', pageDictionary)

def getInjuryStatus(request):
    print("Hit this")
    if(request.method == 'GET'):
        activeTeams = nflTeam.objects.all()
        for team in activeTeams:
            crudLogic.getCurrentWeekAthletesStatus(team.espnId)
        
        return JsonResponse({}, status="200")
    

def loadModel(request, target):
    weeksOnPage = weeksOnPage_Helper()
    
    yearsOnPage = yearsOnPage_Helper()
    
    movingAvgLenOptions = []
    for ma in range(3,17):
        movingAvgLenOptions.append(ma)

    inputReq = request.GET
    reqTarget = target
    if request.method == 'GET':
       
        if 'season' in request.GET and 'week' in request.GET:  
            
            yearOfSeason = inputReq['season'].strip()
            weekOfSeason = inputReq['week'].strip()
            selectedModel = inputReq['model']
            selectedLen = int(inputReq['movingavg'])

            
            anyGamesCompleted = False

            modelResults = []

            gamesInWeek = nflMatch.objects.filter(yearOfSeason = yearOfSeason).filter(weekOfSeason = int(weekOfSeason))

            # if len(gamesInWeek) == 0:
                
            for match in gamesInWeek:
                team1 = nflTeam.objects.get(espnId = match.homeTeamEspnId)
                team2 = nflTeam.objects.get(espnId = match.awayTeamEspnId)

                homeTeamInjuries = []
                awayTeamInjuries = []

                homeTeamInjuriesInclDuplicates = playerWeekStatus.objects.filter(weekOfSeason = weekOfSeason, yearOfSeason = yearOfSeason, team = team1).exclude(playerStatus = 1).order_by('player__espnId', 'reportDate')#.distinct('player__espnId')



                for playerInjury in homeTeamInjuriesInclDuplicates:
                    if len(homeTeamInjuries) == 0:
                        homeTeamInjuries.append(playerInjury)
                    else: 
                        thisPlayersInjury = list(filter(lambda x: x.player == playerInjury.player, homeTeamInjuries))

                        if len(list(thisPlayersInjury)) == 0:
                            homeTeamInjuries.append(playerInjury)
                        elif len(thisPlayersInjury) ==  1:
                            try:
                                if thisPlayersInjury[0].reportDate < playerInjury.reportDate:
                                    homeTeamInjuries.remove(thisPlayersInjury[0])
                                    homeTeamInjuries.append(playerInjury)
                            except: 
                                pass
                            
                
                awayTeamInjuriesInclDuplicates = playerWeekStatus.objects.filter(weekOfSeason = weekOfSeason, yearOfSeason = yearOfSeason, team = team2).exclude(playerStatus = 1).order_by('player__espnId', 'reportDate')#.distinct('player__espnId')

                
                for playerInjury in awayTeamInjuriesInclDuplicates:
                    if len(homeTeamInjuries) == 0:
                        awayTeamInjuries.append(playerInjury)
                    else: 
                        thisPlayersInjury = list(filter(lambda x: x.player == playerInjury.player, awayTeamInjuries))

                        if len(list(thisPlayersInjury)) == 0:
                            awayTeamInjuries.append(playerInjury)
                        elif len(thisPlayersInjury) ==  1:
                            if thisPlayersInjury[0].reportDate != None:
                                try:
                                    if thisPlayersInjury[0].reportDate < playerInjury.reportDate:
                                        awayTeamInjuries.remove(thisPlayersInjury[0])
                                        awayTeamInjuries.append(playerInjury)
                                except:
                                    pass


                if selectedModel == "v1" or selectedModel == "v1.5":
                    
                    if selectedModel == "v1":
                        individualModelResult = businessLogic.generateBettingModelHistV1(match)

                    else:
                        individualModelResult = businessLogic.generateBettingModelHistV1(match, int(selectedLen))
                    gameEspnId = match.espnId
                    
                    if(match.completed):
                        anyGamesCompleted = True
                       

                        if match.completed:     
                            individualModelResult.team1ActualYards = match.homeTeamTotalYards
                            individualModelResult.team2ActualYards = match.awayTeamTotalYards
                            individualModelResult.team1ActualPoints = match.homeTeamPoints
                            individualModelResult.team2ActualPoints = match.awayTeamPoints
                            individualModelResult.actualSpread = match.awayTeamPoints - match.homeTeamPoints
                            individualModelResult.actualTotal = match.homeTeamPoints + match.awayTeamPoints
                            individualModelResult.gameCompleted = True
                    
                        if match.overUnderLine != 0 and match.overUnderLine != None:
                            individualModelResult = businessLogic.checkModelBets(match.overUnderLine, match.matchLineHomeTeam, individualModelResult, team1.abbreviation, team2.abbreviation)
                    else:
                        if match.overUnderLine != 0 and match.overUnderLine != None:
                            individualModelResult.bookProvidedTotal = match.overUnderLine
                        if match.matchLineHomeTeam != None:
                            individualModelResult.bookProvidedSpread = match.matchLineHomeTeam
                    
                    individualModelResult.homeTeamInjuries = sorted(homeTeamInjuries, key= lambda x: x.playerStatus) 
                    individualModelResult.awayTeamInjuries = sorted(awayTeamInjuries, key= lambda x: x.playerStatus) 
                    modelResults.append(individualModelResult)
                    

                elif(selectedModel == "v2"):
                    if int(weekOfSeason) == 1:
                        individualModelResult = businessLogic.generateBettingModelHistV2(match, week1 = True)
                    else:
                        individualModelResult = businessLogic.generateBettingModelHistV2(match)

                    gameEspnId = match.espnId

                    if(match.completed):
                        anyGamesCompleted = True
                        team1 = nflTeam.objects.get(espnId = match.homeTeamEspnId)
                        team2 = nflTeam.objects.get(espnId = match.awayTeamEspnId)
                        
                        team1_drives = driveOfPlay.objects.filter(nflMatch = match, teamOnOffense = team1)
                        team2_drives = driveOfPlay.objects.filter(nflMatch = match, teamOnOffense = team2)

                        if match.awayTeamPoints != None:     
                            individualModelResult.team1ActualYards = match.homeTeamTotalYards
                            individualModelResult.team1ActualPoints = match.homeTeamPoints
                            individualModelResult.actual_t1_OffenseDrives = len(team1_drives)
                            individualModelResult.actual_t1_DrivesRedZone = len(team1_drives.filter(reachedRedZone = True))
                            individualModelResult.actual_t1_RedZoneConv = len(team1_drives.filter(driveResult = 1))
                            
                            individualModelResult.team2ActualYards = match.awayTeamTotalYards
                            individualModelResult.team2ActualPoints = match.awayTeamPoints
                            individualModelResult.actual_t2_OffenseDrives = len(team2_drives)
                            individualModelResult.actual_t2_DrivesRedZone = len(team2_drives.filter(reachedRedZone = True))
                            individualModelResult.actual_t2_RedZoneConv = len(team2_drives.filter(driveResult = 1))
                            
                            individualModelResult.actualSpread = match.awayTeamPoints - match.homeTeamPoints
                            individualModelResult.actualTotal = match.homeTeamPoints + match.awayTeamPoints
                            individualModelResult.gameCompleted = True

                        if match.overUnderLine != 0 and match.overUnderLine != None:      
                            individualModelResult = businessLogic.checkModelBets(match.overUnderLine, match.matchLineHomeTeam, individualModelResult, team1.abbreviation, team2.abbreviation)
                    else:
                        if match.overUnderLine != 0 and match.overUnderLine != None:
                            individualModelResult.bookProvidedTotal = match.overUnderLine
                        if match.matchLineHomeTeam != None:
                            individualModelResult.bookProvidedSpread = match.matchLineHomeTeam

                    individualModelResult.homeTeamInjuries = sorted(homeTeamInjuries, key= lambda x: x.playerStatus)
                    individualModelResult.awayTeamInjuries = sorted(awayTeamInjuries, key= lambda x: x.playerStatus)

                    modelResults.append(individualModelResult)
                

            overUnderCorrect = len(list(filter(lambda x: x.overUnderBetIsCorrect == 'True', modelResults)))
            overUnderWrong = len(list(filter(lambda x: x.overUnderBetIsCorrect == 'False', modelResults)))
            overUnderPush = len(list(filter(lambda x: x.overUnderBetIsCorrect == 'Push', modelResults)))
            overUnderRecord = str(overUnderCorrect) + " - " + str(overUnderWrong) + " - " + str(overUnderPush)

            lineBetCorrect = len(list(filter(lambda x: x.lineBetIsCorrect == "True", modelResults)))
            lineBetWrong = len(list(filter(lambda x: x.lineBetIsCorrect == "False", modelResults)))
            lineBetPush = len(list(filter(lambda x: x.lineBetIsCorrect == "Push", modelResults)))
            lineBetRecord = str(lineBetCorrect) + " - " + str(lineBetWrong) + " - " + str(lineBetPush)
                
            modelResults = businessLogic.setBetRankingsV1(modelResults)
            for m in modelResults:
                print(m.team1Name + " vs. " + m.team2Name + " Bet Rank Score: " + str(m.betRankScore))
            
            

            print(selectedModel)
            if(reqTarget == 'showModel'):
                return render(request, 'nfl/bettingModel.html', {"selectedModel": selectedModel, "modelResults": modelResults, "yearOfSeason": yearOfSeason, "weekOfSeason":weekOfSeason,'weeks':weeksOnPage, 'years': yearsOnPage, 'ma_Len': movingAvgLenOptions, 'sel_ma': selectedLen})
            else:
                return render(request, 'nfl/modelSummary.html', {"selectedModel": selectedModel, "modelResults": modelResults, "yearOfSeason": yearOfSeason, "weekOfSeason":weekOfSeason, 'weeks':weeksOnPage, 'years': yearsOnPage, 'ma_Len': movingAvgLenOptions, 'anyCompleted': anyGamesCompleted, 'ouRecord': overUnderRecord, \
                                                                 'lbRecord': lineBetRecord, 'sel_ma': selectedLen, 'int_sel_week': int(weekOfSeason)})
        else: 
            if(reqTarget == 'showModel'):
                return render(request, 'nfl/bettingModel.html', {'weeks':weeksOnPage, 'years': yearsOnPage, 'ma_Len': movingAvgLenOptions})
            else:
                return render(request, 'nfl/modelSummary.html', {'weeks':weeksOnPage, 'years': yearsOnPage, 'ma_Len': movingAvgLenOptions})
    else:
        if(reqTarget == 'model'):
            return render(request, 'nfl/bettingModel.html', {'weeks':weeksOnPage, 'years': yearsOnPage, 'ma_Len': movingAvgLenOptions})
        else:
            return render(request, 'nfl/modelSummary.html', {'weeks':weeksOnPage, 'years': yearsOnPage, 'ma_Len': movingAvgLenOptions})

def loadModelYear(request):
    yearsOnPage = yearsOnPage_Helper()   

    numResultsSelect = []
    numResultsSelect.append(20)
    for nr in range(2, 11):
        numResultsSelect.append(nr)
    
    

    topNumResults = 20

    modelsOnPage = []
    modelsOnPage.append(['v1', 'V1.0 (Avg Yds/Yds per Pt)'])
    modelsOnPage.append(['v1.5', 'V1.5 (V1 with Moving Avg.)'])
    #modelsOnPage.append(['v2','V2.0 (Drives vs Drive Result)'])
    
    movingAvgLenOptions = []
    for ma in range(3,17):
        movingAvgLenOptions.append(ma)

    inputReq = request.GET

    if request.method == 'GET':
       
        if 'season' in request.GET and 'model' in request.GET: 
            selectedModel = inputReq['model']
            yearOfSeason = inputReq['season'].strip()
            selectedLen = int(inputReq['movingavg'])


            topNumResults = int(inputReq['topNumResults'].strip())
            # calculcatingCurrentSeason = businessLogic.checkIfCurrentSeason(yearOfSeason)

            seasonResults = []

            weeksInSeason = 18 if int(yearOfSeason) >= 2021 else 17

            totalOverUnderWins = 0
            totalOverUnderLosses = 0
            totalOverUnderPushes = 0
            totalLineBetWins = 0
            totalLineBetLosses = 0
            totalLineBetPushes = 0

            # if calculcatingCurrentSeason:
            #     for wk in range (2, weeksInSeason+1):
            #         url = ('https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/'+yearOfSeason+'/types/2/weeks/'+str(wk)+'/events')
            #         response = requests.get(url)
            #         data = response.json()
            #         gameLinks = data['items']
            #         modelWeekResults = []
            #         for link in gameLinks:
                        
            #             gameDataResponse = requests.get(link['$ref'])
            #             gameData = gameDataResponse.json()
            #             completed = (gameData['competitions'][0]['boxscoreSource']['state'] == "full" and gameData['competitions'][0]['liveAvailable'] == False )

            #             if selectedModel == "v1":
            #                 individualModelResult = businessLogic.generateBettingModelV1(gameData, wk, yearOfSeason)

            #                 gameEspnId = gameData['id']
            #                 match = nflMatch.objects.get(espnId = gameEspnId)

            #                 if(completed):
            #                     team1 = nflTeam.objects.get(espnId = match.homeTeamEspnId)
            #                     team2 = nflTeam.objects.get(espnId = match.awayTeamEspnId)

            #                     #print("Game ID: ", gameEspnId)
            #                     if match.awayTeamPoints != None:     
            #                         individualModelResult.team1ActualYards = match.homeTeamTotalYards
            #                         individualModelResult.team2ActualYards = match.awayTeamTotalYards
            #                         individualModelResult.team1ActualPoints = match.homeTeamPoints
            #                         individualModelResult.team2ActualPoints = match.awayTeamPoints
            #                         individualModelResult.actualSpread = match.awayTeamPoints - match.homeTeamPoints
            #                         individualModelResult.actualTotal = match.homeTeamPoints + match.awayTeamPoints
            #                         individualModelResult.gameCompleted = True
                            
            #                     if match.overUnderLine != 0 and match.overUnderLine != None:
            #                         individualModelResult = businessLogic.checkModelBets(match.overUnderLine, match.matchLineHomeTeam, individualModelResult, team1.abbreviation, team2.abbreviation)
                            

            #             elif(selectedModel == "v2"):
            #                 individualModelResult = businessLogic.generateBettingModelV2(gameData, wk, yearOfSeason)

            #                 gameEspnId = gameData['id']
            #                 match = nflMatch.objects.get(espnId = gameEspnId)
                            

            #                 if(completed):
            #                     team1 = nflTeam.objects.get(espnId = match.homeTeamEspnId)
            #                     team2 = nflTeam.objects.get(espnId = match.awayTeamEspnId)
            #                     #team1_performance = teamMatchPerformance.objects.get(matchEspnId = gameEspnId, teamEspnId = match.homeTeamEspnId)
            #                     #team2_performance = teamMatchPerformance.objects.get(matchEspnId = gameEspnId, teamEspnId = match.awayTeamEspnId)    
            #                     team1_drives = driveOfPlay.objects.filter(nflMatch = match, teamOnOffense = team1)
            #                     team2_drives = driveOfPlay.objects.filter(nflMatch = match, teamOnOffense = team2)

            #                     if match.awayTeamPoints != None:     
            #                         individualModelResult.team1ActualYards = match.homeTeamTotalYards
            #                         individualModelResult.team1ActualPoints = match.homeTeamPoints
            #                         individualModelResult.actual_t1_OffenseDrives = len(team1_drives)
            #                         individualModelResult.actual_t1_DrivesRedZone = len(team1_drives.filter(reachedRedZone = True))
            #                         individualModelResult.actual_t1_RedZoneConv = len(team1_drives.filter(driveResult = 1))
                                    
                                    
            #                         individualModelResult.team2ActualYards = match.awayTeamTotalYards
            #                         individualModelResult.team2ActualPoints = match.awayTeamPoints
            #                         individualModelResult.actual_t2_OffenseDrives = len(team2_drives)
            #                         individualModelResult.actual_t2_DrivesRedZone = len(team2_drives.filter(reachedRedZone = True))
            #                         individualModelResult.actual_t2_RedZoneConv = len(team2_drives.filter(driveResult = 1))
                                    
                                    
            #                         individualModelResult.actualSpread = match.awayTeamPoints - match.homeTeamPoints
            #                         individualModelResult.actualTotal = match.homeTeamPoints + match.awayTeamPoints
            #                         individualModelResult.gameCompleted = True

            #                     if match.overUnderLine != 0 and match.overUnderLine != None:      
            #                         individualModelResult = businessLogic.checkModelBets(match.overUnderLine, match.matchLineHomeTeam, individualModelResult, team1.abbreviation, team2.abbreviation)
                            
            #             modelWeekResults.append(individualModelResult)

            #         overUnderCorrect = len(list(filter(lambda x: x.overUnderBetIsCorrect == 'True', modelWeekResults)))
            #         overUnderWrong = len(list(filter(lambda x: x.overUnderBetIsCorrect == 'False', modelWeekResults)))
            #         overUnderPush = len(list(filter(lambda x: x.overUnderBetIsCorrect == 'Push', modelWeekResults)))
            #         overUnderRecord = str(overUnderCorrect) + " - " + str(overUnderWrong) + " - " + str(overUnderPush)

            #         lineBetCorrect = len(list(filter(lambda x: x.lineBetIsCorrect == "True", modelWeekResults)))
            #         lineBetWrong = len(list(filter(lambda x: x.lineBetIsCorrect == "False", modelWeekResults)))
            #         lineBetPush = len(list(filter(lambda x: x.lineBetIsCorrect == "Push", modelWeekResults)))
            #         lineBetRecord = str(lineBetCorrect) + " - " + str(lineBetWrong) + " - " + str(lineBetPush)

            #         totalOverUnderWins += overUnderCorrect
            #         totalOverUnderLosses += overUnderWrong

            #         totalLineBetWins += lineBetCorrect
            #         totalLineBetLosses += lineBetWrong

            #         seasonResults.append([wk, overUnderRecord, lineBetRecord, modelWeekResults])
            
            # else:
            for wk in range (2, weeksInSeason+1):
                gamesInWeek = nflMatch.objects.filter(yearOfSeason = yearOfSeason).filter(weekOfSeason = wk)
                
                gamesInWeekUnfinished = nflMatch.objects.filter(yearOfSeason = yearOfSeason, weekOfSeason = wk, completed = False)
                if len(gamesInWeekUnfinished) == 0:
                    modelWeekResults = []
                    for match in gamesInWeek:
                        
                        completed = True

                        if selectedModel == "v1" or selectedModel == "v1.5":
                            if selectedModel == "v1.5":
                                individualModelResult = businessLogic.generateBettingModelHistV1(match, selectedLen)
                            else:
                                individualModelResult = businessLogic.generateBettingModelHistV1(match)

                            gameEspnId = match.espnId

                            if(completed):
                                team1 = nflTeam.objects.get(espnId = match.homeTeamEspnId)
                                team2 = nflTeam.objects.get(espnId = match.awayTeamEspnId)

                                if match.awayTeamPoints != None:     
                                    individualModelResult.team1ActualYards = match.homeTeamTotalYards
                                    individualModelResult.team2ActualYards = match.awayTeamTotalYards
                                    individualModelResult.team1ActualPoints = match.homeTeamPoints
                                    individualModelResult.team2ActualPoints = match.awayTeamPoints
                                    individualModelResult.actualSpread = match.awayTeamPoints - match.homeTeamPoints
                                    individualModelResult.actualTotal = match.homeTeamPoints + match.awayTeamPoints
                                    individualModelResult.gameCompleted = True
                            
                                if match.overUnderLine != 0 and match.overUnderLine != None:
                                    individualModelResult = businessLogic.checkModelBets(match.overUnderLine, match.matchLineHomeTeam, individualModelResult, team1.abbreviation, team2.abbreviation)
                            

                        elif(selectedModel == "v2"):
                            individualModelResult = businessLogic.generateBettingModelHistV2(match)

                            gameEspnId = match.espnId

                            if(completed):
                                team1 = nflTeam.objects.get(espnId = match.homeTeamEspnId)
                                team2 = nflTeam.objects.get(espnId = match.awayTeamEspnId)
                                #team1_performance = teamMatchPerformance.objects.get(matchEspnId = gameEspnId, teamEspnId = match.homeTeamEspnId)
                                #team2_performance = teamMatchPerformance.objects.get(matchEspnId = gameEspnId, teamEspnId = match.awayTeamEspnId)    
                                team1_drives = driveOfPlay.objects.filter(nflMatch = match, teamOnOffense = team1)
                                team2_drives = driveOfPlay.objects.filter(nflMatch = match, teamOnOffense = team2)

                                if match.awayTeamPoints != None:     
                                    individualModelResult.team1ActualYards = match.homeTeamTotalYards
                                    individualModelResult.team1ActualPoints = match.homeTeamPoints
                                    individualModelResult.actual_t1_OffenseDrives = len(team1_drives)
                                    individualModelResult.actual_t1_DrivesRedZone = len(team1_drives.filter(reachedRedZone = True))
                                    individualModelResult.actual_t1_RedZoneConv = len(team1_drives.filter(driveResult = 1))
                                    
                                    
                                    individualModelResult.team2ActualYards = match.awayTeamTotalYards
                                    individualModelResult.team2ActualPoints = match.awayTeamPoints
                                    individualModelResult.actual_t2_OffenseDrives = len(team2_drives)
                                    individualModelResult.actual_t2_DrivesRedZone = len(team2_drives.filter(reachedRedZone = True))
                                    individualModelResult.actual_t2_RedZoneConv = len(team2_drives.filter(driveResult = 1))
                                    
                                    
                                    individualModelResult.actualSpread = match.awayTeamPoints - match.homeTeamPoints
                                    individualModelResult.actualTotal = match.homeTeamPoints + match.awayTeamPoints
                                    individualModelResult.gameCompleted = True

                                if match.overUnderLine != 0 and match.overUnderLine != None:      
                                    individualModelResult = businessLogic.checkModelBets(match.overUnderLine, match.matchLineHomeTeam, individualModelResult, team1.abbreviation, team2.abbreviation)
                            
                        modelWeekResults.append(individualModelResult)

                    modelWeekResults = businessLogic.setBetRankingsV1(modelWeekResults)

                    topModelWeekResults = []
                    if topNumResults == 20:
                        for modelRslt in modelWeekResults:
                            topModelWeekResults.append(modelRslt)
                    else:
                        for i in range(0, topNumResults):
                            topModelWeekResults.append(modelWeekResults[i])

                    overUnderCorrect = len(list(filter(lambda x: x.overUnderBetIsCorrect == 'True', topModelWeekResults)))
                    overUnderWrong = len(list(filter(lambda x: x.overUnderBetIsCorrect == 'False', topModelWeekResults)))
                    overUnderPush = len(list(filter(lambda x: x.overUnderBetIsCorrect == 'Push', topModelWeekResults)))
                    overUnderRecord = str(overUnderCorrect) + " - " + str(overUnderWrong) + " - " + str(overUnderPush)

                    lineBetCorrect = len(list(filter(lambda x: x.lineBetIsCorrect == "True", topModelWeekResults)))
                    lineBetWrong = len(list(filter(lambda x: x.lineBetIsCorrect == "False", topModelWeekResults)))
                    lineBetPush = len(list(filter(lambda x: x.lineBetIsCorrect == "Push", topModelWeekResults)))
                    lineBetRecord = str(lineBetCorrect) + " - " + str(lineBetWrong) + " - " + str(lineBetPush)
                    

                    totalOverUnderWins += overUnderCorrect
                    totalOverUnderLosses += overUnderWrong
                    totalOverUnderPushes += overUnderPush

                    totalLineBetWins += lineBetCorrect
                    totalLineBetLosses += lineBetWrong
                    totalLineBetPushes += lineBetPush

                    seasonResults.append([wk, overUnderRecord, lineBetRecord, topModelWeekResults])

            totalOverUnderRecord = str(totalOverUnderWins) + " - " + str(totalOverUnderLosses) + " - " + str(totalOverUnderPushes)
            totalLineBetRecord = str(totalLineBetWins) + " - " + str(totalLineBetLosses) + " - " + str(totalLineBetPushes)


            return render(request, 'nfl/yearlySummary.html', {'models': modelsOnPage, 'years': yearsOnPage, 'selectedModel': selectedModel, 'seasonResults':seasonResults, 'ouRecord': totalOverUnderRecord, 'lineBetRecord': totalLineBetRecord, 'yearOfSeason':yearOfSeason, 'nrSelect': numResultsSelect, 'topNumResults': topNumResults, 'ma_Len':movingAvgLenOptions, 'sel_ma':selectedLen})
        else: 
            return render(request, 'nfl/yearlySummary.html', {'models': modelsOnPage, 'years': yearsOnPage, 'nrSelect': numResultsSelect, 'topNumResults': topNumResults, 'ma_Len':movingAvgLenOptions})
    else:
        return render(request, 'nfl/yearlySummary.html', {'models': modelsOnPage, 'years': yearsOnPage, 'nrSelect': numResultsSelect, 'topNumResults': topNumResults, 'ma_Len':movingAvgLenOptions})

def fullTeamStats(request):

    yearsOnPage = yearsOnPage_Helper()
    
    inputReq = request.GET

    if(request.method == 'GET'):
        if 'teamName' in inputReq:
            
            yearOfSeason = inputReq['season']

            selectedTeam = nflTeam.objects.get(abbreviation = inputReq['teamName'])

            selectedTeamEspnId = selectedTeam.espnId
            print("Team EspnId: " + str(selectedTeamEspnId))

            teamHomeGames = nflMatch.objects.filter(homeTeam = selectedTeam).filter(yearOfSeason = yearOfSeason).filter(completed = True)
            teamAwayGames = nflMatch.objects.filter(awayTeam = selectedTeam).filter(yearOfSeason = yearOfSeason).filter(completed = True)

            allTeamGames = nflMatch.objects.filter(homeTeam = selectedTeam).filter(yearOfSeason = yearOfSeason).filter(completed = True) | nflMatch.objects.filter(awayTeam = selectedTeam).filter(yearOfSeason = yearOfSeason).filter(completed = True)

            allTeamGames = allTeamGames.order_by('datePlayed')

            listOfPerformances = []

            # print (str(len(allTeamGames)))
            
            for game in allTeamGames:
                try:
                    performance = teamMatchPerformance.objects.get(matchEspnId = game.espnId, teamEspnId = selectedTeamEspnId)
                    
                    
                    listOfPerformances.append(performance)
                except Exception as e:
                    print(e)

            listOfFieldNames = []

            for f in teamMatchPerformance._meta.get_fields():
                if f.name in ['id', 'matchEspnId', "nflMatch", 'team', 'teamEspnId', 'opponent', 'yearOfSeason', 'atHome']:
                    pass
                else:
                    listOfFieldNames.append(f.name)

            return render(request, 'nfl/teamDetailedStats.html', {"teams": nflTeam.objects.all().order_by('abbreviation'), "season": yearOfSeason, "teamName": inputReq['teamName'], "teamEspnId": selectedTeamEspnId, "teamPerf": listOfPerformances, "fieldNames": listOfFieldNames, 'years': yearsOnPage})

            
        else:
            return render(request, 'nfl/teamDetailedStats.html', {"teams": nflTeam.objects.all().order_by('abbreviation'), 'years': yearsOnPage})
    else:
        return render(request, 'nfl/teamDetailedStats.html', {"teams": nflTeam.objects.all().order_by('abbreviation'), 'years': yearsOnPage})

def viewIndividualStat(request):
    pass

def testPage(request):
    inputReq = request.GET

    if(request.method == 'GET'):
        if 'week' in inputReq:
            yearOfSeason = inputReq['season']
            wkOfSeason = inputReq['week']

            selectedGames = nflMatch.objects.filter(yearOfSeason = yearOfSeason).order_by('weekOfSeason')

            return render(request, 'nfl/testPage.html', {"games": selectedGames})
        else:
            return render(request, 'nfl/testPage.html')

def playerSignificance(request):
    if(request.method == 'GET'):
      
        playerId = request.GET.get('playerId')
        playerStar = request.GET.get('isStar')
        playerContrib = request.GET.get('bigImpact')
        playerStarter = request.GET.get('starter')

        playerObj = player.objects.get(espnId = int(playerId))
        playerObj.starPlayer = True if playerStar == 'true' else False
        playerObj.currentlyHavingBigImpact = True if playerContrib == 'true' else False
        playerObj.isStarter = True if playerStarter == 'true' else False
        playerObj.save()

        return JsonResponse({}, status="200")

# def getPlays(request):
#     nflTeams = nflTeam.objects.all().order_by('abbreviation')

#     yearsOnPage = yearsOnPage_Helper()

#     weeksOnPage = weeksOnPage_Helper()
#     weeksOnPage.insert(0, ["100", "ALL"])

#     pageDictionary = {}
#     pageDictionary['weeks'] = weeksOnPage
#     pageDictionary['years'] = yearsOnPage
#     pageDictionary['teams'] = nflTeams

#     if(request.method == 'GET'):
#         if 'teamName' in request.GET and 'season' in request.GET:
#                 inputReq = request.GET
#                 yearOfSeason = inputReq['season'].strip()
#                 selectedTeam = nflTeam.objects.get(abbreviation = inputReq['teamName'])
#                 teamId = selectedTeam.espnId
                
#                 if yearOfSeason == '2025':
#                     url = ('https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/' + str(teamId) + '/roster')
#                     response = requests.get(url)
#                     responseData = response.json()
#                     rosterData = responseData['athletes']

#                     for subsection in rosterData:
#                         players.createPlayerAthletesFromTeamRoster(subsection, teamId)


#                     playersLoaded = player.objects.filter(team = selectedTeam).order_by('sideOfBall').order_by('playerPosition')

#                     playerTenuresLoaded = []
#                     for pl in playersLoaded:
#                         individualPlayerTenures = playerTeamTenure.objects.filter(player = pl)
#                         for ipt in individualPlayerTenures:
#                             playerTenuresLoaded.append(ipt)
                    
#                     # print(playerTenuresLoaded)

#                     return render(request, 'nfl/players.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage, 'selTeam': selectedTeam, 'players': playersLoaded, 'season': inputReq['season'], 'tenures': playerTenuresLoaded})

#         elif 'week' in request.GET:
#             inputReq = request.GET
#             yearOfSeason = inputReq['season'].strip()
#             weekOfSeason = int(inputReq['week'].strip())
            
                
            
#             # if 'team' in inputReq:

#             #     selectedTeam = nflTeam.objects.get(abbreviation = inputReq['team'])
#             #     teamId = selectedTeam.espnId
#             #     selectedMatchQuerySet = nflMatch.objects.filter(weekOfSeason = weekOfSeason, yearOfSeason = yearOfSeason, homeTeamEspnId = teamId)
#             #     if(len(selectedMatchQuerySet) == 0):
#             #         selectedMatchQuerySet = nflMatch.objects.filter(weekOfSeason = weekOfSeason, yearOfSeason = yearOfSeason, awayTeamEspnId = teamId)
#             #         if(len(selectedMatchQuerySet) == 0):
#             #             responseMessage = "Week " + str(weekOfSeason) + " was the Bye week for " + selectedTeam.abbreviation
#             #             return render(request, 'nfl/players.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage, 'responseMessage': responseMessage})
                
#             #     selectedMatch = selectedMatchQuerySet[0]
#             #     matchId = selectedMatch.espnId
                
#             #     gameRosterUrl='http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/'+str(matchId)+'/competitions/'+str(matchId)+'/competitors/'+str(teamId)+'/roster'
#             #     gameRosterResponse = requests.get(gameRosterUrl)
#             #     print(gameRosterUrl)
#             #     gameRosterData = gameRosterResponse.json()

#             #     athleteAvailability = crudLogic.processGameRosterForAvailability(gameRosterData, selectedTeam, yearOfSeason, weekOfSeason)

#             #     # print(weekOfSeason)
#             #     return render(request, 'nfl/plays.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage, 'athleteAvail': athleteAvailability, 'sel_Team': inputReq['team'], 'sel_Year': yearOfSeason, 'sel_Week': weekOfSeason})
            
#             matches = nflMatch.objects.filter(weekOfSeason = weekOfSeason, yearOfSeason = yearOfSeason)
#             resultArray = []
#             for s_match in matches:
#                 drives = driveOfPlay.objects.filter(nflMatch = s_match)
#                 drives = sorted(drives, key=lambda x: x.sequenceNumber)
#                 result_drives_array = []
#                 for s_drive in drives:
#                     plays = playByPlay.objects.filter(driveOfPlay = s_drive)
#                     result_plays_array = []
#                     for play in plays:
#                         result_plays_array.append(play)
#                     result_plays_array = sorted(result_plays_array, key=lambda x: x.sequenceNumber)
#                     result_drives_array.append([s_drive, result_plays_array])
#                 resultArray.append([s_match, result_drives_array])
            
#             return render(request, 'nfl/plays.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage, 'resultArray': resultArray, 'weekNum': weekOfSeason})
#         else:
            
#             return render(request, 'nfl/plays.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage})    

# CLAUDE CODE
def getPlays(request):
    nflTeams = nflTeam.objects.all().order_by('abbreviation')
    yearsOnPage = yearsOnPage_Helper()
    weeksOnPage = weeksOnPage_Helper()
    weeksOnPage.insert(0, ["100", "ALL"])

    pageDictionary = {}
    pageDictionary['weeks'] = weeksOnPage
    pageDictionary['years'] = yearsOnPage
    pageDictionary['teams'] = nflTeams

    if request.method == 'GET':
        if 'week' in request.GET and 'team' in request.GET:
            inputReq = request.GET
            yearOfSeason = inputReq['season'].strip()
            weekOfSeason = int(inputReq['week'].strip())
            selectedTeamAbbr = inputReq['team'].strip()
            
            # Filter matches based on team selection
            if selectedTeamAbbr == "ALL":
                matches = nflMatch.objects.filter(
                    weekOfSeason=weekOfSeason, 
                    yearOfSeason=yearOfSeason
                )
                selectedTeam = None
            else:
                selectedTeam = nflTeam.objects.get(abbreviation=selectedTeamAbbr)
                teamId = selectedTeam.espnId
                
                # Get matches where the selected team is either home or away
                matches = nflMatch.objects.filter(
                    weekOfSeason=weekOfSeason,
                    yearOfSeason=yearOfSeason
                ).filter(
                    models.Q(homeTeamEspnId=teamId) | models.Q(awayTeamEspnId=teamId)
                )
            
            resultArray = []
            
            for s_match in matches:
                drives = driveOfPlay.objects.filter(nflMatch=s_match)
                
                # If a specific team is selected, filter drives to only show that team's offensive drives
                if selectedTeam:
                    drives = drives.filter(teamOnOffense=selectedTeam)
                
                drives = sorted(drives, key=lambda x: x.sequenceNumber)
                result_drives_array = []
                
                for s_drive in drives:
                    plays = playByPlay.objects.filter(driveOfPlay=s_drive)
                    result_plays_array = []
                    
                    for play in plays:
                        # Populate stat splits for this play if not already done
                        populatePlayStatSplits(play, s_match.espnId)
                        
                        # Get existing stat splits for display
                        play.passer_stats = passerStatSplit.objects.filter(play=play).first()
                        play.rusher_stats = rusherStatSplit.objects.filter(play=play).first()
                        play.receiver_stats = receiverStatSplit.objects.filter(play=play).first()
                        
                        result_plays_array.append(play)
                    
                    result_plays_array = sorted(result_plays_array, key=lambda x: x.sequenceNumber)
                    result_drives_array.append([s_drive, result_plays_array])
                
                resultArray.append([s_match, result_drives_array])
            
            pageDictionary['resultArray'] = resultArray
            pageDictionary['weekNum'] = weekOfSeason
            pageDictionary['selectedTeam'] = selectedTeamAbbr
            pageDictionary['selectedYear'] = yearOfSeason
            
            return render(request, 'nfl/plays.html', pageDictionary)
        else:
            return render(request, 'nfl/plays.html', pageDictionary)

def populatePlayStatSplits(play, match_espn_id):
    """
    Populate stat split models for a given play by fetching participant data from ESPN API
    """
    try:
        # Skip if already populated
        existing_splits = (
            passerStatSplit.objects.filter(play=play).exists() or
            rusherStatSplit.objects.filter(play=play).exists() or
            receiverStatSplit.objects.filter(play=play).exists()
        )
        
        if existing_splits:
            return
        
        # Only process relevant play types
        if play.playType not in [1, 2, 3, 4]:  # RUSH, COMPLETED PASS, INCOMPLETE PASS, SACK
            return
        
        # Fetch play participant data from ESPN API
        if play.espnId:
            play_url = f'http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/{match_espn_id}/competitions/{match_espn_id}/plays/{play.espnId}?lang=en&region=us'
            
            try:
                response = requests.get(play_url)
                if response.status_code == 200:
                    play_data = response.json()
                    
                    # Process participants if available
                    if 'participants' in play_data:
                        processPlayParticipants(play, play_data['participants'])
                    else:
                        # Fallback to parsing play description
                        if play.playDescription:
                            parsePlayDescription(play)
                        
            except Exception as e:
                print(f"Error fetching play data for play {play.espnId}: {e}")
                # Fallback to parsing play description
                if play.playDescription:
                    parsePlayDescription(play)
        
        # If no ESPN ID, try to parse from description
        elif play.playDescription:
            parsePlayDescription(play)
            
    except Exception as e:
        print(f"Error populating stat splits for play {play.id}: {e}")

def processPlayParticipants(play, participants_data):
    """
    Process participant data from ESPN API and create stat split records
    """
    for participant in participants_data:
        try:
            # Extract athlete ID from the $ref URL
            athlete_ref = participant.get('athlete', {}).get('$ref', '')
            athlete_id = extractAthleteIdFromRef(athlete_ref)
            
            if not athlete_id:
                continue
            
            # Get or create player
            try:
                player_obj = player.objects.get(espnId=athlete_id)
            except player.DoesNotExist:
                # Try to fetch and create player from athlete endpoint
                player_obj = createPlayerFromAthleteRef(athlete_ref, play.teamOnOffense)
                if not player_obj:
                    continue
            
            # Get player tenure
            tenure = playerTeamTenure.objects.filter(
                player=player_obj,
                team=play.teamOnOffense
            ).first()
            
            # Get participant type and stats
            participant_type = participant.get('type', '').lower()
            stats_array = participant.get('stats', [])
            
            # Convert stats array to dict for easier access
            stats_dict = {}
            for stat in stats_array:
                stats_dict[stat['name']] = stat['value']
            
            # Create appropriate stat split based on participant type
            if participant_type == 'passer':
                createPasserStatSplit(play, player_obj, tenure, stats_dict)
                
            elif participant_type == 'rusher':
                createRusherStatSplit(play, player_obj, tenure, stats_dict)
                
            elif participant_type == 'receiver':
                createReceiverStatSplit(play, player_obj, tenure, stats_dict)
            
            # Note: We're not creating defender splits for tacklers, but you could add that if needed
                
        except Exception as e:
            print(f"Error processing participant for play {play.id}: {e}")

def extractAthleteIdFromRef(ref_url):
    """
    Extract athlete ID from ESPN API reference URL
    Example: http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/2025/athletes/3045147?lang=en&region=us
    Returns: 3045147
    """
    try:
        if '/athletes/' in ref_url:
            # Split by '/athletes/' and take what comes after
            parts = ref_url.split('/athletes/')
            if len(parts) > 1:
                # Extract just the ID number (before the '?')
                athlete_id = parts[1].split('?')[0]
                return int(athlete_id)
    except Exception as e:
        print(f"Error extracting athlete ID from {ref_url}: {e}")
    return None

def createPlayerFromAthleteRef(athlete_ref, team):
    """
    Fetch athlete data from ESPN API and create player record
    """
    try:
        response = requests.get(athlete_ref)
        if response.status_code == 200:
            athlete_data = response.json()
            
            espn_id = athlete_data.get('id')
            name = athlete_data.get('displayName', athlete_data.get('fullName', 'Unknown'))
            
            if not espn_id:
                return None
            
            # Get position information
            position_info = athlete_data.get('position', {})
            position_abbr = position_info.get('abbreviation', '')
            
            position_map = {
                'QB': 1, 'WR': 2, 'TE': 3, 'RB': 4, 'FB': 5,
                'C': 6, 'G': 6, 'T': 6, 'OL': 6,  # O-Line
                'DE': 7, 'DT': 7, 'NT': 7, 'DL': 7,  # D-Line
                'LB': 8, 'ILB': 8, 'OLB': 8,
                'CB': 9, 'DB': 9,
                'S': 10, 'SS': 10, 'FS': 10,
                'K': 11, 'P': 12
            }
            
            position = position_map.get(position_abbr, 13)  # Default to "Other"
            
            # Determine side of ball
            if position in [1, 2, 3, 4, 5, 6]:
                side_of_ball = 1  # Offense
            elif position in [7, 8, 9, 10]:
                side_of_ball = 2  # Defense
            elif position in [11, 12]:
                side_of_ball = 3  # Special Teams
            else:
                side_of_ball = 4  # Undefined
            
            # Get physical attributes
            height = athlete_data.get('height', 72)  # Default 6 feet
            weight = athlete_data.get('weight', 200)  # Default 200 lbs
            
            player_obj = player.objects.create(
                espnId=espn_id,
                name=name,
                team=team,
                playerPosition=position,
                sideOfBall=side_of_ball,
                playerHeightInches=height,
                playerWeightPounds=weight,
                firstSeason=datetime.datetime.now().year
            )
            
            # Create tenure
            playerTeamTenure.objects.create(
                player=player_obj,
                team=team,
                startDate=datetime.datetime.now()
            )
            
            return player_obj
            
    except Exception as e:
        print(f"Error creating player from athlete ref {athlete_ref}: {e}")
    return None

def createPasserStatSplit(play, player_obj, tenure, stats_dict):
    """
    Create passer stat split record
    """
    try:
        # Check if this is actually a passing play
        if play.playType not in [2, 3, 4]:  # COMPLETED PASS, INCOMPLETE PASS, SACK
            return None
            
        passer_split = passerStatSplit.objects.create(
            play=play,
            player=player_obj,
            currentTenure=tenure,
            playerRole=1,  # passer
            playerPosition=1,  # passer position
            passingYards=stats_dict.get('passingYards', play.yardsOnPlay if play.playType == 2 else 0),
            interception=(play.playType == 15),  # INTERCEPTION
            fumble=(play.playType in [21, 22]),  # QB FUMBLE types
            fumbleLost=(play.playType == 21),  # QB FUMBLE - DEFENSIVE RECOVERY
            passingTdScored=(play.scoringPlay and play.playType == 2 and play.offenseScored)
        )
        return passer_split
    except Exception as e:
        print(f"Error creating passer stat split: {e}")
        return None

def createRusherStatSplit(play, player_obj, tenure, stats_dict):
    """
    Create rusher stat split record
    """
    try:
        if play.playType != 1:  # Only for RUSH plays
            return None
            
        rusher_split = rusherStatSplit.objects.create(
            play=play,
            player=player_obj,
            currentTenure=tenure,
            playerRole=2,  # rusher
            playerPosition=2,  # rusher position
            rushingYards=stats_dict.get('rushingYards', play.yardsOnPlay),
            fumble=(play.playType in [17, 18, 19, 20]),  # Various fumble types
            fumbleLost=(play.playType in [19, 20]),  # Defensive recovery fumbles
            rushingTdScored=(play.scoringPlay and play.playType == 1 and play.offenseScored)
        )
        return rusher_split
    except Exception as e:
        print(f"Error creating rusher stat split: {e}")
        return None

def createReceiverStatSplit(play, player_obj, tenure, stats_dict):
    """
    Create receiver stat split record
    """
    try:
        if play.playType != 2:  # Only for COMPLETED PASS plays
            return None
            
        receiver_split = receiverStatSplit.objects.create(
            play=play,
            player=player_obj,
            currentTenure=tenure,
            playerRole=3,  # receiver
            playerPosition=3,  # receiver position
            receivingYards=stats_dict.get('receivingYards', play.yardsOnPlay),
            yardsAfterCatch=stats_dict.get('yardsAfterCatch', 0),
            fumble=(play.playType in [17, 18, 19, 20]),  # Various fumble types
            fumbleLost=(play.playType in [19, 20]),  # Defensive recovery fumbles
            receivingTdScored=(play.scoringPlay and play.playType == 2 and play.offenseScored)
        )
        return receiver_split
    except Exception as e:
        print(f"Error creating receiver stat split: {e}")
        return None

def parsePlayDescription(play):
    """
    Fallback method to parse play description and extract player names
    """
    import re
    
    if not play.playDescription:
        return
    
    description = play.playDescription
    team = play.teamOnOffense
    
    try:
        if play.playType in [2, 3]:  # COMPLETED PASS, INCOMPLETE PASS
            # Pattern: "K.Murray pass ... to M.Harrison"
            pass_pattern = r'([A-Z]\.\w+)\s+pass.*?to\s+([A-Z]\.\w+)'
            match = re.search(pass_pattern, description)
            
            if match:
                passer_name = match.group(1).strip()
                receiver_name = match.group(2).strip()
                
                # Try to find players by partial name match
                passer = player.objects.filter(
                    name__icontains=passer_name.split('.')[-1],  # Last name
                    team=team,
                    playerPosition=1  # QB
                ).first()
                
                if passer:
                    tenure = playerTeamTenure.objects.filter(player=passer, team=team).first()
                    passerStatSplit.objects.create(
                        play=play,
                        player=passer,
                        currentTenure=tenure,
                        playerRole=1,
                        playerPosition=1,
                        passingYards=play.yardsOnPlay if play.playType == 2 else 0,
                        interception=False,
                        fumble=False,
                        fumbleLost=False,
                        passingTdScored=(play.scoringPlay and play.offenseScored)
                    )
                
                if play.playType == 2:  # Only for completed passes
                    receiver = player.objects.filter(
                        name__icontains=receiver_name.split('.')[-1],  # Last name
                        team=team,
                        playerPosition__in=[2, 3, 4]  # WR, TE, RB
                    ).first()
                    
                    if receiver:
                        tenure = playerTeamTenure.objects.filter(player=receiver, team=team).first()
                        receiverStatSplit.objects.create(
                            play=play,
                            player=receiver,
                            currentTenure=tenure,
                            playerRole=3,
                            playerPosition=3,
                            receivingYards=play.yardsOnPlay,
                            yardsAfterCatch=0,
                            fumble=False,
                            fumbleLost=False,
                            receivingTdScored=(play.scoringPlay and play.offenseScored)
                        )
        
        elif play.playType == 1:  # RUSH
            # Pattern: "J.Conner right tackle" or "J.Conner up the middle"
            rush_pattern = r'([A-Z]\.\w+)\s+(?:left|right|up)'
            match = re.search(rush_pattern, description)
            
            if match:
                rusher_name = match.group(1).strip()
                rusher = player.objects.filter(
                    name__icontains=rusher_name.split('.')[-1],  # Last name
                    team=team,
                    playerPosition__in=[4, 5]  # RB, FB
                ).first()
                
                if rusher:
                    tenure = playerTeamTenure.objects.filter(player=rusher, team=team).first()
                    rusherStatSplit.objects.create(
                        play=play,
                        player=rusher,
                        currentTenure=tenure,
                        playerRole=2,
                        playerPosition=2,
                        rushingYards=play.yardsOnPlay,
                        fumble=False,
                        fumbleLost=False,
                        rushingTdScored=(play.scoringPlay and play.offenseScored)
                    )
                    
    except Exception as e:
        print(f"Error parsing play description for play {play.id}: {e}")

# END CLAUD CODE


def getTouchdowns(request):
    nflTeams = nflTeam.objects.all().order_by('abbreviation')
    yearsOnPage = yearsOnPage_Helper()
    
    pageDictionary = {}
    pageDictionary['years'] = yearsOnPage
    pageDictionary['teams'] = nflTeams
    
    if request.method == 'GET':
        if 'teamName' in request.GET and 'season' in request.GET:
            inputReq = request.GET
            yearOfSeason = inputReq['season'].strip()
            selectedTeam = nflTeam.objects.get(abbreviation=inputReq['teamName'])
            teamId = selectedTeam.espnId
            
            # Get all matches for this team in this season
            homeMatches = nflMatch.objects.filter(
                homeTeamEspnId=teamId,
                yearOfSeason=yearOfSeason,
                completed=True
            )
            awayMatches = nflMatch.objects.filter(
                awayTeamEspnId=teamId,
                yearOfSeason=yearOfSeason,
                completed=True
            )
            allMatches = homeMatches | awayMatches
            allMatches = allMatches.order_by('weekOfSeason')
            
            # Debug: Check if we have matches
            print(f"Found {allMatches.count()} matches for {selectedTeam.abbreviation} in {yearOfSeason}")
            
            touchdownData = []
            debugInfo = {
                'total_matches': allMatches.count(),
                'total_plays_checked': 0,
                'scoring_plays_found': 0,
                'touchdown_plays_found': 0
            }
            
            for match in allMatches:
                # Determine if team was home or away
                isHome = match.homeTeamEspnId == teamId
                opponent = nflTeam.objects.get(
                    espnId=match.awayTeamEspnId if isHome else match.homeTeamEspnId
                )
                
                # First, let's check all plays for this team (for debugging)
                all_team_plays = playByPlay.objects.filter(
                    nflMatch=match,
                    teamOnOffense=selectedTeam
                )
                debugInfo['total_plays_checked'] += all_team_plays.count()
                
                # Check for scoring plays
                scoring_plays = all_team_plays.filter(scoringPlay=True)
                debugInfo['scoring_plays_found'] += scoring_plays.count()
                
                print(f"Match {match.espnId}: {all_team_plays.count()} plays, {scoring_plays.count()} scoring plays")
                
                # Method 1: Try using scoringPlay and offenseScored flags
                tdPlays = playByPlay.objects.filter(
                    nflMatch=match,
                    teamOnOffense=selectedTeam,
                    scoringPlay=True,
                    offenseScored=True,
                    pointsScored__gte=6  # Touchdowns are worth at least 6 points
                ).exclude(playType__in=[5, 6, 7, 8, 9, 10, 11, 12])  # Exclude PAT and 2PT conversions
                
                # Method 2: If no plays found with flags, try alternative approach
                if not tdPlays.exists():
                    # Look for plays with specific TD play types
                    # Based on the playTypes in your model, touchdown plays would be:
                    # Where description contains "touchdown" or specific scoring scenarios
                    tdPlays = playByPlay.objects.filter(
                        nflMatch=match,
                        teamOnOffense=selectedTeam
                    ).filter(
                        models.Q(playDescription__icontains='touchdown') |
                        models.Q(playDescription__icontains=' TD') |
                        models.Q(playType=1, scoringPlay=True) |  # Rushing TD
                        models.Q(playType=2, scoringPlay=True)    # Passing TD
                    ).exclude(playType__in=[5, 6, 7, 8, 9, 10, 11, 12])
                
                debugInfo['touchdown_plays_found'] += tdPlays.count()
                
                for play in tdPlays:
                    tdInfo = {
                        'week': match.weekOfSeason,
                        'date': match.datePlayed,
                        'opponent': opponent.abbreviation,
                        'homeAway': 'Home' if isHome else 'Away',
                        'quarter': play.quarter,
                        'time': play.displayClockTime,
                        'playType': play.get_playType_display(),
                        'description': play.playDescription[:200] if play.playDescription else 'N/A',
                        'yardsOnPlay': play.yardsOnPlay,
                        'pointsScored': play.pointsScored,
                        'scorer': None,
                        'passer': None,
                        'playId': play.id,  # For debugging
                        'playEspnId': play.espnId  # For debugging
                    }
                    
                    # Try to identify the scorer from the play description if no stat splits
                    if play.playDescription:
                        tdInfo['scorer'] = extractPlayerFromDescription(play.playDescription, 'touchdown')
                    
                    # Try to get scorer from stat splits
                    try:
                        # Check for rushing TD
                        rusher = rusherStatSplit.objects.filter(
                            play=play,
                            rushingTdScored=True
                        ).first()
                        if rusher:
                            tdInfo['scorer'] = rusher.player.name
                            tdInfo['scorerPosition'] = rusher.player.get_playerPosition_display()
                        
                        # Check for receiving TD
                        receiver = receiverStatSplit.objects.filter(
                            play=play,
                            receivingTdScored=True
                        ).first()
                        if receiver:
                            tdInfo['scorer'] = receiver.player.name
                            tdInfo['scorerPosition'] = receiver.player.get_playerPosition_display()
                            
                            # Get the passer for receiving TDs
                            passer = passerStatSplit.objects.filter(
                                play=play,
                                passingTdScored=True
                            ).first()
                            if passer:
                                tdInfo['passer'] = passer.player.name
                    except Exception as e:
                        print(f"Error getting player info for play {play.id}: {e}")
                    
                    touchdownData.append(tdInfo)
            
            # Alternative: If no touchdown plays found in playByPlay, get from match data
            if not touchdownData:
                print("No touchdown plays found in playByPlay table. Trying match-level data...")
                
                # Get touchdowns from match statistics
                for match in allMatches:
                    isHome = match.homeTeamEspnId == teamId
                    opponent = nflTeam.objects.get(
                        espnId=match.awayTeamEspnId if isHome else match.homeTeamEspnId
                    )
                    
                    if isHome:
                        rushing_tds = match.homeTeamRushingTDScored or 0
                        receiving_tds = match.homeTeamReceivingTDScored or 0
                        total_points = match.homeTeamPoints or 0
                    else:
                        rushing_tds = match.awayTeamRushingTDScored or 0
                        receiving_tds = match.awayTeamReceivingTDScored or 0
                        total_points = match.awayTeamPoints or 0
                    
                    # Add summary TD data if available
                    if rushing_tds > 0 or receiving_tds > 0:
                        for i in range(rushing_tds):
                            touchdownData.append({
                                'week': match.weekOfSeason,
                                'date': match.datePlayed,
                                'opponent': opponent.abbreviation,
                                'homeAway': 'Home' if isHome else 'Away',
                                'quarter': 'N/A',
                                'time': 'N/A',
                                'playType': 'RUSH',
                                'description': 'Rushing TD (details not available)',
                                'yardsOnPlay': None,
                                'pointsScored': 6,
                                'scorer': 'Unknown',
                                'passer': None
                            })
                        
                        for i in range(receiving_tds):
                            touchdownData.append({
                                'week': match.weekOfSeason,
                                'date': match.datePlayed,
                                'opponent': opponent.abbreviation,
                                'homeAway': 'Home' if isHome else 'Away',
                                'quarter': 'N/A',
                                'time': 'N/A',
                                'playType': 'COMPLETED PASS',
                                'description': 'Receiving TD (details not available)',
                                'yardsOnPlay': None,
                                'pointsScored': 6,
                                'scorer': 'Unknown',
                                'passer': 'Unknown'
                            })
            
            # Calculate season totals
            totalTouchdowns = len(touchdownData)
            
            # Group touchdowns by player (skip if all unknowns)
            playerTouchdowns = {}
            for td in touchdownData:
                if td['scorer'] and td['scorer'] != 'Unknown':
                    if td['scorer'] not in playerTouchdowns:
                        playerTouchdowns[td['scorer']] = {
                            'rushing': 0,
                            'receiving': 0,
                            'total': 0
                        }
                    if 'RUSH' in td['playType']:
                        playerTouchdowns[td['scorer']]['rushing'] += 1
                    elif 'PASS' in td['playType']:
                        playerTouchdowns[td['scorer']]['receiving'] += 1
                    playerTouchdowns[td['scorer']]['total'] += 1
            
            # Sort players by total touchdowns
            sortedPlayers = sorted(
                playerTouchdowns.items(), 
                key=lambda x: x[1]['total'], 
                reverse=True
            )
            
            pageDictionary['touchdowns'] = touchdownData
            pageDictionary['selectedTeam'] = selectedTeam
            pageDictionary['yearOfSeason'] = yearOfSeason
            pageDictionary['totalTouchdowns'] = totalTouchdowns
            pageDictionary['playerTouchdowns'] = sortedPlayers
            pageDictionary['debugInfo'] = debugInfo  # Add debug info to context
            
            # Print debug info
            print(f"Debug Info: {debugInfo}")
            print(f"Total touchdowns found: {totalTouchdowns}")
            
            return render(request, 'nfl/touchdowns.html', pageDictionary)
    
    return render(request, 'nfl/touchdowns.html', pageDictionary)

def extractPlayerFromDescription(description, keyword='touchdown'):
    """
    Extract player name from play description
    """
    import re
    
    # Common patterns for touchdowns
    patterns = [
        r'([A-Z]\.\w+)\s+\d+\s+[Yy]d\s+[Rr]un',  # J.Conner 1 Yd Run
        r'([A-Z]\.\w+)\s+\d+\s+[Yy]ard',  # J.Conner 1 yard
        r'([A-Z]\.\w+)\s+rush',  # J.Conner rush
        r'pass.*?to\s+([A-Z]\.\w+)',  # pass to M.Harrison
        r'([A-Z]\.\w+)\s+pass',  # K.Murray pass
    ]
    
    for pattern in patterns:
        match = re.search(pattern, description)
        if match:
            return match.group(1)
    
    return None

def weeksOnPage_Helper():
    weeksOnPage = []
    for w in range(1,19):
        weeksOnPage.append([w, w])
    weeksOnPage.append([19, "Wildcard Weekend"])
    weeksOnPage.append([20, "Divisional Round"])
    weeksOnPage.append([21, "Conference Championship"])
    weeksOnPage.append([22, "Super Bowl"])

    return weeksOnPage

def yearsOnPage_Helper():
    yearsOnPage = []
    for y in range(2025, 2016, -1):
        yearsOnPage.append(y)
    
    return yearsOnPage        
    



