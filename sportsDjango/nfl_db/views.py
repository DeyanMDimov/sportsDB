from django.shortcuts import render
from django.http import HttpResponse
from django.core import serializers
import json
from nfl_db.models import nflTeam
from nfl_db.models import nflMatch
from nfl_db.models import teamMatchPerformance
from django.db import models
import requests
from nfl_db import businessLogic
import datetime
import time

# Create your views here.

def index(request):
    return render (request, 'nfl/base.html')

def getData(request):
    if request.method == 'GET':
        if 'season' in request.GET and 'week' in request.GET:     
            print("Hit game stats endpoint")
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

                    playsDataUrl = gameData['competitions'][0]['details']['$ref']
                    playsDataResponse = requests.get(playsDataUrl)
                    playsData = playsDataResponse.json()
                    
                    matchData = businessLogic.createOrUpdateNflMatch(existingMatch, gameData, gameCompleted, gameOvertime, homeTeamScore, homeTeamStats, awayTeamScore, awayTeamStats, oddsData, playsData, weekOfSeason, yearOfSeason)

                    try:
                        businessLogic.createTeamPerformance(homeTeamScore, homeTeamStats, matchData.espnId, matchData.homeTeamEspnId, matchData.awayTeamEspnId, playsData, seasonWeek=weekOfSeason, seasonYear=yearOfSeason)
                        businessLogic.createTeamPerformance(awayTeamScore, awayTeamStats, matchData.espnId, matchData.awayTeamEspnId, matchData.homeTeamEspnId, playsData, seasonWeek=weekOfSeason, seasonYear=yearOfSeason)

                        responseMessage = "Successfully pulled in Week " + str(weekOfSeason) + " for " + str(yearOfSeason)
                    except Exception as e: 
                        businessLogic.updateTeamPerformance(homeTeamScore, homeTeamStats, matchData.espnId, matchData.homeTeamEspnId, matchData.awayTeamEspnId, playsData, weekOfSeason, yearOfSeason)
                        businessLogic.updateTeamPerformance(awayTeamScore, awayTeamStats, matchData.espnId, matchData.awayTeamEspnId, matchData.homeTeamEspnId, playsData, weekOfSeason, yearOfSeason)

            return render (request, 'nfl/pullData.html', {"message": responseMessage})

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
                    
                    if datetime.datetime.now()<dateOfGame or gameCompleted==False:
                        businessLogic.createOrUpdateScheduledNflMatch(existingMatch, gameData, oddsData, str(weekOfSeason), str(yearOfSeason))
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

                        playsDataUrl = gameData['competitions'][0]['details']['$ref']
                        playsDataResponse = requests.get(playsDataUrl)
                        playsData = playsDataResponse.json()
                        
                        matchData = businessLogic.createOrUpdateNflMatch(existingMatch, gameData, gameCompleted, gameOvertime, homeTeamScore, homeTeamStats, awayTeamScore, awayTeamStats, oddsData, playsData, str(weekOfSeason), str(yearOfSeason))

                        try:
                            businessLogic.createTeamPerformance(homeTeamScore, homeTeamStats, matchData.espnId, matchData.homeTeamEspnId, matchData.awayTeamEspnId, playsData, seasonWeek=str(weekOfSeason), seasonYear=str(yearOfSeason))
                        except Exception as e: 
                            businessLogic.updateTeamPerformance(homeTeamScore, homeTeamStats, matchData.espnId, matchData.homeTeamEspnId, matchData.awayTeamEspnId, playsData, str(weekOfSeason), str(yearOfSeason))
                        try:
                            businessLogic.createTeamPerformance(awayTeamScore, awayTeamStats, matchData.espnId, matchData.awayTeamEspnId, matchData.homeTeamEspnId, playsData, seasonWeek=str(weekOfSeason), seasonYear=str(yearOfSeason))
                        except Exception as e:
                            businessLogic.updateTeamPerformance(awayTeamScore, awayTeamStats, matchData.espnId, matchData.awayTeamEspnId, matchData.homeTeamEspnId, playsData, str(weekOfSeason), str(yearOfSeason))
                            
                            
                
                print("Week ", str(i), " loaded.")
                i += 1
            if startWeek == endWeek:
                message = "Games loaded for Week " + str(startWeek) + " of " + str(yearOfSeason) + " season."
            else:
                message = "Games loaded for Week " + str(startWeek) + " through Week " + str(endWeek) + " of " + str(yearOfSeason) + " season."
            return render (request, 'nfl/pullData.html', {'message': message})

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

                        playsDataUrl = gameData['competitions'][0]['details']['$ref']
                        playsDataResponse = requests.get(playsDataUrl)
                        playsData = playsDataResponse.json()
                        
                        matchData = businessLogic.createOrUpdateNflMatch(existingMatch, gameData, homeTeamScore, homeTeamStats, awayTeamScore, awayTeamStats, oddsData, playsData, weekOfSeason, yearOfSeason)

                        try:
                            businessLogic.createTeamPerformance(homeTeamScore, homeTeamStats, matchData.espnId, matchData.homeTeamEspnId, matchData.awayTeamEspnId, playsData, seasonWeek=weekOfSeason, seasonYear=yearOfSeason)
                            businessLogic.createTeamPerformance(awayTeamScore, awayTeamStats, matchData.espnId, matchData.awayTeamEspnId, matchData.homeTeamEspnId, playsData, seasonWeek=weekOfSeason, seasonYear=yearOfSeason)
                        except Exception as e: 
                            businessLogic.updateTeamPerformance(homeTeamScore, homeTeamStats, matchData.espnId, matchData.homeTeamEspnId, matchData.awayTeamEspnId, playsData, weekOfSeason, yearOfSeason)
                            businessLogic.updateTeamPerformance(awayTeamScore, awayTeamStats, matchData.espnId, matchData.awayTeamEspnId, matchData.homeTeamEspnId, playsData, weekOfSeason, yearOfSeason)
                            
                
                print("Week ", str(i), " loaded.")
                i += 1
            
            message = "Full " + str(yearOfSeason) + " season loaded."
            return render (request, 'nfl/pullData.html', {'message': message})

        elif 'reset' in request.GET:
            businessLogic.resetAllMatchAssociationsForClearing()
            return render (request, 'nfl/pullData.html')

        elif 'resetPerf' in request.GET:
            resetMessage = businessLogic.resetAllPerformanceAssociationsForClearing()
            return render(request, 'nfl/pullData.html', {"message": resetMessage})
        
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
            


            return render (request, 'nfl/pullData.html', {"teamNames": teamNames})
        else:
            return render (request, 'nfl/pullData.html')
    else: 
        return HttpResponse('unsuccessful')


