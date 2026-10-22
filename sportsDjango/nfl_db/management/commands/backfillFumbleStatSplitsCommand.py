from nfl_db.models import nflMatch, playByPlay, passerStatSplit, rusherStatSplit, receiverStatSplit
from nfl_db.crudLogic import FUMBLE_PLAY_TYPES, processPlayParticipants
from django.core.management.base import BaseCommand

import requests
import time as clock


OFFENSIVE_SPLIT_MODELS = [passerStatSplit, rusherStatSplit, receiverStatSplit]


def fetchPlayParticipantsForMatch(matchEspnId):
    """
    Pull every play for a match off the ESPN core API and return a map of
    play espnId (as string) -> its participants.
    """
    playParticipants = {}
    pageIndex = 1
    pageCount = 1

    while pageIndex <= pageCount:
        playsUrl = ('http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/'
                    + str(matchEspnId) + '/competitions/' + str(matchEspnId)
                    + '/plays?limit=300&page=' + str(pageIndex))

        response = requests.get(playsUrl, timeout = 30)
        if response.status_code != 200:
            print("   ESPN returned " + str(response.status_code) + " for page " + str(pageIndex))
            return playParticipants

        pageOfPlays = response.json()
        pageCount = pageOfPlays.get('pageCount', 1)

        for individualPlay in pageOfPlays.get('items', []):
            if 'participants' in individualPlay:
                playParticipants[str(individualPlay['id'])] = individualPlay['participants']

        pageIndex += 1

    return playParticipants


def offensiveSplitCount(plays):
    return sum(splitModel.objects.filter(play__in = plays).count() for splitModel in OFFENSIVE_SPLIT_MODELS)


class Command(BaseCommand):
    help = ('Writes the passer, rusher and receiver stat splits that plays ending in a fumble never got '
            '(ESPN types them by the recovery, so the catch, carry or sack before it went uncounted), e.g. '
            'manage.py backfillFumbleStatSplitsCommand --season 2026')

    def add_arguments(self, parser):
        parser.add_argument('--season', default = None, help = 'Only backfill this year of season')
        parser.add_argument('--match', default = None, help = 'Only backfill this match espnId')
        parser.add_argument('--dryRun', action = 'store_true', help = 'Report what would change without saving')

    def handle(self, *args, **options):
        fumblePlays = playByPlay.objects.filter(playType__in = FUMBLE_PLAY_TYPES).exclude(espnId__isnull = True)

        if options['season'] != None:
            fumblePlays = fumblePlays.filter(nflMatch__yearOfSeason = int(options['season']))
        if options['match'] != None:
            fumblePlays = fumblePlays.filter(nflMatch__espnId = int(options['match']))

        playIdsWithSplits = set()
        for splitModel in OFFENSIVE_SPLIT_MODELS:
            playIdsWithSplits.update(splitModel.objects.filter(play__in = fumblePlays).values_list('play_id', flat = True))
        playsToFill = fumblePlays.exclude(id__in = playIdsWithSplits)

        matchEspnIds = sorted(set(playsToFill.values_list('nflMatch__espnId', flat = True)))

        print("Fumble plays without passer/rusher/receiver splits: " + str(playsToFill.count())
              + " across " + str(len(matchEspnIds)) + " matches")

        totalPlaysFilled = 0
        totalSplitsWritten = 0
        totalUnmatched = 0

        for matchEspnId in matchEspnIds:
            matchData = nflMatch.objects.get(espnId = matchEspnId)
            playsForMatch = list(playsToFill.filter(nflMatch = matchData))

            print(str(matchData.yearOfSeason) + " wk " + str(matchData.weekOfSeason)
                  + " - match " + str(matchEspnId) + " - " + str(len(playsForMatch)) + " plays")

            try:
                playParticipants = fetchPlayParticipantsForMatch(matchEspnId)
            except Exception as e:
                print("   Failed to fetch plays: " + str(e))
                continue

            if len(playParticipants) == 0:
                print("   ESPN returned no play participants for this match")
                continue

            splitsBefore = offensiveSplitCount(playsForMatch)
            playsFilled = 0
            for play in playsForMatch:
                participants = playParticipants.get(str(play.espnId))
                if participants == None:
                    totalUnmatched += 1
                    continue
                if not any(participant.get('type', '').lower() in ['rusher', 'passer', 'receiver'] for participant in participants):
                    continue
                playsFilled += 1
                if not options['dryRun']:
                    processPlayParticipants(play, participants)

            if options['dryRun']:
                print("   Would fill " + str(playsFilled) + " plays")
            else:
                splitsWritten = offensiveSplitCount(playsForMatch) - splitsBefore
                print("   Filled " + str(playsFilled) + " plays with " + str(splitsWritten) + " splits")
                totalSplitsWritten += splitsWritten

            totalPlaysFilled += playsFilled
            clock.sleep(0.5)

        print("")
        print("Done. " + ("Would fill " if options['dryRun'] else "Filled ")
              + str(totalPlaysFilled) + " plays"
              + ("" if options['dryRun'] else " with " + str(totalSplitsWritten) + " splits")
              + ". " + str(totalUnmatched) + " plays had no matching ESPN play.")
