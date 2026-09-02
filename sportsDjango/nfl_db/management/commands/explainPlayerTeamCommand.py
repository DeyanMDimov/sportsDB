from nfl_db.models import player, nflTeam, playerWeekStatus, passerStatSplit, rusherStatSplit, receiverStatSplit, returnerStatSplit
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Says why a player is listed under a team, e.g. manage.py explainPlayerTeamCommand "Romeo Doubs" CHI'

    def add_arguments(self, parser):
        parser.add_argument('playerName')
        parser.add_argument('teamAbbreviation')
        parser.add_argument('--season', default = None)

    def handle(self, *args, **options):
        try:
            playerObj = player.objects.filter(name__iexact = options['playerName']).first()
            if playerObj == None:
                playerObj = player.objects.filter(name__icontains = options['playerName']).first()
            if playerObj == None:
                print("No player matching " + options['playerName'])
                return

            team = nflTeam.objects.filter(abbreviation__iexact = options['teamAbbreviation']).first()
            if team == None:
                print("No team " + options['teamAbbreviation'])
                return

            print("Player: " + playerObj.name + "  (espnId " + str(playerObj.espnId) + ", id " + str(playerObj.id) + ")")
            print("player.team FK: " + (playerObj.team.abbreviation if playerObj.team else "none"))
            print("Asking about team: " + team.abbreviation)
            print("")

            weekStatuses = playerWeekStatus.objects.filter(player = playerObj, team = team)
            if options['season'] != None:
                weekStatuses = weekStatuses.filter(yearOfSeason = int(options['season']))

            print("playerWeekStatus rows for " + team.abbreviation + ": " + str(weekStatuses.count()))
            for weekStatus in weekStatuses.order_by('yearOfSeason', 'weekOfSeason', 'reportDate')[:40]:
                print("   " + str(weekStatus.yearOfSeason) + " wk " + str(weekStatus.weekOfSeason)
                      + "  status " + str(weekStatus.playerStatus)
                      + "  date " + str(weekStatus.reportDate)
                      + "  (row id " + str(weekStatus.id) + ")")
            print("")

            for splitModel in [passerStatSplit, rusherStatSplit, receiverStatSplit, returnerStatSplit]:
                splits = splitModel.objects.filter(player = playerObj, play__teamOnOffense = team)
                if options['season'] != None:
                    splits = splits.filter(play__nflMatch__yearOfSeason = int(options['season']))

                print(splitModel.__name__ + " rows on " + team.abbreviation + " plays: " + str(splits.count()))
                for split in splits.select_related('play', 'play__nflMatch')[:5]:
                    print("   " + str(split.play.nflMatch.yearOfSeason) + " wk " + str(split.play.nflMatch.weekOfSeason)
                          + "  " + (split.play.playDescription or "")[:90])

            print("")
            print("The Performances dropdown lists a player for a team when either the")
            print("playerWeekStatus count or one of the offensive split counts above is not zero.")

        except Exception as e:
            raise CommandError(repr(e))
