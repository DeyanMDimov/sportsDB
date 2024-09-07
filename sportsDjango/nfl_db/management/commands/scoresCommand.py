from nfl_db import crudLogic
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Command to pull updated scores'

    def add_argument(self, parser):
        pass
        
    def handle(self, *args, **options):
        try:
           crudLogic.scheduledScorePull()
           print("Done. Ran Successfully")
            
        except Exception as e:
            CommandError(repr(e))
            print("Error: " + str(e))