from nfl_db.models import playByPlay
from django.core.management.base import BaseCommand
from collections import Counter


class Command(BaseCommand):
    help = ('Fills in playDirection ("left guard", "deep middle", ...) from each play\'s description, e.g. '
            'manage.py backfillPlayDirectionsCommand --season 2025')

    def add_arguments(self, parser):
        parser.add_argument('--season', default = None, help = 'Only backfill this year of season')
        parser.add_argument('--dryRun', action = 'store_true', help = 'Report what would change without saving')

    def handle(self, *args, **options):
        plays = playByPlay.objects.exclude(playType__in = playByPlay.directionlessPlayTypes)
        if options['season'] != None:
            plays = plays.filter(nflMatch__yearOfSeason = int(options['season']))

        print("Plays to check: " + str(plays.count()))

        directionLabels = dict(playByPlay.playDirections)
        directionsFound = Counter()
        playsToUpdate = []
        for play in plays.only('id', 'playType', 'playDescription', 'playDirection').iterator(chunk_size = 2000):
            direction = playByPlay.directionFromDescription(play.playType, play.playDescription)
            directionsFound[directionLabels.get(direction, "(none)")] += 1
            if direction != play.playDirection:
                play.playDirection = direction
                playsToUpdate.append(play)

        for label, count in directionsFound.most_common():
            print("   " + label + ": " + str(count))

        if options['dryRun']:
            print("Would update " + str(len(playsToUpdate)) + " plays")
        else:
            playByPlay.objects.bulk_update(playsToUpdate, ['playDirection'], batch_size = 1000)
            print("Updated " + str(len(playsToUpdate)) + " plays")
