from django.shortcuts import render
from django.http import HttpResponse
from django.core import serializers
import json
from nfl_db.models import nflTeam, nflMatch, teamMatchPerformance, driveOfPlay, player, playerTeamTenure
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
    for y in range(2023, 2015, -1):
        yearsOnPage.append(y)

    if request.method == 'GET':
        if 'season' in request.GET and 'week' in request.GET:     
            #print("Hit game stats endpoint")
            inputReq = request.GET
            yearOfSeason = inputReq['season'].strip()
            weekOfSeason = inputReq['week'].strip()
           
            print(inputReq['season'])
            print(inputReq['week'])
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

                gameStatusUrl = gameData['competitions'][0]['status']['$ref']
                gameStatusResponse = requests.get(gameStatusUrl)
                gameStatus = gameStatusResponse.json()


                gameCompleted = (gameStatus['type']['completed'] == True)
                gameOvertime = ("OT" in gameStatus['type']['detail']) 


                oddsUrl = gameData['competitions'][0]['odds']['$ref']
                oddsResponse = requests.get(oddsUrl)
                oddsData = oddsResponse.json()

                existingMatch = None

                responseMessage = ""

                try:
                    existingMatch = nflMatch.objects.get(espnId = matchEspnId)
                except:
                    pass
                
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

                        responseMessage = "Successfully pulled in Week " + str(weekOfSeason) + " for " + str(yearOfSeason)
                    except Exception as e: 
                        businessLogic.updateTeamPerformance(homeTeamScore, homeTeamStats, matchData.espnId, matchData.homeTeamEspnId, matchData.awayTeamEspnId, playsData, drivesData, weekOfSeason, yearOfSeason)
                        businessLogic.updateTeamPerformance(awayTeamScore, awayTeamStats, matchData.espnId, matchData.awayTeamEspnId, matchData.homeTeamEspnId, playsData, drivesData, weekOfSeason, yearOfSeason)

            return render (request, 'nfl/pullData.html', {'weeks':weeksOnPage, 'years': yearsOnPage, 'message': responseMessage})

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

            exceptionCollection = []

            while i <= endWeek:
                time.sleep(2)
                weekOfSeason = i
                


                url = ('https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/'+str(yearOfSeason)+'/types/2/weeks/'+str(weekOfSeason)+'/events')
                
                if(weekOfSeason >= 19):
                    playoffWeekOfSeason = weekOfSeason - 18
                    url = ('https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/'+str(yearOfSeason)+'/types/3/weeks/'+str(playoffWeekOfSeason)+'/events')
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
                            print("Multiple pages of Data in game")
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

                        try:
                            existingHomeTeamPerf = teamMatchPerformance.objects.get(matchEspnId = matchData.espnId, teamEspnId = matchData.homeTeamEspnId)
                            # print()
                            # print("Team performance found for combination of data")
                            # print("matchEspnId = " + str(matchEspnId))
                            # print("homeTeamEspnId = " + str(homeTeamEspnId))
                            # print("matchData.espnId = " + str(matchData.espnId))
                            # print("matchData.homeTeamEspnId = " + str(matchData.homeTeamEspnId))
                        
                        except Exception as e:
                            print()
                            print(e)
                            print("matchEspnId = " + str(matchEspnId))
                            print("homeTeamEspnId = " + str(homeTeamEspnId))
                            print("matchData.espnId = " + str(matchData.espnId))
                            print("matchData.homeTeamEspnId = " + str(matchData.homeTeamEspnId))
                            print()

                        
                        
                        
                        try:
                            crudLogic.createOrUpdateTeamMatchPerformance(existingHomeTeamPerf, homeTeamScore, homeTeamStats, matchData.espnId, matchData.homeTeamEspnId, matchData.awayTeamEspnId, playsData, playByPlayOfGame, drivesData, seasonWeek=str(weekOfSeason), seasonYear=str(yearOfSeason))                        
                        
                        except Exception as e: 
                            print("Problem with creating home team Match performance")
                            game_exception = []
                            game_exception.append("There was an exception when pulling game " + str(matchEspnId) + " from week " + str(weekOfSeason) + " of year " + str(yearOfSeason) + ".")
                            game_exception.append(e.args[0][0][0])
                            game_exception.append(e.args[0][0][1])
                            game_exception.append(str(matchEspnId)+str(homeTeamEspnId))
                            exceptionCollection.append(game_exception)

                        try:
                            crudLogic.createOrUpdateTeamMatchPerformance(existingAwayTeamPerf, awayTeamScore, awayTeamStats, matchData.espnId, matchData.awayTeamEspnId, matchData.homeTeamEspnId, playsData, playByPlayOfGame, drivesData, seasonWeek=str(weekOfSeason), seasonYear=str(yearOfSeason))    

                        except Exception as e:
                            print("Problem with creating away team Match performance")
                            game_exception = []
                            game_exception.append("There was an exception when pulling game " + str(matchEspnId) + " from week " + str(weekOfSeason) + " of year " + str(yearOfSeason) + ".")
                            game_exception.append(e.args[0][0][0])
                            game_exception.append(e.args[0][0][1])
                            game_exception.append(str(matchEspnId)+str(awayTeamEspnId))
                            exceptionCollection.append(game_exception)
                            
                            
                            
                
                print("Week ", str(i), " loaded.")
                i += 1
            if startWeek == endWeek:
                message = "Games loaded for Week " + str(startWeek) + " of " + str(yearOfSeason) + " season."
            else:
                message = "Games loaded for Week " + str(startWeek) + " through Week " + str(endWeek) + " of " + str(yearOfSeason) + " season."
            if len(exceptionCollection) > 0:
                print("There were exceptions.")
                return render (request, 'nfl/pullData.html', {'weeks':weeksOnPage, 'years': yearsOnPage, 'sel_year': yearOfSeason, 'message': message, 'exceptions': exceptionCollection})
            else:
                return render (request, 'nfl/pullData.html', {'weeks':weeksOnPage, 'years': yearsOnPage, 'sel_year': yearOfSeason, 'message': message})

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

                    matchEspnId = gameData['id']
                    dateOfGameFromApi = gameData['date']
                    dateOfGame = datetime.datetime.fromisoformat(dateOfGameFromApi.replace("Z", ":00"))

                    gameStatusUrl = gameData['competitions'][0]['status']['$ref']
                    gameStatusResponse = requests.get(gameStatusUrl)
                    gameStatus = gameStatusResponse.json()


                    gameCompleted = (gameStatus['type']['completed'] == True)
                    gameOvertime = ("OT" in gameStatus['type']['detail']) 

                    oddsUrl = gameData['competitions'][0]['odds']['$ref']
                    oddsResponse = requests.get(oddsUrl)
                    oddsData = oddsResponse.json()

                    existingMatch = None

                    try:
                        existingMatch = nflMatch.objects.get(espnId = matchEspnId)
                    except:
                        pass
                    
                    if datetime.datetime.now()<dateOfGame or gameCompleted == False:
                        businessLogic.createOrUpdateScheduledNflMatch(existingMatch, gameData, oddsData, weekOfSeason, yearOfSeason)
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
                        
                        matchData = businessLogic.createOrUpdateNflMatch(existingMatch, gameData, homeTeamScore, homeTeamStats, awayTeamScore, awayTeamStats, oddsData, playsData, weekOfSeason, yearOfSeason)

                        try:
                            businessLogic.createTeamPerformance(homeTeamScore, homeTeamStats, matchData.espnId, matchData.homeTeamEspnId, matchData.awayTeamEspnId, playsData, drivesData, seasonWeek=weekOfSeason, seasonYear=yearOfSeason)
                        except Exception as e: 
                            businessLogic.updateTeamPerformance(homeTeamScore, homeTeamStats, matchData.espnId, matchData.homeTeamEspnId, matchData.awayTeamEspnId, playsData, drivesData, weekOfSeason, yearOfSeason)
                        
                        try:
                            businessLogic.createTeamPerformance(awayTeamScore, awayTeamStats, matchData.espnId, matchData.awayTeamEspnId, matchData.homeTeamEspnId, playsData, drivesData, seasonWeek=weekOfSeason, seasonYear=yearOfSeason)
                        except Exception as e:
                            businessLogic.updateTeamPerformance(awayTeamScore, awayTeamStats, matchData.espnId, matchData.awayTeamEspnId, matchData.homeTeamEspnId, playsData, drivesData, weekOfSeason, yearOfSeason)
                            
                
                print("Week ", str(i), " loaded.")
                i += 1
            
            message = "Full " + str(yearOfSeason) + " season loaded."
            return render (request, 'nfl/pullData.html', {'weeks':weeksOnPage, 'years': yearsOnPage, 'message': message})

        elif 'reset' in request.GET:
            businessLogic.resetAllMatchAssociationsForClearing()
            return render (request, 'nfl/pullData.html')

        elif 'resetPerf' in request.GET:
            resetMessage = businessLogic.resetAllPerformanceAssociationsForClearing()
            return render(request, 'nfl/pullData.html', {"message": resetMessage})
        
        elif 'deleteDrives' in request.GET:
            deleteDrivesMessage = crudLogic.deleteDriveOfPlay()
            return render(request, 'nfl/pullData.html', {"message": deleteDrivesMessage})

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
            


            return render (request, 'nfl/pullData.html', {'weeks':weeksOnPage, 'years': yearsOnPage, 'teamNames': teamNames})
        else:
            return render (request, 'nfl/pullData.html', {'weeks':weeksOnPage, 'years': yearsOnPage})
    else: 
        return HttpResponse('unsuccessful')

