from nfl_db import crudLogic, propLines
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = ('Pulls sportsbook player prop lines (passing, rushing, receiving yards and so on) from ESPN into '
            'playerPropLine. manage.py propLinesCommand pulls the current week; '
            'manage.py propLinesCommand --season 2024 2025 backfills whole seasons; '
            'manage.py propLinesCommand --season 2026 --week 9 10 pulls particular weeks. '
            'Safe to re-run: each pull overwrites the stored line with ESPN\'s latest, so a finished game keeps its closing line.')

    def add_arguments(self, parser):
        parser.add_argument('--season', type = int, nargs = '+',
                            help = 'yearOfSeason(s) to pull. Defaults to the current season.')
        parser.add_argument('--week', type = int, nargs = '+',
                            help = 'weekOfSeason(s) to pull (playoffs are 19 and up). Defaults to the current week '
                                   'when no season is given, and to the whole season when one is.')

    def handle(self, *args, **options):
        seasons = options['season']
        weeks = options['week']
        if not seasons:
            seasons = [crudLogic.currentSeasonYear()]
            if not weeks:
                week = propLines.currentWeek(seasons[0])
                if week == None:
                    raise CommandError("No games left to play in " + str(seasons[0]) + "; pass --season and --week to pull past games.")
                weeks = [week]

        for seasonYear in seasons:
            try:
                propLines.printPropLineSummary(propLines.pullPropLines(seasonYear, weeks))
            except Exception as e:
                raise CommandError("Prop line pull for " + str(seasonYear) + " failed: " + repr(e))
