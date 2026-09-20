from nfl_db.models import nflMatch, bettingModelResult
from nfl_db import businessLogic
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Precomputes stored betting model results, e.g. manage.py modelResultsCommand --season 2024 --model v1.5 --movingavg 5. Use --clear to delete stored results first.'

    def add_arguments(self, parser):
        parser.add_argument('--season', type = int, default = None)
        parser.add_argument('--model', default = None, choices = businessLogic.MODEL_VERSIONS)
        parser.add_argument('--movingavg', type = int, default = 5)
        parser.add_argument('--clear', action = 'store_true')

    def handle(self, *args, **options):
        storedResults = bettingModelResult.objects.all()
        if options['season'] != None:
            storedResults = storedResults.filter(yearOfSeason = options['season'])
        if options['model'] != None:
            storedResults = storedResults.filter(modelVersion = options['model'])

        if options['clear']:
            deletedCount, _ = storedResults.delete()
            print("Deleted " + str(deletedCount) + " stored model results.")

        if options['season'] == None:
            if not options['clear']:
                print("Pass --season to precompute results for a season.")
            return

        models = [options['model']] if options['model'] != None else ["v1", "v1.5"]
        seasonMatches = list(nflMatch.objects.filter(yearOfSeason = options['season'], completed = True).order_by('weekOfSeason'))

        for selectedModel in models:
            businessLogic.getModelResultsForMatches(seasonMatches, selectedModel, options['movingavg'])
            print("Stored " + selectedModel + " results for " + str(len(seasonMatches)) + " completed " + str(options['season']) + " matches.")
