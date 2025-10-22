from nfl_db import crudLogic, views
from django.core.management.base import BaseCommand, CommandError
from django.test import RequestFactory

class Command(BaseCommand):
    help = 'Command to pull odds during week.'

    def add_argument(self, parser):
        pass
        
    def handle(self, *args, **options):
        try:
           factory = RequestFactory()
           request = factory.get('/players/?season=2025&teamName=ALL')
           views.getPlayers(request)
           print("Done - Pulled players.")
            
        except Exception as e:
            CommandError(repr(e))
            print("Done")