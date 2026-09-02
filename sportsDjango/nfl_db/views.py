from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.core import serializers
import json
from nfl_db.models import nflTeam, nflMatch, teamMatchPerformance, driveOfPlay, player, playerTeamTenure, playerWeekStatus, playByPlay, availabilityJob
from nfl_db.models import passerStatSplit, rusherStatSplit, receiverStatSplit, returnerStatSplit
from django.db import models
from nfl_db import businessLogic, crudLogic, players
import datetime, time, requests, traceback, threading
from zoneinfo import ZoneInfo

# Create your views here.

def index(request):
    return render (request, 'nfl/base.html')

def getData(request):

    weeksOnPage = weeksOnPage_Helper()
    yearsOnPage = yearsOnPage_Helper()

    pageDictionary = {}
    pageDictionary['weeks'] = weeksOnPage_Helper()
    pageDictionary['years'] = yearsOnPage_Helper()
    pageDictionary['teams'] = nflTeam.objects.all().order_by('abbreviation')

    if request.method == 'GET':
        if 'dataCleanup' in request.GET:
            # Two steps: the button previews what is wrong, and only a second
            # click with dataCleanup=run actually deletes anything.
            cleanupAction = request.GET['dataCleanup']
            if cleanupAction in ['dates', 'datesRun']:
                pageDictionary['dateReport'] = crudLogic.backfillWeekStatusDates(applyChanges = cleanupAction == 'datesRun')
            else:
                pageDictionary['cleanupReport'] = crudLogic.runPlayerDataCleanup(applyChanges = cleanupAction == 'run')
            return render(request, 'nfl/pullData.html', pageDictionary)

        if 'season' in request.GET and 'week' in request.GET:     
        #     inputReq = request.GET
        #     yearOfSeason = inputReq['season'].strip()
        #     weekOfSeason = inputReq['week'].strip()

        #     pageDictionary['sel_year'] = yearOfSeason
        #     pageDictionary['start_week'] = weekOfSeason
            
        #     url = ('https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/'+yearOfSeason+'/types/2/weeks/'+weekOfSeason+'/events')
        #     response = requests.get(url)
        #     data = response.json()
        #     gameLinks = data['items']

        #     for link in gameLinks:
                
        #         gameDataResponse = requests.get(link['$ref'])
        #         gameData = gameDataResponse.json()

        #         matchEspnId = gameData['id']
        #         dateOfGameFromApi = gameData['date']
        #         dateOfGame = datetime.datetime.fromisoformat(dateOfGameFromApi.replace("Z", ":00"))

        #         homeTeamEspnId = gameData['competitions'][0]['competitors'][0]['id']
        #         awayTeamEspnId = gameData['competitions'][0]['competitors'][1]['id']
        #         homeTeamAbbr = nflTeam.objects.get(espnId = homeTeamEspnId).abbreviation
        #         awayTeamAbbr = nflTeam.objects.get(espnId = awayTeamEspnId).abbreviation
        #         print()
        #         print("Processing " + homeTeamAbbr + " vs. " + awayTeamAbbr)

        #         gameStatusUrl = gameData['competitions'][0]['status']['$ref']
        #         gameStatusResponse = requests.get(gameStatusUrl)
        #         gameStatus = gameStatusResponse.json()

        #         gameCompleted = (gameStatus['type']['completed'] == True)
        #         gameOvertime = ("OT" in gameStatus['type']['detail']) 

        #         oddsUrl = gameData['competitions'][0]['odds']['$ref']
        #         print(gameData['competitions'][0]['odds'])
        #         oddsResponse = requests.get(oddsUrl)
        #         oddsData = oddsResponse.json()

        #         existingMatch = None
        #         existingHomeTeamPerf = None
        #         existingAwayTeamPerf = None
                
        #         responseMessage = ""

        #         try:
        #             existingMatch = nflMatch.objects.get(espnId = matchEspnId)
        #         except Exception as e:
        #                 print(e)
                
                
        #         if datetime.datetime.now()<dateOfGame or gameCompleted == False:
        #             print("updating scheduled match")
        #             businessLogic.createOrUpdateScheduledNflMatch(existingMatch, gameData, oddsData, weekOfSeason, yearOfSeason)
        #         else:
        #             print("creating or updating matchData")
        #             homeTeamStatsUrl = gameData['competitions'][0]['competitors'][0]['statistics']['$ref']
        #             homeTeamStatsResponse = requests.get(homeTeamStatsUrl)
        #             homeTeamStats = homeTeamStatsResponse.json()

        #             homeTeamScoreUrl = gameData['competitions'][0]['competitors'][0]['score']['$ref']
        #             homeTeamScoreResponse = requests.get(homeTeamScoreUrl)
        #             homeTeamScore = homeTeamScoreResponse.json()

        #             awayTeamStatsUrl = gameData['competitions'][0]['competitors'][1]['statistics']['$ref']
        #             awayTeamStatsResponse = requests.get(awayTeamStatsUrl)
        #             awayTeamStats = awayTeamStatsResponse.json()
                    
        #             awayTeamScoreUrl = gameData['competitions'][0]['competitors'][1]['score']['$ref']
        #             awayTeamScoreResponse = requests.get(awayTeamScoreUrl)
        #             awayTeamScore = awayTeamScoreResponse.json()

        #             drivesDataUrl = gameData['competitions'][0]['drives']['$ref']
        #             drivesDataResponse = requests.get(drivesDataUrl)
        #             drivesData = drivesDataResponse.json()

        #             playsDataUrl = gameData['competitions'][0]['details']['$ref']
                    
        #             playsDataResponse = requests.get(playsDataUrl)
        #             playsData = playsDataResponse.json()

                    
                    
        #             matchData = businessLogic.createOrUpdateNflMatch(existingMatch, gameData, gameCompleted, gameOvertime, homeTeamScore, homeTeamStats, awayTeamScore, awayTeamStats, oddsData, playsData, drivesData, weekOfSeason, yearOfSeason)

        #             try:
        #                 businessLogic.createTeamPerformance(homeTeamScore, homeTeamStats, matchData.espnId, matchData.homeTeamEspnId, matchData.awayTeamEspnId, playsData, drivesData, seasonWeek=weekOfSeason, seasonYear=yearOfSeason)
        #                 businessLogic.createTeamPerformance(awayTeamScore, awayTeamStats, matchData.espnId, matchData.awayTeamEspnId, matchData.homeTeamEspnId, playsData, drivesData, seasonWeek=weekOfSeason, seasonYear=yearOfSeason)

        #                 pageDictionary['responseMessage'] = "Successfully pulled in Week " + str(weekOfSeason) + " for " + str(yearOfSeason)
        #             except Exception as e: 
        #                 businessLogic.updateTeamPerformance(homeTeamScore, homeTeamStats, matchData.espnId, matchData.homeTeamEspnId, matchData.awayTeamEspnId, playsData, drivesData, weekOfSeason, yearOfSeason)
        #                 businessLogic.updateTeamPerformance(awayTeamScore, awayTeamStats, matchData.espnId, matchData.awayTeamEspnId, matchData.homeTeamEspnId, playsData, drivesData, weekOfSeason, yearOfSeason)

        #     return render (request, 'nfl/pullData.html', pageDictionary)
            pass

        if 'espnGameId' in request.GET:
            inputReq = request.GET
            matchEspnId = inputReq['espnGameId'].strip()
            
            try:
                # Fetch the match data from ESPN API
                matchURL = f"http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/{matchEspnId}?lang=en&region=us"
                matchResponse = requests.get(matchURL)
                
                if matchResponse.status_code != 200:
                    pageDictionary['specificMatchMessage'] = f"Error: Could not find match with ID {matchEspnId}"
                    return render(request, 'nfl/pullData.html', pageDictionary)
                
                gameData = matchResponse.json()
                
                # Get the week and year from the existing match or game data
                try:
                    existingMatch = nflMatch.objects.get(espnId=matchEspnId)
                    weekOfSeason = existingMatch.weekOfSeason
                    yearOfSeason = existingMatch.yearOfSeason
                except nflMatch.DoesNotExist:
                    # Extract from game data if match doesn't exist
                    seasonUrl = gameData['season']['$ref']
                    seasonResponse = requests.get(seasonUrl)
                    seasonData = seasonResponse.json()
                    yearOfSeason = seasonData['year']
                    
                    weekUrl = gameData['week']['$ref']
                    weekResponse = requests.get(weekUrl)
                    weekData = weekResponse.json()
                    weekOfSeason = weekData['number']
                
                # Process the game
                homeTeamEspnId = gameData['competitions'][0]['competitors'][0]['id']
                awayTeamEspnId = gameData['competitions'][0]['competitors'][1]['id']
                homeTeamAbbr = nflTeam.objects.get(espnId=homeTeamEspnId).abbreviation
                awayTeamAbbr = nflTeam.objects.get(espnId=awayTeamEspnId).abbreviation
                
                print(f"Reprocessing match {matchEspnId}: {homeTeamAbbr} vs {awayTeamAbbr}")
                
                crudLogic.processGameData(gameData, weekOfSeason, yearOfSeason)

                plays_updated, scoring_corrected = crudLogic.reprocessMatchPlays(matchEspnId)
        
                pageDictionary['specificMatchMessage'] = f"Successfully reprocessed match {matchEspnId}: {homeTeamAbbr} vs {awayTeamAbbr} (Week {weekOfSeason}, {yearOfSeason}). Updated {plays_updated} plays, corrected {scoring_corrected} scoring flags."
                
            except Exception as e:
                print(f"Error reprocessing match {matchEspnId}: {e}")
                pageDictionary['specificMatchMessage'] = f"Error reprocessing match {matchEspnId}: {str(e)}"
            
            return render(request, 'nfl/pullData.html', pageDictionary)
        
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
                print(f'Procesing Week {i}')
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

                            
                print()
                print("Week ", str(i), " loaded.")
                print()
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
            return render (request, 'nfl/pullData.html', {'weeks':weeksOnPage, 'years': yearsOnPage, 'teams': nflTeam.objects.all().order_by('abbreviation'), 'message': message})

        # elif 'reset' in request.GET:
        #     crudLogic.resetAllMatchAssociationsForClearing()
        #     return render (request, 'nfl/pullData.html')

        # elif 'resetPerf' in request.GET:
        #     resetMessage = crudLogic.resetAllPerformanceAssociationsForClearing()
        #     return render(request, 'nfl/pullData.html', {"message": resetMessage})
        
        # elif 'deleteDrives' in request.GET:
        #     deleteDrivesMessage = crudLogic.deleteDriveOfPlay()
        #     return render(request, 'nfl/pullData.html', {"message": deleteDrivesMessage})

        elif 'teamName' in request.GET:
            inputReq = request.GET
            rosterTeamAbbreviation = inputReq['teamName'].strip()

            if rosterTeamAbbreviation == 'ALL':
                teamsToPull = nflTeam.objects.all().order_by('abbreviation')
            else:
                teamsToPull = [nflTeam.objects.get(abbreviation = rosterTeamAbbreviation)]

            rosterPlayers = []
            for rosterTeam in teamsToPull:
                rosterPlayers.extend(crudLogic.pullTeamRosterFromApi(rosterTeam))

            pageDictionary['rosterTeamName'] = rosterTeamAbbreviation
            pageDictionary['rosterPlayers'] = rosterPlayers
            pageDictionary['rosterMessage'] = "Pulled " + str(len(rosterPlayers)) + " players from " + str(len(teamsToPull)) + " roster(s)."

            return render (request, 'nfl/pullData.html', pageDictionary)

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