def loadModel(request, target):
    inputReq = request.GET
    reqTarget = target
    if request.method == 'GET':
       
        if 'season' in request.GET and 'week' in request.GET:  
            print("Hit generate model endpoint")
            #inputReq = request.GET
            yearOfSeason = inputReq['season'].strip()
            weekOfSeason = inputReq['week'].strip()

            
            url = ('https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/'+yearOfSeason+'/types/2/weeks/'+weekOfSeason+'/events')
            if(int(weekOfSeason) >= 19):
                playoffWeekOfSeason = int(weekOfSeason) - 18
                url = ('https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/'+str(yearOfSeason)+'/types/3/weeks/'+str(playoffWeekOfSeason)+'/events')
            
            response = requests.get(url)
            data = response.json()
            gameLinks = data['items']
            modelResults = []
            for link in gameLinks:
                
                gameDataResponse = requests.get(link['$ref'])
                gameData = gameDataResponse.json()
                completed = (gameData['competitions'][0]['boxscoreSource']['state'] == "full" and gameData['competitions'][0]['liveAvailable'] == False )

                individualModelResult = businessLogic.generateBettingModel(gameData, weekOfSeason, yearOfSeason, completed)

                gameEspnId = gameData['id']
                match = nflMatch.objects.get(espnId = gameEspnId)

                if(completed):
                    
                    #print("Game ID: ", gameEspnId)
                    if match.awayTeamPoints != None:     
                        individualModelResult.team1ActualYards = match.homeTeamTotalYards
                        individualModelResult.team2ActualYards = match.awayTeamTotalYards
                        individualModelResult.team1ActualPoints = match.homeTeamPoints
                        individualModelResult.team2ActualPoints = match.awayTeamPoints
                        individualModelResult.actualSpread = match.awayTeamPoints - match.homeTeamPoints
                        individualModelResult.actualTotal = match.homeTeamPoints + match.awayTeamPoints
                        individualModelResult.gameCompleted = True
                    
                if match.overUnderLine != 0:
                    individualModelResult.bookProvidedSpread = match.matchLineHomeTeam
                    individualModelResult.bookProvidedTotal = match.overUnderLine
                      

                modelResults.append(individualModelResult)
                

            if(reqTarget == 'showModel'):
                return render(request, 'nfl/bettingModel.html', {"modelResults": modelResults, "yearOfSeason": yearOfSeason, "weekOfSeason":weekOfSeason})
            else:
                print("passing stuff")
                return render(request, 'nfl/modelSummary.html', {"modelResults": modelResults, "yearOfSeason": yearOfSeason, "weekOfSeason":weekOfSeason})
        else: 
            if(reqTarget == 'showModel'):
                return render(request, 'nfl/bettingModel.html')
            else:
                return render(request, 'nfl/modelSummary.html')
    else:
        if(reqTarget == 'model'):
            return render(request, 'nfl/bettingModel.html')
        else:
            return render(request, 'nfl/modelSummary.html')


