from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.core import serializers
import json
from nfl_db.models import nflTeam, nflMatch, teamMatchPerformance, driveOfPlay, player, playerTeamTenure, playerWeekStatus, playByPlay
from django.db import models
from nfl_db import businessLogic, crudLogic
import datetime, time, requests, traceback

# Create your views here.

def index(request):
    return render (request, 'nfl/base.html')

def getData(request):
    weeksOnPage = []
    for w in range(1,19):
        weeksOnPage.append([w, w])
    weeksOnPage.append([19, "Wildcard Weekend"])
    weeksOnPage.append([20, "Divisional Round"])
    weeksOnPage.append([21, "Conference Championship"])
    weeksOnPage.append([22, "Super Bowl"])

    yearsOnPage = []
    for y in range(2023, 2012, -1):
        yearsOnPage.append(y)
    
    pageDictionary = {}
    pageDictionary['weeks'] = weeksOnPage
    pageDictionary['years'] = yearsOnPage


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

            i = startWeek

            pageDictionary['sel_year'] = yearOfSeason
            pageDictionary['start_week'] = startWeek
            pageDictionary['end_week'] = endWeek

            exceptionCollection = []

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
                    #print(link['$ref'])
                    gameDataResponse = requests.get(link['$ref'])
                    gameData=gameDataResponse.json()

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
                    
                    if datetime.datetime.now()<dateOfGame or gameCompleted==False:
                        crudLogic.createOrUpdateScheduledNflMatch(existingMatch, gameData, oddsData, str(weekOfSeason), str(yearOfSeason))

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

                        playByPlayOfGame = crudLogic.playByPlayData(playsData)
                        
                        pagesOfPlaysData = playsData['pageCount']
                        if pagesOfPlaysData > 1:
                            #print("Multiple pages of Data in game")
                            for page in range(2, pagesOfPlaysData+1):
                                multiPagePlaysDataUrl = playsDataUrl+"&page="+str(page)
                                pagePlaysDataResponse = requests.get(multiPagePlaysDataUrl)
                                pagePlaysData = pagePlaysDataResponse.json()
                                playByPlayOfGame.addJSON(pagePlaysData)
                        
                        try:
                            matchData = crudLogic.createOrUpdateFinishedNflMatch(existingMatch, gameData, gameCompleted, gameOvertime, homeTeamScore, homeTeamStats, awayTeamScore, awayTeamStats, oddsData, playsData, drivesData, str(weekOfSeason), str(yearOfSeason))
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

                        # try:
                        #     existingHomeTeamPerf = teamMatchPerformance.objects.get(matchEspnId = matchData.espnId, teamEspnId = matchData.homeTeamEspnId)
                        # except Exception as e:
                        #     print()
                        #     print(e)
                        #     print("matchEspnId = " + str(matchEspnId))
                        #     print("homeTeamEspnId = " + str(homeTeamEspnId))
                        #     print("matchData.espnId = " + str(matchData.espnId))
                        #     print("matchData.homeTeamEspnId = " + str(matchData.homeTeamEspnId))
                        #     print()

                        
                        
                        
                        try:
                            crudLogic.createOrUpdateTeamMatchPerformance(existingHomeTeamPerf, homeTeamScore, homeTeamStats, matchData.espnId, matchData.homeTeamEspnId, matchData.awayTeamEspnId, awayTeamStats, playsData, playByPlayOfGame, drivesData, seasonWeek=str(weekOfSeason), seasonYear=str(yearOfSeason))                        
                        except Exception as e: 
                            print("Problem with creating home team Match performance")
                            game_exception = []
                            game_exception.append("There was an exception when pulling game " + str(matchEspnId) + " from week " + str(weekOfSeason) + " of year " + str(yearOfSeason) + ".")
                            game_exception.append(e.args[0][0][0])
                            game_exception.append(e.args[0][0][1])
                            game_exception.append(str(matchEspnId)+str(homeTeamEspnId))
                            exceptionCollection.append(game_exception)

                        try:
                            crudLogic.createOrUpdateTeamMatchPerformance(existingAwayTeamPerf, awayTeamScore, awayTeamStats, matchData.espnId, matchData.awayTeamEspnId, matchData.homeTeamEspnId, homeTeamStats, playsData, playByPlayOfGame, drivesData, seasonWeek=str(weekOfSeason), seasonYear=str(yearOfSeason))    

                        except Exception as e:
                            print("Problem with creating away team Match performance")
                            game_exception = []
                            game_exception.append("There was an exception when pulling game " + str(matchEspnId) + " from week " + str(weekOfSeason) + " of year " + str(yearOfSeason) + ".")
                            game_exception.append(e.args[0][0][0])
                            game_exception.append(e.args[0][0][1])
                            game_exception.append(str(matchEspnId)+str(awayTeamEspnId))
                            exceptionCollection.append(game_exception)

                        print("Completed.")    
                            
                            
                
                print("Week ", str(i), " loaded.")
                i += 1
            if startWeek <= endWeek:
                message = "Games loaded for Week " + str(startWeek) + " of " + str(yearOfSeason) + " season."
            else:
                message = "Games loaded for Week " + str(startWeek) + " through Week " + str(endWeek) + " of " + str(yearOfSeason) + " season."
            pageDictionary['message'] = message
           
            if len(exceptionCollection) > 0:
                pageDictionary['exceptions'] = exceptionCollection
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

    yearsOnPage = []
    for y in range(2023, 2017, -1):
        yearsOnPage.append(y)

    weeksOnPage = []
    weeksOnPage.append(["100", "ALL"])
    for w in range(1,19):
        weeksOnPage.append([w, w])
    # weeksOnPage.append([19, "Wildcard Weekend"])
    # weeksOnPage.append([20, "Divisional Round"])
    # weeksOnPage.append([21, "Conference Championship"])
    # weeksOnPage.append([22, "Super Bowl"])

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
                
                if yearOfSeason == '2023':
                    url = ('https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/' + str(teamId) + '/roster')
                    response = requests.get(url)
                    responseData = response.json()
                    rosterData = responseData['athletes']

                    for subsection in rosterData:
                        crudLogic.createPlayerAthletesFromTeamRoster(subsection, teamId)


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

            playersLoaded = sorted(player.objects.filter(playerPosition = selectedPosition), key = lambda x: x.team.abbreviation)

            return render(request, 'nfl/players.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage, 'allPlayers': playersLoaded})

        elif 'week' in request.GET:
            inputReq = request.GET
            yearOfSeason = inputReq['season'].strip()
            weekOfSeason = int(inputReq['week'].strip())
            if weekOfSeason == 100:
                #print("We Get here")
                endRangeWeek = 19
                if int(yearOfSeason) == 2023:

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
    weeksOnPage = []
    for w in range(1,19):
        weeksOnPage.append([w, w])
    weeksOnPage.append([19, "Wildcard Weekend"])
    weeksOnPage.append([20, "Divisional Round"])
    weeksOnPage.append([21, "Conference Championship"])
    weeksOnPage.append([22, "Super Bowl"])

    yearsOnPage = []
    for y in range(2023, 2017, -1):
        yearsOnPage.append(y)
    
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
            return render(request, 'nfl/bettingModel.html')
        else:
            return render(request, 'nfl/modelSummary.html')

def loadModelYear(request):
    yearsOnPage = []
    for y in range(2022, 2017, -1):
        yearsOnPage.append(y)

    numResultsSelect = []
    numResultsSelect.append(20)
    for nr in range(2, 11):
        numResultsSelect.append(nr)
    
    

    topNumResults = 20

    modelsOnPage = []
    modelsOnPage.append(['v1', 'V1.0 (Avg Yds/Yds per Pt)'])
    modelsOnPage.append(['v1.5', 'V1.5 (V1 with Moving Avg.)'])
    modelsOnPage.append(['v2','V2.0 (Drives vs Drive Result)'])
    
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

    yearsOnPage = []
    for y in range(2023, 2017, -1):
        yearsOnPage.append(y)
    
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

def getPlays(request):
    nflTeams = nflTeam.objects.all().order_by('abbreviation')

    yearsOnPage = []
    for y in range(2023, 2017, -1):
        yearsOnPage.append(y)

    weeksOnPage = []
    weeksOnPage.append(["100", "ALL"])
    for w in range(1,19):
        weeksOnPage.append([w, w])
    # weeksOnPage.append([19, "Wildcard Weekend"])
    # weeksOnPage.append([20, "Divisional Round"])
    # weeksOnPage.append([21, "Conference Championship"])
    # weeksOnPage.append([22, "Super Bowl"])

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
                
                if yearOfSeason == '2023':
                    url = ('https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/' + str(teamId) + '/roster')
                    response = requests.get(url)
                    responseData = response.json()
                    rosterData = responseData['athletes']

                    for subsection in rosterData:
                        crudLogic.createPlayerAthletesFromTeamRoster(subsection, teamId)


                    playersLoaded = player.objects.filter(team = selectedTeam).order_by('sideOfBall').order_by('playerPosition')

                    playerTenuresLoaded = []
                    for pl in playersLoaded:
                        individualPlayerTenures = playerTeamTenure.objects.filter(player = pl)
                        for ipt in individualPlayerTenures:
                            playerTenuresLoaded.append(ipt)
                    
                    # print(playerTenuresLoaded)

                    return render(request, 'nfl/players.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage, 'selTeam': selectedTeam, 'players': playersLoaded, 'season': inputReq['season'], 'tenures': playerTenuresLoaded})

        elif 'week' in request.GET:
            inputReq = request.GET
            yearOfSeason = inputReq['season'].strip()
            weekOfSeason = int(inputReq['week'].strip())
            
                
            
            # if 'team' in inputReq:

            #     selectedTeam = nflTeam.objects.get(abbreviation = inputReq['team'])
            #     teamId = selectedTeam.espnId
            #     selectedMatchQuerySet = nflMatch.objects.filter(weekOfSeason = weekOfSeason, yearOfSeason = yearOfSeason, homeTeamEspnId = teamId)
            #     if(len(selectedMatchQuerySet) == 0):
            #         selectedMatchQuerySet = nflMatch.objects.filter(weekOfSeason = weekOfSeason, yearOfSeason = yearOfSeason, awayTeamEspnId = teamId)
            #         if(len(selectedMatchQuerySet) == 0):
            #             responseMessage = "Week " + str(weekOfSeason) + " was the Bye week for " + selectedTeam.abbreviation
            #             return render(request, 'nfl/players.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage, 'responseMessage': responseMessage})
                
            #     selectedMatch = selectedMatchQuerySet[0]
            #     matchId = selectedMatch.espnId
                
            #     gameRosterUrl='http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/'+str(matchId)+'/competitions/'+str(matchId)+'/competitors/'+str(teamId)+'/roster'
            #     gameRosterResponse = requests.get(gameRosterUrl)
            #     print(gameRosterUrl)
            #     gameRosterData = gameRosterResponse.json()

            #     athleteAvailability = crudLogic.processGameRosterForAvailability(gameRosterData, selectedTeam, yearOfSeason, weekOfSeason)

            #     # print(weekOfSeason)
            #     return render(request, 'nfl/plays.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage, 'athleteAvail': athleteAvailability, 'sel_Team': inputReq['team'], 'sel_Year': yearOfSeason, 'sel_Week': weekOfSeason})
            
            matches = nflMatch.objects.filter(weekOfSeason = weekOfSeason, yearOfSeason = yearOfSeason)
            resultArray = []
            for s_match in matches:
                drives = driveOfPlay.objects.filter(nflMatch = s_match)
                drives = sorted(drives, key=lambda x: x.sequenceNumber)
                result_drives_array = []
                for s_drive in drives:
                    plays = playByPlay.objects.filter(driveOfPlay = s_drive)
                    result_plays_array = []
                    for play in plays:
                        result_plays_array.append(play)
                    result_plays_array = sorted(result_plays_array, key=lambda x: x.sequenceNumber)
                    result_drives_array.append([s_drive, result_plays_array])
                resultArray.append([s_match, result_drives_array])
            
            return render(request, 'nfl/plays.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage, 'resultArray': resultArray, 'weekNum': weekOfSeason})
        else:
            
            return render(request, 'nfl/plays.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage})    
                
        
    