def performancePlayerOptions(request):
    # Feeds the Performances tab's player dropdown when season/team/position change.
    performanceTeam = nflTeam.objects.filter(abbreviation = request.GET.get('team', '').strip()).first()
    if performanceTeam == None:
        return JsonResponse({'players': []})

    playersForFilters = crudLogic.getPlayersForPerformanceFilters(
        request.GET.get('season', '').strip(),
        performanceTeam,
        request.GET.get('position', '1').strip(),
    )

    return JsonResponse({'players': [{'espnId': playerObj.espnId, 'name': playerObj.name} for playerObj in playersForFilters]})


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
        if 'performancePlayer' in request.GET:
            inputReq = request.GET
            performanceYear = inputReq.get('performanceSeason', str(yearsOnPage[0])).strip()
            performanceTeamAbbreviation = inputReq.get('performanceTeam', '').strip()
            performancePosition = inputReq.get('performancePosition', '1').strip()
            performancePlayerEspnId = inputReq['performancePlayer'].strip()

            performanceTeam = nflTeam.objects.filter(abbreviation = performanceTeamAbbreviation).first()
            performancePlayer = player.objects.filter(espnId = performancePlayerEspnId).first()

            performanceRows = []
            performanceColumns = []
            if performancePlayer != None and performanceTeam != None:
                performanceRows = crudLogic.getPlayerPerformancesForSeason(performancePlayer, performanceTeam, performanceYear)
                for statKey in crudLogic.PERFORMANCE_STATS_BY_POSITION.get(int(performancePosition), []):
                    performanceColumns.append({'key': statKey, 'label': crudLogic.PERFORMANCE_STAT_LABELS[statKey]})

            # Line each row's stats up with the columns so the template just walks them.
            for performanceRow in performanceRows:
                orderedStats = []
                for performanceColumn in performanceColumns:
                    orderedStats.append({
                        'playerValue': performanceRow['playerStats'].get(performanceColumn['key'], 0),
                        'teamValue': performanceRow['teamStats'].get(performanceColumn['key']),
                    })
                performanceRow['orderedStats'] = orderedStats

            return render(request, 'nfl/players.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage,
                'performanceActive': True, 'performanceRows': performanceRows, 'performanceColumns': performanceColumns,
                'performancePlayerName': performancePlayer.name if performancePlayer else "",
                'performancePlayerEspnId': performancePlayerEspnId, 'performanceYear': performanceYear,
                'performanceTeam': performanceTeamAbbreviation, 'performancePosition': performancePosition,
                'performancePositions': crudLogic.PERFORMANCE_POSITIONS,
                'performancePlaysStored': crudLogic.seasonHasStoredPlays(performanceTeam, performanceYear) if performanceTeam else False,
                'performancePlayerOptions': crudLogic.getPlayersForPerformanceFilters(performanceYear, performanceTeam, performancePosition) if performanceTeam else []})

        elif 'viewRosterTeam' in request.GET:
            inputReq = request.GET
            viewRosterTeamAbbreviation = inputReq['viewRosterTeam'].strip()
            viewRosterYear = inputReq.get('viewRosterSeason', str(yearsOnPage[0])).strip()
            selectedTeam = nflTeam.objects.get(abbreviation = viewRosterTeamAbbreviation)

            viewRoster, viewRosterSource = crudLogic.getStartOfSeasonRoster(selectedTeam, viewRosterYear)

            return render(request, 'nfl/players.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage, 'viewRoster': viewRoster, 'viewRosterSource': viewRosterSource, 'viewRosterTeam': viewRosterTeamAbbreviation, 'viewRosterTeamName': selectedTeam.teamName, 'viewRosterYear': viewRosterYear})

        elif 'position' in request.GET:
            inputReq = request.GET
            selectedPosition = inputReq['position'].strip()
            positionYear = inputReq.get('positionSeason', str(yearsOnPage[0])).strip()

            playersLoaded, positionSource = crudLogic.getPlayersByPositionForSeason(selectedPosition, positionYear)
            positionName = dict(player.playerPositions).get(int(selectedPosition), "Players")

            return render(request, 'nfl/players.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage, 'allPlayers': playersLoaded, 'positionSelected': selectedPosition, 'positionName': positionName, 'positionYear': positionYear, 'positionSource': positionSource})

        elif 'jobResult' in request.GET:
            job = availabilityJob.objects.get(id = request.GET['jobResult'])
            jobResult = json.loads(job.result) if job.result else None
            jobError = job.error if job.status == 'error' else None
            return render(request, 'nfl/players.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage, 'jobResult': jobResult, 'jobError': jobError, 'sel_Team': job.team, 'sel_Year': job.season, 'sel_Week': job.week})

        elif 'week' in request.GET:
            inputReq = request.GET
            yearOfSeason = inputReq['season'].strip()
            weekRaw = inputReq['week'].strip()
            teamParam = inputReq.get('team', '').strip()
            pullFresh = 'pullFresh' in inputReq

            # Unticked "Pull Fresh" means look at nothing but the database. No
            # ESPN request, no background job, whatever the team/week combination.
            if not pullFresh:
                storedAvailability = crudLogic.buildAvailabilityFromDatabase(yearOfSeason, weekRaw, teamParam)
                if len(storedAvailability['rows']) == 0:
                    responseMessage = "Nothing stored for that season, week and team yet. Tick \"Pull Fresh\" to pull it from ESPN."
                    return render(request, 'nfl/players.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage, 'responseMessage': responseMessage, 'sel_Team': teamParam, 'sel_Year': yearOfSeason, 'sel_Week': weekRaw, 'pullFresh': pullFresh})

                return render(request, 'nfl/players.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage, 'jobResult': storedAvailability, 'sel_Team': teamParam, 'sel_Year': yearOfSeason, 'sel_Week': weekRaw, 'pullFresh': pullFresh})

            # Heavy pulls (every team, or the whole season) fire many sequential
            # ESPN requests and would blow past the host's web-worker time limit,
            # so hand them to a background thread and let the page poll for the
            # result. A single team + single week is fast, so it stays inline.
            if teamParam == 'ALL' or weekRaw == '100':
                job = availabilityJob.objects.create(season = yearOfSeason, week = weekRaw, team = teamParam)
                workerThread = threading.Thread(target = crudLogic.runAvailabilityJob, args = (job.id,), daemon = True)
                workerThread.start()
                return render(request, 'nfl/players.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage, 'availabilityJobId': job.id, 'sel_Team': teamParam, 'sel_Year': yearOfSeason, 'sel_Week': weekRaw, 'pullFresh': pullFresh})

            weekOfSeason = int(weekRaw)
            if 'team' in inputReq:
                selectedTeam = nflTeam.objects.get(abbreviation = teamParam)
                teamId = selectedTeam.espnId
                selectedMatchQuerySet = nflMatch.objects.filter(weekOfSeason = weekOfSeason, yearOfSeason = yearOfSeason, homeTeamEspnId = teamId)
                if(len(selectedMatchQuerySet) == 0):
                    selectedMatchQuerySet = nflMatch.objects.filter(weekOfSeason = weekOfSeason, yearOfSeason = yearOfSeason, awayTeamEspnId = teamId)
                    if(len(selectedMatchQuerySet) == 0):
                        responseMessage = "Week " + str(weekOfSeason) + " was the Bye week for " + selectedTeam.abbreviation
                        return render(request, 'nfl/players.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage, 'responseMessage': responseMessage, 'sel_Team': teamParam, 'sel_Year': yearOfSeason, 'sel_Week': weekOfSeason, 'pullFresh': pullFresh})

                selectedMatch = selectedMatchQuerySet[0]
                matchId = selectedMatch.espnId

                gameRosterData = crudLogic.fetchGameRoster(matchId, teamId)
                if gameRosterData is None:
                    # ESPN publishes the game roster around kickoff, so an
                    # upcoming week has nothing to show yet.
                    responseMessage = "No player availability published yet for " + selectedTeam.abbreviation + " in week " + str(weekOfSeason) + " of " + str(yearOfSeason) + "."
                    return render(request, 'nfl/players.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage, 'responseMessage': responseMessage, 'sel_Team': teamParam, 'sel_Year': yearOfSeason, 'sel_Week': weekOfSeason, 'pullFresh': pullFresh})

                athleteAvailability = crudLogic.processGameRosterForAvailability(gameRosterData, selectedTeam, yearOfSeason, weekOfSeason)

                return render(request, 'nfl/players.html', {"teams": nflTeams, 'years': yearsOnPage, 'weeks': weeksOnPage, 'athleteAvail': athleteAvailability, 'sel_Team': teamParam, 'sel_Year': yearOfSeason, 'sel_Week': weekOfSeason, 'pullFresh': pullFresh})

    return render(request, 'nfl/players.html', pageDictionary)

def availabilityJobStatus(request):
    # Polled by the players page while a background availability pull runs.
    jobId = request.GET.get('jobId')
    try:
        job = availabilityJob.objects.get(id = jobId)
    except availabilityJob.DoesNotExist:
        return JsonResponse({"status": "error", "progress": "", "error": "Job not found"})

    return JsonResponse({
        "status": job.status,
        "progress": job.progress,
        "error": job.error or "",
    })

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
                            print("OOOPS!")
                            print(f'Over under line: {match.overUnderLine};')
                    else:
                        if match.overUnderLine != 0 and match.overUnderLine != None:
                            individualModelResult.bookProvidedTotal = match.overUnderLine
                        if match.matchLineHomeTeam != None:
                            individualModelResult.bookProvidedSpread = match.matchLineHomeTeam
                        else:
                            print("OOOPS!")
                            print(f'Over under line: {match.overUnderLine};')
                    
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

# Ordered groupings for the Team Stats page. Each entry is
# (groupName, [(subGroupName or None, [fieldName, ...]), ...]).
# Field names must match attributes on teamMatchPerformance. Any stat field
# not listed here (and not in TEAM_STAT_METADATA_FIELDS) is appended to
# Miscellaneous by buildTeamStatGroups so nothing silently disappears.
TEAM_STAT_GROUPS = [
    ("Team / Overall", [
        (None, [
            "totalPointsScored", "totalPointsAllowed", "totalTouchdownsScored",
            "totalPenalties", "totalPenaltyYards",
        ]),
    ]),
    ("Offense", [
        ("Overall", [
            "totalYardsGained", "totalExplosivePlays", "totalGiveaways",
            "totalOffensePenalties", "totalOffensePenaltyYards",
        ]),
        ("Passing", [
            "passCompletions", "passingAttempts", "totalPassingYards",
            "passPlaysTwentyFivePlus", "qbHitsTaken", "sacksTaken", "sackYardsLost",
            "twoPtPassConversions", "twoPtPassAttempts", "interceptionsOnOffense",
            "passingFumbles", "passingFumblesLost",
        ]),
        ("Rushing", [
            "rushingAttempts", "rushingYards", "rushingPlaysTenPlus", "stuffsTaken",
            "stuffYardsLost", "twoPtRushConversions", "twoPtRushAttempts",
            "rushingFumbles", "rushingFumblesLost",
        ]),
        ("Receiving", [
            "totalReceivingYards", "receivingYardsAfterCatch",
        ]),
        ("Red Zone", [
            "redZoneAttempts", "redZoneTDConversions", "redZoneFumbles",
            "redZoneFumblesLost", "redZoneInterceptions",
        ]),
        ("Downs & Drives", [
            "firstDowns", "firstDownsRushing", "firstDownsPassing", "firstDownsByPenalty",
            "thirdDownAttempts", "thirdDownConvs", "fourthDownAttempts", "fourthDownConvs",
            "drivePinnedInsideTen", "drivePinnedInsideFive",
            "rushPctFirstDown", "passPctFirstDown", "completionPctFirstDown",
            "rushPctSecondDown", "passPctSecondDown", "completionPctSecondDown",
            "rushPctThirdDown", "passPctThirdDown", "completionPctThirdDown",
        ]),
    ]),
    ("Defense", [
        (None, [
            "totalPointsAllowedByDefense", "totalYardsAllowedByDefense",
            "totalPassYardsAllowed", "totalRushYardsAllowed",
            "totalTakeaways", "defenseInterceptions", "defenseInterceptionYards",
            "defenseInterceptionTouchdowns", "defenseForcedFumbles",
            "defenseFumblesRecovered", "defenseFumbleTouchdowns",
            "defenseSacks", "sackYardsGained", "qbHits", "defenseStuffs",
            "passesBattedDown", "defensiveTouchdownsScored", "safetiesScored",
            "totalDefensePenalties", "totalDefensePenaltyYards", "firstDownsByPenaltyGiven",
        ]),
    ]),
    ("Special Teams", [
        ("Punting", [
            "totalPunts", "opponentPinnedInsideTen", "opponentPinnedInsideFive",
        ]),
        ("Blocks & Returns", [
            "blockedFieldGoals", "blockedFieldGoalTouchdowns",
            "blockedPunts", "blockedPuntTouchdowns",
        ]),
        ("Penalties", [
            "specialTeamsPenalties", "specialTeamsPenaltyYards",
        ]),
    ]),
    ("Scoring", [
        (None, [
            "passingTouchdowns", "rushingTouchdowns", "totalTwoPointConvs",
            "fieldGoalAttempts", "fieldGoalsMade", "extraPointAttempts", "extraPointsMade",
        ]),
    ]),
    ("Miscellaneous", [
        (None, [
            "twoPtReturns", "onePtSafetiesMade",
        ]),
    ]),
]

# Fields that are metadata rather than stats: excluded from the stat groups.
# weekOfSeason is surfaced separately as a metadata row in the template.
TEAM_STAT_METADATA_FIELDS = {
    'id', 'matchEspnId', 'nflMatch', 'team', 'teamEspnId', 'opponent',
    'yearOfSeason', 'atHome', 'weekOfSeason',
}


def buildTeamStatGroups():
    """Return the Team Stats groupings as template-friendly dicts, appending any
    teamMatchPerformance stat field not explicitly placed in a group to
    Miscellaneous so newly added fields are never silently dropped."""
    groups = []
    covered = set()
    for groupName, subGroups in TEAM_STAT_GROUPS:
        builtSubs = []
        for subName, fields in subGroups:
            builtSubs.append({"name": subName, "fields": list(fields)})
            covered.update(fields)
        groups.append({"name": groupName, "subGroups": builtSubs})

    uncovered = []
    for f in teamMatchPerformance._meta.get_fields():
        if f.name in TEAM_STAT_METADATA_FIELDS or f.name in covered:
            continue
        uncovered.append(f.name)

    if uncovered:
        miscGroup = next((g for g in groups if g["name"] == "Miscellaneous"), None)
        if miscGroup is None:
            miscGroup = {"name": "Miscellaneous", "subGroups": []}
            groups.append(miscGroup)
        miscGroup["subGroups"].append({"name": "Uncategorized", "fields": uncovered})

    return groups


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

            statGroups = buildTeamStatGroups()

            return render(request, 'nfl/teamDetailedStats.html', {"teams": nflTeam.objects.all().order_by('abbreviation'), "season": yearOfSeason, "teamName": inputReq['teamName'], "teamEspnId": selectedTeamEspnId, "teamPerf": listOfPerformances, "statGroups": statGroups, "colSpan": len(listOfPerformances) + 1, 'years': yearsOnPage})

            
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
        if 'week' in request.GET and 'teamName' in request.GET:
            inputReq = request.GET
            yearOfSeason = inputReq['season'].strip()
            weekOfSeason = int(inputReq['week'].strip())
            selectedTeamAbbr = inputReq['teamName'].strip()
            
            pageDictionary['selectedYear'] = yearOfSeason
            pageDictionary['selectedWeek'] = weekOfSeason
            pageDictionary['selectedTeam'] = selectedTeamAbbr

            resultArray = []

            # Filter matches based on team selection
            if selectedTeamAbbr == "ALL":
                teamsToProcess = nflTeam.objects.all()
            else:
                teamsToProcess = [nflTeam.objects.get(abbreviation=selectedTeamAbbr)]
            
            weeksToProcess = range(1, 19, 1) if weekOfSeason == 100 else [weekOfSeason]

            for s_week in weeksToProcess:
                print(f"Processing Week {s_week} - {len(teamsToProcess)} teams")
                
                teamsAlreadyProcessed = []

                for s_team in teamsToProcess:
                    if s_team.espnId in teamsAlreadyProcessed:
                        continue   
                    
                    teamId = s_team.espnId
                
                    # Get matches where the selected team is either home or away
                    matches = nflMatch.objects.filter(
                        yearOfSeason=yearOfSeason,
                        weekOfSeason=s_week
                    ).filter(
                        models.Q(homeTeamEspnId=teamId) | models.Q(awayTeamEspnId=teamId)
                    )
                    
                    for s_match in matches:
                        matchData = retrievePlaysForMatch(s_match, teamId)
                        teamsAlreadyProcessed.append(matchData[2])
                        resultArray.append(matchData)
            
            pageDictionary['resultArray'] = resultArray
            pageDictionary['weekNum'] = weekOfSeason
            pageDictionary['selectedTeam'] = selectedTeamAbbr
            pageDictionary['selectedYear'] = yearOfSeason
            
            return render(request, 'nfl/plays.html', pageDictionary)
        else:
            return render(request, 'nfl/plays.html', pageDictionary)
    
    return render(request, 'nfl/plays.html', pageDictionary)


def retrievePlaysForMatch(s_match, teamId):
    """
    Retrieve all plays for a match, organized by drives.
    Stat splits should already exist from data loading.
    """
    # Get opposing team ID
    opposingTeam = s_match.homeTeamEspnId if teamId != s_match.homeTeamEspnId else s_match.awayTeamEspnId
    
    # Get all drives for this match, sorted by sequence
    drives = driveOfPlay.objects.filter(nflMatch=s_match).order_by('sequenceNumber')
    
    result_drives_array = []
    
    for s_drive in drives:
        # Get all plays for this drive, sorted by sequence
        plays = playByPlay.objects.filter(driveOfPlay=s_drive).order_by('sequenceNumber')
        
        result_plays_array = []
        
        for play in plays:
            # Attach existing stat splits to the play object for display
            play.passer_stats = passerStatSplit.objects.filter(play=play).first()
            play.rusher_stats = rusherStatSplit.objects.filter(play=play).first()
            play.receiver_stats = receiverStatSplit.objects.filter(play=play).first()
            play.returner_stats = returnerStatSplit.objects.filter(play=play).first()
            
            result_plays_array.append(play)
        
        result_drives_array.append([s_drive, result_plays_array])
    
    return [s_match, result_drives_array, opposingTeam]



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
            
            # Determine which touchdowns to load
            load_type = inputReq.get('loadType', 'team')  # 'team', 'opponent', or 'all'
            
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
            
            touchdownData = []
            opponentTouchdownData = []
            
            for match in allMatches:
                # Determine if team was home or away
                isHome = match.homeTeamEspnId == teamId
                opponent = nflTeam.objects.get(
                    espnId=match.awayTeamEspnId if isHome else match.homeTeamEspnId
                )
                
                # Get team's touchdowns (if requested)
                if load_type in ['team', 'all']:
                    teamTds = extractTouchdownsFromMatch(match, selectedTeam, opponent, isHome)
                    touchdownData.extend(teamTds)
                    touchdownData = sorted(touchdownData, key=lambda x: (
                        x['week'],
                        x['quarter'] if x['quarter'] else 'Z',
                        -x['secondsRemainingInPeriod'] if 'secondsRemainingInPeriod' in x and x['secondsRemainingInPeriod'] else 0
                    ))
                
                # Get opponent's touchdowns (if requested)
                if load_type in ['opponent', 'all']:
                    opponentTds = extractTouchdownsFromMatch(match, opponent, selectedTeam, not isHome)
                    opponentTouchdownData.extend(opponentTds)
                    opponentTouchdownData = sorted(opponentTouchdownData, key=lambda x: (
                        x['week'],
                        x['quarter'] if x['quarter'] else 'Z',
                        -x['secondsRemainingInPeriod'] if 'secondsRemainingInPeriod' in x and x['secondsRemainingInPeriod'] else 0
                    ))
            
            # Calculate totals and player summaries
            totalTouchdowns = len(touchdownData)

            playerTouchdowns = calculatePlayerTouchdowns(touchdownData)
            
            totalOpponentTouchdowns = len(opponentTouchdownData)
            # Use position-based calculation for opponent touchdowns
            opponentPositionTouchdowns = calculateTouchdownsByPosition(opponentTouchdownData)
            
            pageDictionary['touchdowns'] = touchdownData
            pageDictionary['opponentTouchdowns'] = opponentTouchdownData
            pageDictionary['selectedTeam'] = selectedTeam
            pageDictionary['yearOfSeason'] = yearOfSeason
            pageDictionary['totalTouchdowns'] = totalTouchdowns
            pageDictionary['playerTouchdowns'] = playerTouchdowns
            pageDictionary['totalOpponentTouchdowns'] = totalOpponentTouchdowns
            pageDictionary['opponentPositionTouchdowns'] = opponentPositionTouchdowns
            pageDictionary['loadType'] = load_type
            
            return render(request, 'nfl/touchdowns.html', pageDictionary)
    
    return render(request, 'nfl/touchdowns.html', pageDictionary)

def predictTouchdowns(request):
    nflTeams = nflTeam.objects.all().order_by('abbreviation')
    yearsOnPage = yearsOnPage_Helper()
    weeksOnPage = weeksOnPage_Helper()
    
    pageDictionary = {}
    pageDictionary['years'] = yearsOnPage
    pageDictionary['teams'] = nflTeams
    pageDictionary['weeks'] = weeksOnPage
    
    if request.method == 'GET':
        if 'teamName' in request.GET and 'season' in request.GET and 'week' in request.GET:
            inputReq = request.GET
            yearOfSeason = inputReq['season'].strip()
            weekOfSeason = int(inputReq['week'].strip())
            selectedTeam = nflTeam.objects.get(abbreviation=inputReq['teamName'])
            teamId = selectedTeam.espnId
            
            # Find the opponent for this week
            upcomingMatch = nflMatch.objects.filter(
                yearOfSeason=yearOfSeason,
                weekOfSeason=weekOfSeason
            ).filter(
                models.Q(homeTeamEspnId=teamId) | models.Q(awayTeamEspnId=teamId)
            ).first()
            
            if not upcomingMatch:
                pageDictionary['error'] = f"No match found for {selectedTeam.abbreviation} in Week {weekOfSeason}"
                return render(request, 'nfl/predictTouchdowns.html', pageDictionary)
            
            # Determine opponent
            opponentId = upcomingMatch.awayTeamEspnId if upcomingMatch.homeTeamEspnId == teamId else upcomingMatch.homeTeamEspnId
            opponent = nflTeam.objects.get(espnId=opponentId)
            
            # Get team's previous matches this season (before selected week)
            teamMatches = nflMatch.objects.filter(
                yearOfSeason=yearOfSeason,
                weekOfSeason__lt=weekOfSeason,
                completed=True
            ).filter(
                models.Q(homeTeamEspnId=teamId) | models.Q(awayTeamEspnId=teamId)
            ).order_by('weekOfSeason')
            
            # Get opponent's previous matches this season (before selected week)
            opponentMatches = nflMatch.objects.filter(
                yearOfSeason=yearOfSeason,
                weekOfSeason__lt=weekOfSeason,
                completed=True
            ).filter(
                models.Q(homeTeamEspnId=opponentId) | models.Q(awayTeamEspnId=opponentId)
            ).order_by('weekOfSeason')
            
            # Get team's touchdowns scored
            teamTouchdowns = []
            for match in teamMatches:
                isHome = match.homeTeamEspnId == teamId
                matchOpponent = nflTeam.objects.get(
                    espnId=match.awayTeamEspnId if isHome else match.homeTeamEspnId
                )
                tds = extractTouchdownsFromMatch(match, selectedTeam, matchOpponent, isHome)
                teamTouchdowns.extend(tds)
            
            # Sort team touchdowns chronologically
            teamTouchdowns = sorted(teamTouchdowns, key=lambda x: (
                x['week'],
                x['quarter'] if x['quarter'] else 'Z',
                -x['secondsRemainingInPeriod'] if 'secondsRemainingInPeriod' in x and x['secondsRemainingInPeriod'] else 0
            ))
            
            # Get opponent's touchdowns allowed (touchdowns scored by their opponents)
            opponentTouchdownsAllowed = []
            for match in opponentMatches:
                isHome = match.homeTeamEspnId == opponentId
                matchOpponent = nflTeam.objects.get(
                    espnId=match.awayTeamEspnId if isHome else match.homeTeamEspnId
                )
                # Get touchdowns scored BY the opponent's opponents (i.e., allowed by the opponent)
                tds = extractTouchdownsFromMatch(match, matchOpponent, opponent, not isHome)
                opponentTouchdownsAllowed.extend(tds)
            
            # Sort opponent touchdowns allowed chronologically
            opponentTouchdownsAllowed = sorted(opponentTouchdownsAllowed, key=lambda x: (
                x['week'],
                x['quarter'] if x['quarter'] else 'Z',
                -x['secondsRemainingInPeriod'] if 'secondsRemainingInPeriod' in x and x['secondsRemainingInPeriod'] else 0
            ))
            
            # Check if the selected week's game has been played
            gameHasBeenPlayed = upcomingMatch.completed
            actualGameTouchdowns = []

            if gameHasBeenPlayed:
                # Get touchdowns from the actual game
                isHome = upcomingMatch.homeTeamEspnId == teamId
                actualGameTouchdowns = extractTouchdownsFromMatch(upcomingMatch, selectedTeam, opponent, isHome)
                
                # Sort chronologically
                actualGameTouchdowns = sorted(actualGameTouchdowns, key=lambda x: (
                    x['quarter'] if x['quarter'] else 'Z',
                    -x['secondsRemainingInPeriod'] if 'secondsRemainingInPeriod' in x and x['secondsRemainingInPeriod'] else 0
                ))

            pageDictionary['teamTouchdowns'] = teamTouchdowns
            pageDictionary['opponentTouchdownsAllowed'] = opponentTouchdownsAllowed
            pageDictionary['selectedTeam'] = selectedTeam
            pageDictionary['opponent'] = opponent
            pageDictionary['yearOfSeason'] = yearOfSeason
            pageDictionary['weekOfSeason'] = weekOfSeason
            pageDictionary['totalTeamTouchdowns'] = len(teamTouchdowns)
            pageDictionary['totalOpponentTouchdownsAllowed'] = len(opponentTouchdownsAllowed)
            pageDictionary['gameHasBeenPlayed'] = gameHasBeenPlayed
            pageDictionary['actualGameTouchdowns'] = actualGameTouchdowns
            pageDictionary['totalActualGameTouchdowns'] = len(actualGameTouchdowns)
            
            return render(request, 'nfl/predictTouchdowns.html', pageDictionary)
    
    return render(request, 'nfl/predictTouchdowns.html', pageDictionary)

def extractTouchdownsFromMatch(match, team, opponent, isHome):
    """
    Extract all touchdowns scored by a team in a match
    Returns list of touchdown dictionaries
    """
    touchdowns = []
    
    # Offensive TDs (rushing and passing)
    offensive_tds = playByPlay.objects.filter(
        nflMatch=match,
        teamOnOffense=team,
        scoringPlay=True,
        offenseScored=True,
        pointsScored__gte=6
    ).exclude(playType__in=[5, 6, 7, 8, 9, 10, 11, 12])  # Exclude PAT and 2PT conversions
    
    for play in offensive_tds:
        td = createTouchdownDict(play, match, team, opponent, isHome, 'Offensive')
        touchdowns.append(td)
    
    # Defensive/Special Teams TDs
    # For defensive TDs, the teamOnOffense is the OPPONENT (they had the ball)
    # and offenseScored should be False (because the DEFENSE scored)
    defensive_scoring_plays = [16, 19, 20, 21, 25, 27, 41]
    
    defensive_tds = playByPlay.objects.filter(
        nflMatch=match,
        teamOnOffense=opponent,  # OPPONENT had the ball
        scoringPlay=True,
        offenseScored=False,  # But DEFENSE scored
        playType__in=defensive_scoring_plays
    )
    
    for play in defensive_tds:
        td = createTouchdownDict(play, match, team, opponent, isHome, 'Defensive')
        touchdowns.append(td)
    
    # For return TDs
    punt_return_td_drives = driveOfPlay.objects.filter(
        nflMatch=match,
        teamOnOffense=opponent,
        driveResult__in=[21]  # PUNT RETURN TD
    )
    kickoff_return_td_drives = driveOfPlay.objects.filter(
        nflMatch=match,
        teamOnOffense=opponent,
        driveResult__in=[1],  # PUNT RETURN TD
        numberOffensivePlays=0
    )
    return_td_drives = []
    return_td_drives.extend(punt_return_td_drives)
    return_td_drives.extend(kickoff_return_td_drives)

    
    for drive in return_td_drives:
        # Find the scoring play in this drive
        scoring_play = playByPlay.objects.filter(
            driveOfPlay=drive,
            scoringPlay=True
        ).first()
        
        if scoring_play:
            td = createTouchdownDict(scoring_play, match, team, opponent, isHome, 'Return')
            touchdowns.append(td)
    
    all_scoring_plays = playByPlay.objects.filter(
        nflMatch=match,
        scoringPlay=True,
        pointsScored__gte=6
    ).exclude(playType__in=[5, 6, 7, 8, 9, 10, 11, 12])

    print(f"\n=== All scoring plays for {team.abbreviation} vs {opponent.abbreviation} ===")
    for play in all_scoring_plays:
        print(f"Play {play.espnId}: Type={play.playType}, TeamOnOffense={play.teamOnOffense.abbreviation}, "
            f"OffenseScored={play.offenseScored}, Points={play.pointsScored}")

    print(f"\n=== All TDs for {team.abbreviation} vs {opponent.abbreviation} ===")
    for play in touchdowns:
        print(f"Play {play['espnId']}: Type={play['playType']}, TD Type={play['tdType']}, TeamOnOffense={play['teamOnOffense']}, "
            f"Off_Scored={play['offenseScored']}, Points={play['pointsScored']}, Desc={play['description']}")
    
    return touchdowns

def createTouchdownDict(play, match, team, opponent, isHome, td_type):
    """
    Create a standardized touchdown dictionary
    """
    play_url = f'http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/{match.espnId}/competitions/{match.espnId}/plays/{play.espnId}?lang=en&region=us'
    
    td = {
        'url': play_url,
        'week': match.weekOfSeason,
        'date': match.datePlayed,
        'espnId': play.espnId,
        'team': team.abbreviation,
        'opponent': opponent.abbreviation,
        'homeAway': 'Home' if isHome else 'Away',
        'teamOnOffense': play.teamOnOffense.abbreviation,
        'offenseScored': play.offenseScored,
        'quarter': play.quarter,
        'time': play.displayClockTime,
        'secondsRemainingInPeriod': play.secondsRemainingInPeriod,
        'playType': play.get_playType_display(),
        'tdType': td_type,  # 'Offensive', 'Defensive', or 'Return'
        'description': play.playDescription[:200] if play.playDescription else 'N/A',
        'yardsOnPlay': play.yardsOnPlay,
        'pointsScored': play.pointsScored,
        'down': play.playDown,
        'scorer': None,
        'scorerPosition': None,
        'passer': None,
    }
    
    # Get scorer information based on TD type
    if td_type == 'Offensive':
        # Check for rushing TD
        rusher = rusherStatSplit.objects.filter(play=play, rushingTdScored=True).first()
        if rusher:
            td['scorer'] = rusher.player.name
            td['scorerPosition'] = rusher.player.get_playerPosition_display()
        
        # Check for receiving TD
        receiver = receiverStatSplit.objects.filter(play=play, receivingTdScored=True).first()
        if receiver:
            td['scorer'] = receiver.player.name
            td['scorerPosition'] = receiver.player.get_playerPosition_display()
            
            # Get the passer
            passer = passerStatSplit.objects.filter(play=play, passingTdScored=True).first()
            if passer:
                td['passer'] = passer.player.name
    
    elif td_type in ['Defensive', 'Return']:
        # Check for returner
        returner = returnerStatSplit.objects.filter(play=play).first()
        if returner:
            td['scorer'] = returner.player.name
            if play.playType == 24 or play.playType == 26:
                td['scorerPosition'] = "ST"
            else:
                td['scorerPosition'] = returner.player.get_playerPosition_display()
    
    # Fallback to description parsing
    if not td['scorer'] and play.playDescription:
        td['scorer'] = extractPlayerFromDescription(play.playDescription, 'touchdown')
    
    return td

def calculatePlayerTouchdowns(touchdown_list):
    """
    Calculate touchdown statistics by player
    """
    playerTouchdowns = {}
    
    for td in touchdown_list:
        if td['scorer'] and td['scorer'] != 'Unknown':
            if td['scorer'] not in playerTouchdowns:
                playerTouchdowns[td['scorer']] = {
                    'rushing': 0,
                    'receiving': 0,
                    'defensive': 0,
                    'return': 0,
                    'total': 0,
                    'position': td.get('scorerPosition', '-')
                }
            
            if td['tdType'] == 'Offensive':
                if 'RUSH' in td['playType']:
                    playerTouchdowns[td['scorer']]['rushing'] += 1
                elif 'PASS' in td['playType']:
                    playerTouchdowns[td['scorer']]['receiving'] += 1
            elif td['tdType'] == 'Defensive':
                playerTouchdowns[td['scorer']]['defensive'] += 1
            elif td['tdType'] == 'Return':
                playerTouchdowns[td['scorer']]['return'] += 1
            
            playerTouchdowns[td['scorer']]['total'] += 1
    
    # Sort by total touchdowns
    return sorted(playerTouchdowns.items(), key=lambda x: x[1]['total'], reverse=True)

def calculateTouchdownsByPosition(touchdown_list):
    """
    Calculate touchdown statistics by position group
    """
    positionTouchdowns = {}
    
    # Define position groups
    position_groups = {
        'QB': 'QB',
        'RB': 'RB', 'FB': 'RB',
        'WR': 'WR',
        'TE': 'TE',
        'OL': 'OL', 'C': 'OL', 'G': 'OL', 'T': 'OL',
        'DL': 'DL', 'DE': 'DL', 'DT': 'DL', 'NT': 'DL',
        'LB': 'LB', 'ILB': 'LB', 'OLB': 'LB', 'MLB': 'LB',
        'CB': 'CB', 'DB': 'CB',
        'S': 'S', 'SS': 'S', 'FS': 'S',
        'ST': 'ST',  # Special Teams
        'K': 'K',
        'P': 'P'
    }
    
    for td in touchdown_list:
        if td['scorer'] and td['scorer'] != 'Unknown':
            position = td.get('scorerPosition', '-')
            
            # Map to position group
            pos_group = position_groups.get(position, position)
            
            if pos_group not in positionTouchdowns:
                positionTouchdowns[pos_group] = {
                    'rushing': 0,
                    'receiving': 0,
                    'defensive': 0,
                    'return': 0,
                    'total': 0
                }
            
            if td['tdType'] == 'Offensive':
                if 'RUSH' in td['playType']:
                    positionTouchdowns[pos_group]['rushing'] += 1
                elif 'PASS' in td['playType']:
                    positionTouchdowns[pos_group]['receiving'] += 1
            elif td['tdType'] == 'Defensive':
                positionTouchdowns[pos_group]['defensive'] += 1
            elif td['tdType'] == 'Return':
                positionTouchdowns[pos_group]['return'] += 1
            
            positionTouchdowns[pos_group]['total'] += 1
    
    # Sort by total touchdowns
    return sorted(positionTouchdowns.items(), key=lambda x: x[1]['total'], reverse=True)

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
    for y in range(2026, 2016, -1):
        yearsOnPage.append(y)
    
    return yearsOnPage        
    



