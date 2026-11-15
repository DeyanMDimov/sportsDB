from nfl_db.crudLogic import runStatSplitRepair, BOX_SCORE_YARDS_TOLERANCE
from django.core.management.base import BaseCommand


def shortened(text, length = 110):
    text = " ".join(text.split())
    return text if len(text) <= length else text[:length - 3] + "..."


class Command(BaseCommand):
    help = ('Repairs the stored passer, rusher, receiver and returner stat splits: removes repeat rows for the '
            'same player on the same play, sets the yards columns to the yards gained on the play (some seasons '
            'hold the player\'s whole-game total on every row), and adds the passer rows interceptions never got. '
            'Only reports what it would change unless --apply is given, e.g. '
            'manage.py repairPlayStatSplitsCommand --season 2025, then the same with --apply.')

    def add_arguments(self, parser):
        parser.add_argument('--season', type = int, default = None, help = 'Only repair this year of season')
        parser.add_argument('--apply', action = 'store_true', help = 'Make the changes. Without it the command only reports.')

    def handle(self, *args, **options):
        report = runStatSplitRepair(applyChanges = options['apply'], seasonYear = options['season'])
        applied = report['applied']

        seasons = set()
        for entry in report['duplicates'] + report['yards']:
            seasons.update(entry['bySeason'])
        seasons.update(report['interceptions']['bySeason'])
        seasons.update(report['interceptions']['withoutPasserBySeason'])
        seasons = sorted(seasons)

        def printCounts(rows):
            labelWidth = max([len(label) for label, bySeason, total in rows] + [10])
            print("  " + "".ljust(labelWidth) + "".join(str(season).rjust(8) for season in seasons) + "   total")
            for label, bySeason, total in rows:
                print("  " + label.ljust(labelWidth) + "".join(str(bySeason.get(season, 0)).rjust(8) for season in seasons) + str(total).rjust(8))

        print("")
        print("1. Repeat rows for the same player on the same play - " + ("deleted" if applied else "to delete") + ", keeping the newest")
        printCounts([(entry['label'], entry['bySeason'], entry['total']) for entry in report['duplicates']])
        for entry in report['duplicates']:
            for sample in entry['samples'][:2]:
                print("    e.g. " + entry['label'] + ", " + str(sample['season']) + " wk " + str(sample['week']) + ", "
                      + sample['player'] + ": " + shortened(sample['play'], 80))

        print("")
        print("2. Yards columns that aren't the yards gained on the play - " + ("corrected" if applied else "to correct"))
        printCounts([(entry['label'], entry['bySeason'], entry['total']) for entry in report['yards']])
        for entry in report['yards']:
            for sample in entry['samples']:
                print("    e.g. " + entry['field'] + " " + str(sample['stored']) + " -> " + str(sample['credited']) + ", "
                      + str(sample['season']) + " wk " + str(sample['week']) + ", " + sample['player'] + ": " + shortened(sample['play'], 80))

        interceptions = report['interceptions']
        print("")
        print("3. Interceptions with no passer row")
        printCounts([
            ("passer rows added" if applied else "passer rows to add", interceptions['bySeason'], interceptions['total']),
            ("no passer named", interceptions['withoutPasserBySeason'], interceptions['withoutPasserTotal']),
        ])
        for sample in interceptions['samples']:
            print("    e.g. " + str(sample['season']) + " wk " + str(sample['week']) + ", " + sample['player'] + ": " + shortened(sample['play'], 90))
        for sample in interceptions['withoutPasserSamples'][:3]:
            print("    no passer named, " + str(sample['season']) + " wk " + str(sample['week']) + ": " + shortened(sample['play'], 90))
        if interceptions['withoutPasserTotal'] > 0:
            print("    The plays with no passer named can be fetched from ESPN with backfillPlayStatSplitsCommand.")

        print("")
        print("Passer rows against the box score " + ("now" if applied else "once repaired")
              + " (team-games whose passingYards add up to within " + str(BOX_SCORE_YARDS_TOLERANCE) + " yards of totalPassingYards)")
        for seasonCheck in report['boxScoreCheck']:
            print("  " + str(seasonCheck['season']) + ": " + str(seasonCheck['close']) + " of " + str(seasonCheck['teamGames'])
                  + " (" + str(seasonCheck['exact']) + " exact, largest gap " + str(seasonCheck['largestGap']) + " yards)")

        print("")
        if applied:
            print("Done. " + str(report['totalChanges']) + " rows deleted, corrected or added.")
        elif report['totalChanges'] == 0:
            print("Nothing to repair.")
        else:
            print("Dry run: nothing was changed. " + str(report['totalChanges'])
                  + " rows would be deleted, corrected or added - run again with --apply to make the changes.")
