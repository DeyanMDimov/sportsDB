from nfl_db import snapCounts
from django.core.management.base import BaseCommand, CommandError
from datetime import datetime


class Command(BaseCommand):
    help = ('Pulls player snap counts from the nflverse snap_counts release into playerMatchUsage, e.g. '
            'manage.py snapCountCommand, or manage.py snapCountCommand --season 2024 2025 to backfill. '
            'Safe to re-run: stored rows are only updated when the figures changed.')

    def add_arguments(self, parser):
        parser.add_argument('--season', type = int, nargs = '+',
                            help = 'yearOfSeason(s) to pull. Defaults to the current season.')

    def handle(self, *args, **options):
        seasons = options['season']
        if not seasons:
            today = datetime.now()
            seasons = [today.year if today.month > 4 else today.year - 1]

        for seasonYear in seasons:
            try:
                snapCounts.printSnapCountSummary(snapCounts.pullSnapCounts(seasonYear))
            except Exception as e:
                raise CommandError("Snap count pull for " + str(seasonYear) + " failed: " + repr(e))
