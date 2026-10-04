from nfl_db import crudLogic
from nfl_db.models import nflTeam
from django.core.management.base import BaseCommand, CommandError

class Command(BaseCommand):
    help = "Pulls every team's current roster from ESPN, moving players to the team they are on now."

    def add_argument(self, parser):
        pass
        
    def handle(self, *args, **options):
        try:
            # This used to send ?teamName=ALL to the players page, which has no
            # branch for it, so it never pulled anything.
            for team in nflTeam.objects.all().order_by('abbreviation'):
                roster, movedPlayers = crudLogic.refreshTeamRosterFromApi(team)
                print(team.abbreviation + ": " + str(len(roster)) + " players, " + str(len(movedPlayers)) + " moved here.")
                for move in movedPlayers:
                    print("   " + move['name'] + " (was " + move['fromTeam'] + ")")
            print("Done - Pulled players.")
            
        except Exception as e:
            raise CommandError(repr(e))