def fullTeamStats(request):
    inputReq = request.GET

    if(request.method == 'GET'):
        if 'teamName' in inputReq:
            
            yearOfSeason = inputReq['season']

            selectedTeam = nflTeam.objects.get(abbreviation = inputReq['teamName'])

            selectedTeamEspnId = selectedTeam.espnId

            teamHomeGames = nflMatch.objects.filter(homeTeam = selectedTeam).filter(yearOfSeason = yearOfSeason).filter(completed = True)
            teamAwayGames = nflMatch.objects.filter(awayTeam = selectedTeam).filter(yearOfSeason = yearOfSeason).filter(completed = True)

            allTeamGames = nflMatch.objects.filter(homeTeam = selectedTeam).filter(yearOfSeason = yearOfSeason).filter(completed = True) | nflMatch.objects.filter(awayTeam = selectedTeam).filter(yearOfSeason = yearOfSeason).filter(completed = True)

            allTeamGames = allTeamGames.order_by('datePlayed')

            listOfPerformances = []

            for game in allTeamGames:
                performance = teamMatchPerformance.objects.get(matchEspnId = game.espnId, teamEspnId = selectedTeamEspnId)
                listOfPerformances.append(performance)

            listOfFieldNames = []

            for f in teamMatchPerformance._meta.get_fields():
                if f.name in ['id', 'matchEspnId', "nflMatch", 'team', 'teamEspnId', 'opponent', 'weekOfSeason', 'yearOfSeason', 'atHome']:
                    pass
                else:
                    listOfFieldNames.append(f.name)

            return render(request, 'nfl/teamDetailedStats.html', {"teams": nflTeam.objects.all().order_by('abbreviation'), "season": yearOfSeason, "teamName": inputReq['teamName'], "teamEspnId": selectedTeamEspnId, "teamPerf": listOfPerformances, "fieldNames": listOfFieldNames})

            
        else:
            return render(request, 'nfl/teamDetailedStats.html', {"teams": nflTeam.objects.all().order_by('abbreviation')})
    else:
        return render(request, 'nfl/teamDetailedStats.html', {"teams": nflTeam.objects.all().order_by('abbreviation')})