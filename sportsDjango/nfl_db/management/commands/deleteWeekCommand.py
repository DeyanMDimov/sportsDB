from nfl_db.models import nflTeam, nflMatch, teamMatchPerformance, teamMatchRoster, driveOfPlay, playByPlay
from nfl_db.models import playerMatchOffense, playerMatchDefense, playerWeekStatus, nflMatchOdds, bettingModelResult
from nfl_db.models import passerStatSplit, rusherStatSplit, receiverStatSplit, returnerStatSplit
from nfl_db.models import kickerFgStatSplit, punterStatSplit, defenderStatSplit, penalizedStatSplit
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q


statSplitModels = [
    ("passerStatSplit", passerStatSplit),
    ("rusherStatSplit", rusherStatSplit),
    ("receiverStatSplit", receiverStatSplit),
    ("returnerStatSplit", returnerStatSplit),
    ("kickerFgStatSplit", kickerFgStatSplit),
    ("punterStatSplit", punterStatSplit),
    ("defenderStatSplit", defenderStatSplit),
    ("penalizedStatSplit", penalizedStatSplit),
]


class Command(BaseCommand):
    help = ('Deletes every stored row for one week of one season so it can be pulled again, e.g. '
            'manage.py deleteWeekCommand --season 2026 --week 2 --confirm. '
            'Without --confirm it only reports what it would delete.')

    def add_arguments(self, parser):
        parser.add_argument('--season', type = int, required = True, help = 'yearOfSeason to clear')
        parser.add_argument('--week', type = int, required = True, help = 'weekOfSeason to clear (19-22 are the playoff weeks)')
        parser.add_argument('--confirm', action = 'store_true', help = 'Actually delete. Without it the command only reports.')
        parser.add_argument('--keepMatches', action = 'store_true',
                            help = 'Keep the nflMatch rows themselves and only clear their stats, plays, odds and model results')
        parser.add_argument('--keepAvailability', action = 'store_true',
                            help = 'Keep the playerWeekStatus injury rows for the week')
        parser.add_argument('--team', default = None, help = 'Limit to one team abbreviation, e.g. --team CHI')

    def handle(self, *args, **options):
        seasonYear = options['season']
        seasonWeek = options['week']

        if seasonWeek < -4 or seasonWeek > 22:
            raise CommandError("weekOfSeason must be between -4 and 22.")

        teamFilter = None
        if options['team'] != None:
            teamFilter = nflTeam.objects.filter(abbreviation = options['team'].strip().upper()).first()
            if teamFilter == None:
                raise CommandError("No team with abbreviation " + options['team'])

        matches = nflMatch.objects.filter(yearOfSeason = seasonYear, weekOfSeason = seasonWeek)
        if teamFilter != None:
            matches = matches.filter(Q(homeTeamEspnId = teamFilter.espnId) | Q(awayTeamEspnId = teamFilter.espnId))

        matchIds = list(matches.values_list('id', flat = True))
        matchEspnIds = list(matches.values_list('espnId', flat = True))

        # teamMatchPerformance is a many to many to nflMatch, so deleting the match only clears the
        # join row and leaves the performance behind. It carries its own week and year, so catch both
        # the rows tied to these matches and any stragglers stamped with this week.
        performances = teamMatchPerformance.objects.filter(
            Q(matchEspnId__in = matchEspnIds) | Q(yearOfSeason = seasonYear, weekOfSeason = seasonWeek)
        )
        if teamFilter != None:
            performances = performances.filter(teamEspnId = teamFilter.espnId)

        # playerWeekStatus has no match foreign key at all, only the week and year.
        weekStatuses = playerWeekStatus.objects.filter(yearOfSeason = seasonYear, weekOfSeason = seasonWeek)
        if teamFilter != None:
            weekStatuses = weekStatuses.filter(team = teamFilter)

        rowCounts = [
            ("nflMatch", matches.count()),
            ("teamMatchPerformance", performances.count()),
            ("teamMatchRoster", teamMatchRoster.objects.filter(nflMatch__in = matchIds).count()),
            ("driveOfPlay", driveOfPlay.objects.filter(nflMatch__in = matchIds).count()),
            ("playByPlay", playByPlay.objects.filter(nflMatch__in = matchIds).count()),
            ("playerMatchOffense", playerMatchOffense.objects.filter(nflMatch__in = matchIds).count()),
            ("playerMatchDefense", playerMatchDefense.objects.filter(nflMatch__in = matchIds).count()),
            ("nflMatchOdds", nflMatchOdds.objects.filter(nflMatch__in = matchIds).count()),
            ("bettingModelResult", bettingModelResult.objects.filter(nflMatch__in = matchIds).count()),
            ("playerWeekStatus", weekStatuses.count()),
        ]
        for splitName, splitModel in statSplitModels:
            rowCounts.append((splitName, splitModel.objects.filter(play__nflMatch__in = matchIds).count()))

        print("")
        print(str(seasonYear) + " week " + str(seasonWeek)
              + (" for " + teamFilter.abbreviation if teamFilter != None else "")
              + " currently holds:")
        for rowName, rowCount in rowCounts:
            if rowCount > 0:
                print("   " + rowName + ": " + str(rowCount))
        if sum(rowCount for rowName, rowCount in rowCounts) == 0:
            print("   nothing. There is no data stored for this week.")
            return

        if options['keepMatches']:
            print("   (--keepMatches: the " + str(len(matchIds))
                  + (" nflMatch row stays" if len(matchIds) == 1 else " nflMatch rows stay")
                  + ", their child rows go)")
        if options['keepAvailability']:
            print("   (--keepAvailability: the playerWeekStatus rows stay)")

        if not options['confirm']:
            print("")
            print("Nothing deleted. Re-run with --confirm to delete.")
            return

        deletedByModel = {}

        with transaction.atomic():
            # These two are not reachable by cascade, so they go first and by hand.
            deletedCount, perModel = performances.delete()
            mergeDeleteCounts(deletedByModel, perModel)

            if not options['keepAvailability']:
                deletedCount, perModel = weekStatuses.delete()
                mergeDeleteCounts(deletedByModel, perModel)

            if options['keepMatches']:
                for childModel in [teamMatchRoster, driveOfPlay, playerMatchOffense, playerMatchDefense,
                                   nflMatchOdds, bettingModelResult]:
                    deletedCount, perModel = childModel.objects.filter(nflMatch__in = matchIds).delete()
                    mergeDeleteCounts(deletedByModel, perModel)
                deletedCount, perModel = playByPlay.objects.filter(nflMatch__in = matchIds).delete()
                mergeDeleteCounts(deletedByModel, perModel)
            else:
                # Everything else hangs off nflMatch with on_delete = CASCADE.
                deletedCount, perModel = matches.delete()
                mergeDeleteCounts(deletedByModel, perModel)

        print("")
        if len(deletedByModel) == 0:
            print("Deleted nothing.")
        else:
            print("Deleted:")
            for modelLabel in sorted(deletedByModel.keys()):
                print("   " + modelLabel + ": " + str(deletedByModel[modelLabel]))

        print("")
        print("Pull it again with: /pulldata?season=" + str(seasonYear)
              + "&startWeek=" + str(seasonWeek) + "&endWeek=" + str(seasonWeek))
        if not options['keepAvailability']:
            print("Injury rows were removed too, so re-run the availability pull for the week as well.")


def mergeDeleteCounts(runningTotals, perModelCounts):
    for modelLabel in perModelCounts:
        if perModelCounts[modelLabel] == 0:
            continue
        runningTotals[modelLabel] = runningTotals.get(modelLabel, 0) + perModelCounts[modelLabel]
