from nfl_db.models import nflMatch, playByPlay
from django.core.management.base import BaseCommand
from django.db.models import Q

import requests
import time as clock


def fetchPlayTextsForMatch(matchEspnId):
    """
    Pull every play for a match off the ESPN core API and return a map of
    play espnId (as string) -> play text.
    """
    playTexts = {}
    pageIndex = 1
    pageCount = 1

    while pageIndex <= pageCount:
        playsUrl = ('http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/'
                    + str(matchEspnId) + '/competitions/' + str(matchEspnId)
                    + '/plays?limit=300&page=' + str(pageIndex))

        response = requests.get(playsUrl, timeout = 30)
        if response.status_code != 200:
            print("   ESPN returned " + str(response.status_code) + " for page " + str(pageIndex))
            return playTexts

        pageOfPlays = response.json()
        pageCount = pageOfPlays.get('pageCount', 1)

        for individualPlay in pageOfPlays.get('items', []):
            if 'text' in individualPlay and individualPlay['text'] != None:
                playTexts[str(individualPlay['id'])] = individualPlay['text']

        pageIndex += 1

    return playTexts


class Command(BaseCommand):
    help = ('Backfills playDescription on plays that are missing it, e.g. '
            'manage.py backfillPlayDescriptionsCommand --season 2023')

    def add_arguments(self, parser):
        parser.add_argument('--season', default = None, help = 'Only backfill this year of season')
        parser.add_argument('--match', default = None, help = 'Only backfill this match espnId')
        parser.add_argument('--dryRun', action = 'store_true', help = 'Report what would change without saving')

    def handle(self, *args, **options):
        missingPlays = playByPlay.objects.filter(
            Q(playDescription__isnull = True) | Q(playDescription = "")
        ).exclude(espnId__isnull = True)

        if options['season'] != None:
            missingPlays = missingPlays.filter(nflMatch__yearOfSeason = int(options['season']))
        if options['match'] != None:
            missingPlays = missingPlays.filter(nflMatch__espnId = int(options['match']))

        matchEspnIds = sorted(set(missingPlays.values_list('nflMatch__espnId', flat = True)))

        print("Plays missing a description: " + str(missingPlays.count())
              + " across " + str(len(matchEspnIds)) + " matches")

        totalUpdated = 0
        totalUnmatched = 0

        for matchEspnId in matchEspnIds:
            matchData = nflMatch.objects.get(espnId = matchEspnId)
            playsForMatch = missingPlays.filter(nflMatch = matchData)

            print(str(matchData.yearOfSeason) + " wk " + str(matchData.weekOfSeason)
                  + " - match " + str(matchEspnId) + " - " + str(playsForMatch.count()) + " plays")

            try:
                playTexts = fetchPlayTextsForMatch(matchEspnId)
            except Exception as e:
                print("   Failed to fetch plays: " + str(e))
                continue

            if len(playTexts) == 0:
                print("   ESPN returned no play text for this match")
                continue

            playsToUpdate = []
            for play in playsForMatch:
                playText = playTexts.get(str(play.espnId))
                if playText == None:
                    totalUnmatched += 1
                    continue
                play.playDescription = playText[:800]
                playsToUpdate.append(play)

            if options['dryRun']:
                print("   Would update " + str(len(playsToUpdate)) + " plays")
            else:
                playByPlay.objects.bulk_update(playsToUpdate, ['playDescription'], batch_size = 500)
                print("   Updated " + str(len(playsToUpdate)) + " plays")

            totalUpdated += len(playsToUpdate)
            clock.sleep(0.5)

        print("")
        print("Done. " + ("Would update " if options['dryRun'] else "Updated ")
              + str(totalUpdated) + " plays. " + str(totalUnmatched) + " plays had no matching ESPN text.")