def getPlayers(request):
    nflTeams = nflTeam.objects.all().order_by('abbreviation')

    yearsOnPage = []
    for y in range(2023, 2022, -1):
        yearsOnPage.append(y)

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
                        crudLogic.createPlayerAthletes(subsection, teamId)
                        #crudLogic.createPlayerAthlete(subsection, teamId)


                    playersLoaded = player.objects.filter(team = selectedTeam).order_by('sideOfBall').order_by('playerPosition')

                    playerTenuresLoaded = []
                    for pl in playersLoaded:
                        individualPlayerTenures = playerTeamTenure.objects.filter(player = pl)
                        for ipt in individualPlayerTenures:
                            playerTenuresLoaded.append(ipt)
                    
                    # print(playerTenuresLoaded)

                    return render(request, 'nfl/players.html', {"teams": nflTeams, 'years': yearsOnPage, 'selTeam': selectedTeam, 'players': playersLoaded, 'season': inputReq['season'], 'tenures': playerTenuresLoaded})

        else:
            return render(request, 'nfl/players.html', {"teams": nflTeams, 'years': yearsOnPage})
    else:
        return render(request, 'nfl/players.html', {"teams": nflTeams, 'years': yearsOnPage})



def loadModel(request, target):
    weeksOnPage = []
    for w in range(2,19):
        weeksOnPage.append([w, w])
    weeksOnPage.append([19, "Wildcard Weekend"])
    weeksOnPage.append([20, "Divisional Round"])
    weeksOnPage.append([21, "Conference Championship"])
    weeksOnPage.append([22, "Super Bowl"])

    yearsOnPage = []
    for y in range(2023, 2017, -1):
        yearsOnPage.append(y)
    
    inputReq = request.GET
    reqTarget = target
    if request.method == 'GET':
       
        if 'season' in request.GET and 'week' in request.GET:  
            
            
            yearOfSeason = inputReq['season'].strip()
            weekOfSeason = inputReq['week'].strip()
            selectedModel = inputReq['model']

            calculcatingCurrentSeason = businessLogic.checkIfCurrentSeason(yearOfSeason)

            #weeksInSeason = 18 if int(yearOfSeason) >= 2021 else 17

            modelResults = []
            if not calculcatingCurrentSeason:
               
                gamesInWeek = nflMatch.objects.filter(yearOfSeason = yearOfSeason).filter(weekOfSeason = int(weekOfSeason))
                for match in gamesInWeek:
                    if selectedModel == "v1":
                        individualModelResult = businessLogic.generateBettingModelHistV1(match)

                        gameEspnId = match.espnId
                        
                        if(match.completed):
                            team1 = nflTeam.objects.get(espnId = match.homeTeamEspnId)
                            team2 = nflTeam.objects.get(espnId = match.awayTeamEspnId)

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
                        
                        modelResults.append(individualModelResult)
                        

                    elif(selectedModel == "v2"):
                        individualModelResult = businessLogic.generateBettingModelHistV2(match)

                        gameEspnId = match.espnId

                        if(match.completed):
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
                        
                        modelResults.append(individualModelResult)
                else:

                    url = ('https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/'+yearOfSeason+'/types/2/weeks/'+weekOfSeason+'/events')
                    if(int(weekOfSeason) >= 19):
                        playoffWeekOfSeason = int(weekOfSeason) - 18
                        url = ('https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/'+str(yearOfSeason)+'/types/3/weeks/'+str(playoffWeekOfSeason)+'/events')
                    
                    response = requests.get(url)
                    data = response.json()
                    gameLinks = data['items']
                    
                    for link in gameLinks:
                        
                        gameDataResponse = requests.get(link['$ref'])
                        gameData = gameDataResponse.json()
                        completed = (gameData['competitions'][0]['boxscoreSource']['state'] == "full" and gameData['competitions'][0]['liveAvailable'] == False )

                        if selectedModel == "v1":
                            individualModelResult = businessLogic.generateBettingModelV1(gameData, weekOfSeason, yearOfSeason)

                            gameEspnId = gameData['id']
                            match = nflMatch.objects.get(espnId = gameEspnId)

                            if(completed):
                                team1 = nflTeam.objects.get(espnId = match.homeTeamEspnId)
                                team2 = nflTeam.objects.get(espnId = match.awayTeamEspnId)

                                #print("Game ID: ", gameEspnId)
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
                            individualModelResult = businessLogic.generateBettingModelV2(gameData, weekOfSeason, yearOfSeason)

                            gameEspnId = gameData['id']
                            match = nflMatch.objects.get(espnId = gameEspnId)
                            

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
                            
                                
                                

                        #modelResults.append(individualModelResult)

                    overUnderCorrect = len(list(filter(lambda x: x.overUnderBetIsCorrect == 'True', modelResults)))
                    overUnderWrong = len(list(filter(lambda x: x.overUnderBetIsCorrect == 'False', modelResults)))
                    overUnderPush = len(list(filter(lambda x: x.overUnderBetIsCorrect == 'Push', modelResults)))
                    overUnderRecord = str(overUnderCorrect) + " - " + str(overUnderWrong) + " - " + str(overUnderPush)

                    lineBetCorrect = len(list(filter(lambda x: x.lineBetIsCorrect == "True", modelResults)))
                    lineBetWrong = len(list(filter(lambda x: x.lineBetIsCorrect == "False", modelResults)))
                    lineBetPush = len(list(filter(lambda x: x.lineBetIsCorrect == "Push", modelResults)))

                    lineBetRecord = str(lineBetCorrect) + " - " + str(lineBetWrong) + " - " + str(lineBetPush)
                

            if(reqTarget == 'showModel'):
                return render(request, 'nfl/bettingModel.html', {"selectedModel": selectedModel, "modelResults": modelResults, "yearOfSeason": yearOfSeason, "weekOfSeason":weekOfSeason,'weeks':weeksOnPage, 'years': yearsOnPage})
            else:
                #print("passing stuff")
                return render(request, 'nfl/modelSummary.html', {"selectedModel": selectedModel, "modelResults": modelResults, "yearOfSeason": yearOfSeason, "weekOfSeason":weekOfSeason, 'weeks':weeksOnPage, 'years': yearsOnPage, 'ouRecord': overUnderRecord, 'lbRecord': lineBetRecord})
        else: 
            if(reqTarget == 'showModel'):
                return render(request, 'nfl/bettingModel.html', {'weeks':weeksOnPage, 'years': yearsOnPage})
            else:
                return render(request, 'nfl/modelSummary.html', {'weeks':weeksOnPage, 'years': yearsOnPage})
    else:
        if(reqTarget == 'model'):
            return render(request, 'nfl/bettingModel.html')
        else:
            return render(request, 'nfl/modelSummary.html')

