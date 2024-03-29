from nfl_db import crudLogic
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = 'Command to pull odds during week.'

    def add_argument(self, parser):
        pass
        
    def handle(self, *args, **options):
        try:
           crudLogic.scheduledInjuryPull()
           print("Done")
            
        except Exception as e:
            CommandError(repr(e))
            print("Done")