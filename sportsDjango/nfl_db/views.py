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
                gameData=gameDataResponse.json()

                matchEspnId = gameData['id']
                dateOfGameFromApi = gameData['date']
                dateOfGame = datetime.datetime.fromisoformat(dateOfGameFromApi.replace("Z", ":00"))

                completed = (gameData['competitions'][0]['boxscoreSource']['state'] == "full" and gameData['competitions'][0]['liveAvailable'] == False )


                oddsUrl = gameData['competitions'][0]['odds']['$ref']
                oddsResponse = requests.get(oddsUrl)
                oddsData = oddsResponse.json()

                existingMatch = None

                responseMessage = ""

                try:
                    existingMatch = nflMatch.objects.get(espnId = matchEspnId)
                except:
                    pass
                
                if datetime.datetime.now()<dateOfGame or completed == False:
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
                    
                    matchData = businessLogic.createOrUpdateNflMatch(existingMatch, gameData, homeTeamScore, homeTeamStats, awayTeamScore, awayTeamStats, oddsData, playsData, weekOfSeason, yearOfSeason)

                    try:
                        businessLogic.createTeamPerformance(homeTeamScore, homeTeamStats, matchData.espnId, matchData.homeTeamEspnId, matchData.awayTeamEspnId, seasonWeek=weekOfSeason, seasonYear=yearOfSeason)
                        businessLogic.createTeamPerformance(awayTeamScore, awayTeamStats, matchData.espnId, matchData.awayTeamEspnId, matchData.homeTeamEspnId, seasonWeek=weekOfSeason, seasonYear=yearOfSeason)

                        responseMessage = "Successfully pulled in Week " + str(weekOfSeason) + " for " + str(yearOfSeason)
                    except Exception as e: 
                        print("Hit an Exception")
                        print(e)
                        responseMessage = "Hit an error while pulling in Week " + str(weekOfSeason) + " for " + str(yearOfSeason)

            return render (request, 'nfl/nflhome.html', {"message": responseMessage})
        elif 'espnGameId' in request.GET:
            print("Hit single game endpoint")
            inputReq = request.GET
            yearOfSeason = inputReq['season'].strip()
            weekOfSeason = inputReq['week'].strip()
        
        elif 'season' in request.GET and 'full' in request.GET:
            
            print("Hit full season endpoint")
            inputReq = request.GET
            yearOfSeason = inputReq['season'].strip()
            i = 1
            
            while i <= 18: 
                time.sleep(5)
                weekOfSeason = str(i)
            
                url = ('https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/'+yearOfSeason+'/types/2/weeks/'+weekOfSeason+'/events')
                response = requests.get(url)
                data = response.json()
                gameLinks = data['items']

                for link in gameLinks:
                    
                    gameDataResponse = requests.get(link['$ref'])
                    gameData=gameDataResponse.json()

                    matchEspnId = gameData['id']
                    dateOfGameFromApi = gameData['date']
                    dateOfGame = datetime.datetime.fromisoformat(dateOfGameFromApi.replace("Z", ":00"))

                    completed = (gameData['competitions'][0]['boxscoreSource']['state'] == "full" and gameData['competitions'][0]['liveAvailable'] == False)

                    oddsUrl = gameData['competitions'][0]['odds']['$ref']
                    oddsResponse = requests.get(oddsUrl)
                    oddsData = oddsResponse.json()

                    existingMatch = None

                    try:
                        existingMatch = nflMatch.objects.get(espnId = matchEspnId)
                    except:
                        pass
                    
                    if datetime.datetime.now()<dateOfGame or completed==False:
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
                            businessLogic.createTeamPerformance(homeTeamScore, homeTeamStats, matchData.espnId, matchData.homeTeamEspnId, matchData.awayTeamEspnId, seasonWeek=weekOfSeason, seasonYear=yearOfSeason)
                            businessLogic.createTeamPerformance(awayTeamScore, awayTeamStats, matchData.espnId, matchData.awayTeamEspnId, matchData.homeTeamEspnId, seasonWeek=weekOfSeason, seasonYear=yearOfSeason)
                        except Exception as e: 
                            print("Hit an Exception")
                            print(e)
                            
                
                print("Week ", str(i), " loaded.")
                i += 1
            
            message = "Full " + str(yearOfSeason) + " season loaded."
            return render (request, 'nfl/nflhome.html', {'message': message})

        elif 'reset' in request.GET:
            businessLogic.resetAllMatchAssociationsForClearing()
            return render (request, 'nfl/nflhome.html')

        elif 'resetPerf' in request.GET:
            resetMessage = businessLogic.resetAllPerformanceAssociationsForClearing()
            return render(request, 'nfl/nflhome.html', {"message": resetMessage})
        
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
            


            return render (request, 'nfl/nflhome.html', {"teamNames": teamNames})
        else:
            return render (request, 'nfl/nflhome.html')
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
            response = requests.get(url)
            data = response.json()
            gameLinks = data['items']
            modelResults = []
            for link in gameLinks:
                
                gameDataResponse = requests.get(link['$ref'])
                gameData = gameDataResponse.json()
                completed = (gameData['competitions'][0]['boxscoreSource']['state'] == "full" and gameData['competitions'][0]['liveAvailable'] == False )

                individualModelResult = businessLogic.generateBettingModel(gameData, weekOfSeason, yearOfSeason, completed)

                if(completed):
                    gameEspnId = gameData['id']
                    match = nflMatch.objects.get(espnId = gameEspnId)
                    individualModelResult.team1ActualYards = match.homeTeamTotalYards
                    individualModelResult.team2ActualYards = match.awayTeamTotalYards
                    individualModelResult.team1ActualPoints = match.homeTeamPoints
                    individualModelResult.team2ActualPoints = match.awayTeamPoints
                    individualModelResult.bookProvidedSpread = match.matchLineHomeTeam
                    individualModelResult.actualSpread = match.awayTeamPoints - match.homeTeamPoints
                    individualModelResult.bookProvidedTotal = match.overUnderLine
                    individualModelResult.actualTotal = match.homeTeamPoints + match.awayTeamPoints

                modelResults.append(individualModelResult)
                

            if(reqTarget == 'showModel'):
                return render(request, 'nfl/bettingModel.html', {"modelResults": modelResults, "yearOfSeason": yearOfSeason, "weekOfSeason":weekOfSeason, "gameCompleted": completed})
            else:
                print("passing stuff")
                return render(request, 'nfl/modelSummary.html', {"modelResults": modelResults, "yearOfSeason": yearOfSeason, "weekOfSeason":weekOfSeason, "gameCompleted": completed})
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
                if f in ['id', 'matchEspnId', "nflMatch", 'team', 'teamEspnId', 'opponent', 'weekOfSeason', 'yearOfSeason', 'atHome']:
                    pass
                else:
                    listOfFieldNames.append(f.name)

            return render(request, 'nfl/teamDetailedStats.html', {"teams": nflTeam.objects.all().order_by('abbreviation'), "season": yearOfSeason, "teamName": inputReq['teamName'], "teamEspnId": selectedTeamEspnId, "teamPerf": listOfPerformances, "fieldNames": listOfFieldNames})

            
        else:
            return render(request, 'nfl/teamDetailedStats.html', {"teams": nflTeam.objects.all().order_by('abbreviation')})
    else:
        return render(request, 'nfl/teamDetailedStats.html', {"teams": nflTeam.objects.all().order_by('abbreviation')})