def loadModelYear(request):
    yearsOnPage = []
    for y in range(2022, 2017, -1):
        yearsOnPage.append(y)

    modelsOnPage = []
    modelsOnPage.append(['v1', 'V1.0 (Avg Yds/Yds per Pt)'])
    modelsOnPage.append(['v2','V2.0 (Drives vs Drive Result)'])
    
    inputReq = request.GET

    if request.method == 'GET':
       
        if 'season' in request.GET and 'model' in request.GET: 
            selectedModel = inputReq['model']
            yearOfSeason = inputReq['season'].strip()

            calculcatingCurrentSeason = businessLogic.checkIfCurrentSeason(yearOfSeason)

            seasonResults = []

            weeksInSeason = 18 if int(yearOfSeason) >= 2021 else 17

            totalOverUnderWins = 0
            totalOverUnderLosses = 0
            totalLineBetWins = 0
            totalLineBetLosses = 0

            if calculcatingCurrentSeason:
                for wk in range (2, weeksInSeason+1):
                    url = ('https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/'+yearOfSeason+'/types/2/weeks/'+str(wk)+'/events')
                    response = requests.get(url)
                    data = response.json()
                    gameLinks = data['items']
                    modelWeekResults = []
                    for link in gameLinks:
                        
                        gameDataResponse = requests.get(link['$ref'])
                        gameData = gameDataResponse.json()
                        completed = (gameData['competitions'][0]['boxscoreSource']['state'] == "full" and gameData['competitions'][0]['liveAvailable'] == False )

                        if selectedModel == "v1":
                            individualModelResult = businessLogic.generateBettingModelV1(gameData, wk, yearOfSeason)

                            gameEspnId = gameData['id']
                            match = nflMatch.objects.get(espnId = gameEspnId)

                            if(completed):
                                team1 = nflTeam.objects.get(espnId = match.homeTeamEspnId)
                                team2 = nflTeam.objects.get(espnId = match.awayTeamEspnId)

                                #print("Game ID: ", gameEspnId)
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
                            individualModelResult = businessLogic.generateBettingModelV2(gameData, wk, yearOfSeason)

                            gameEspnId = gameData['id']
                            match = nflMatch.objects.get(espnId = gameEspnId)
                            

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

                    overUnderCorrect = len(list(filter(lambda x: x.overUnderBetIsCorrect == 'True', modelWeekResults)))
                    overUnderWrong = len(list(filter(lambda x: x.overUnderBetIsCorrect == 'False', modelWeekResults)))
                    overUnderPush = len(list(filter(lambda x: x.overUnderBetIsCorrect == 'Push', modelWeekResults)))
                    overUnderRecord = str(overUnderCorrect) + " - " + str(overUnderWrong) + " - " + str(overUnderPush)

                    lineBetCorrect = len(list(filter(lambda x: x.lineBetIsCorrect == "True", modelWeekResults)))
                    lineBetWrong = len(list(filter(lambda x: x.lineBetIsCorrect == "False", modelWeekResults)))
                    lineBetPush = len(list(filter(lambda x: x.lineBetIsCorrect == "Push", modelWeekResults)))
                    lineBetRecord = str(lineBetCorrect) + " - " + str(lineBetWrong) + " - " + str(lineBetPush)

                    totalOverUnderWins += overUnderCorrect
                    totalOverUnderLosses += overUnderWrong

                    totalLineBetWins += lineBetCorrect
                    totalLineBetLosses += lineBetWrong

                    seasonResults.append([wk, overUnderRecord, lineBetRecord, modelWeekResults])
            
            else:
                for wk in range (2, weeksInSeason+1):
                    gamesInWeek = nflMatch.objects.filter(yearOfSeason = yearOfSeason).filter(weekOfSeason = wk)
                    
                    modelWeekResults = []
                    for match in gamesInWeek:
                        
                        completed = True

                        if selectedModel == "v1":
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

                    overUnderCorrect = len(list(filter(lambda x: x.overUnderBetIsCorrect == 'True', modelWeekResults)))
                    overUnderWrong = len(list(filter(lambda x: x.overUnderBetIsCorrect == 'False', modelWeekResults)))
                    overUnderPush = len(list(filter(lambda x: x.overUnderBetIsCorrect == 'Push', modelWeekResults)))
                    overUnderRecord = str(overUnderCorrect) + " - " + str(overUnderWrong) + " - " + str(overUnderPush)

                    lineBetCorrect = len(list(filter(lambda x: x.lineBetIsCorrect == "True", modelWeekResults)))
                    lineBetWrong = len(list(filter(lambda x: x.lineBetIsCorrect == "False", modelWeekResults)))
                    lineBetPush = len(list(filter(lambda x: x.lineBetIsCorrect == "Push", modelWeekResults)))
                    lineBetRecord = str(lineBetCorrect) + " - " + str(lineBetWrong) + " - " + str(lineBetPush)

                    totalOverUnderWins += overUnderCorrect
                    totalOverUnderLosses += overUnderWrong

                    totalLineBetWins += lineBetCorrect
                    totalLineBetLosses += lineBetWrong

                    seasonResults.append([wk, overUnderRecord, lineBetRecord, modelWeekResults])

            return render(request, 'nfl/yearlySummary.html', {'models': modelsOnPage, 'years': yearsOnPage, 'selectedModel': selectedModel, 'seasonResults':seasonResults, 'ouWins': totalOverUnderWins, 'ouLosses': totalOverUnderLosses, 'lbWins': totalLineBetWins, 'lbLosses': totalLineBetLosses, 'yearOfSeason':yearOfSeason})
        else: 
            return render(request, 'nfl/yearlySummary.html', {'models': modelsOnPage, 'years': yearsOnPage})
    else:
        return render(request, 'nfl/yearlySummary.html', {'models': modelsOnPage, 'years': yearsOnPage})

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





