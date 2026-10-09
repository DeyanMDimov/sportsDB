from nfl_db import crudLogic
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Command to pull player statuses and injury reports'

    def add_arguments(self, parser):
        parser.add_argument('--now', action = 'store_true',
                            help = 'Pull right away instead of only at the scheduled times')

    def handle(self, *args, **options):
        try:
           crudLogic.scheduledInjuryPull(force = options['now'])
           print("Done")

        except Exception as e:
            CommandError(repr(e))
            print("Done")