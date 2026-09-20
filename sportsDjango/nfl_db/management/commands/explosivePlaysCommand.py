from nfl_db.models import teamMatchPerformance
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Recalculates totalExplosivePlays (rush 10+ plus pass 25+) on stored team performances, e.g. manage.py explosivePlaysCommand --apply --season 2025. Without --apply it only reports what would change.'

    def add_arguments(self, parser):
        parser.add_argument('--season', type = int, default = None)
        parser.add_argument('--apply', action = 'store_true')

    def handle(self, *args, **options):
        performances = teamMatchPerformance.objects.all()
        if options['season'] != None:
            performances = performances.filter(yearOfSeason = options['season'])

        # Rows missing a component can't be totalled; they need the match re-pulled.
        missingComponents = performances.filter(rushingPlaysTenPlus = None) | performances.filter(passPlaysTwentyFivePlus = None)
        countable = performances.exclude(rushingPlaysTenPlus = None).exclude(passPlaysTwentyFivePlus = None)

        rowsToUpdate = []
        for performance in countable:
            explosivePlays = performance.rushingPlaysTenPlus + performance.passPlaysTwentyFivePlus
            if performance.totalExplosivePlays != explosivePlays:
                performance.totalExplosivePlays = explosivePlays
                rowsToUpdate.append(performance)

        # A leftover total on a row we can't total came from the old first-page count,
        # which undercounted, so clear it rather than leave a wrong number on the page.
        staleTotals = missingComponents.exclude(totalExplosivePlays = None)

        print(str(countable.count()) + " performances can be totalled, " + str(len(rowsToUpdate)) + " need updating.")
        print(str(missingComponents.count()) + " performances are missing a component stat and were skipped, "
              + str(staleTotals.count()) + " of those still carry an old total to clear.")

        if options['apply']:
            teamMatchPerformance.objects.bulk_update(rowsToUpdate, ['totalExplosivePlays'], batch_size = 500)
            clearedCount = staleTotals.update(totalExplosivePlays = None)
            print("Updated " + str(len(rowsToUpdate)) + " performances and cleared " + str(clearedCount) + " old totals.")
        else:
            print("Dry run; pass --apply to save.")
