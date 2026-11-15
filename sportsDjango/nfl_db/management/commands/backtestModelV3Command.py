from nfl_db import bettingModelV3
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = ('Backtests betting model V3 against the stored book lines, predicting every week only from the games before it, '
            'e.g. manage.py backtestModelV3Command --from 2019 --to 2025. Nothing is written to the database.')

    def add_arguments(self, parser):
        parser.add_argument('--from', dest = 'firstSeason', type = int, default = 2019,
                            help = 'First season to include (default 2019, the first with a full previous season to rate teams on).')
        parser.add_argument('--to', dest = 'lastSeason', type = int, default = None, help = 'Last season to include (default: the latest).')
        parser.add_argument('--quarterbacks', default = "actual", choices = ["actual", "expected", "none"],
                            help = 'Who each team is rated with: "actual" is whoever took its first dropback (known by kickoff, the default), '
                                   '"expected" is whoever started its previous game, "none" leaves the quarterback adjustment out.')

    def handle(self, *args, **options):
        data = bettingModelV3.modelData(usePregameNews = False)
        predictionsByMode = {
            mode: bettingModelV3.backtestPredictions(options['firstSeason'], options['lastSeason'], mode, data)
            for mode in ("none", "expected", "actual")
        }
        predictions = predictionsByMode[options['quarterbacks']]
        if len(predictions) == 0:
            print("No completed games with book lines in that range.")
            return

        self.printQuarterbackComparison(predictionsByMode)
        print("The tables below rate each team with its " + options['quarterbacks'] + " quarterback.")

        minimumEdge = bettingModelV3.MINIMUM_EDGE_POINTS

        print()
        print("Average miss in points (lower is better). 'Bets' are games where the model was at least "
              + str(minimumEdge) + " point from the book.")
        print()
        print("{:<8}{:>6}  {:>12}{:>12}  {:>12}{:>12}  {:>20}{:>20}".format(
            "Season", "Games", "Model line", "Book line", "Model total", "Book total", "Line bets", "Total bets"))

        seasons = sorted(set(prediction.yearOfSeason for prediction in predictions))
        for season in seasons + ["All"]:
            seasonPredictions = predictions if season == "All" else [prediction for prediction in predictions if prediction.yearOfSeason == season]
            summary = bettingModelV3.evaluatePredictions(seasonPredictions)
            print("{:<8}{:>6}  {:>12.2f}{:>12.2f}  {:>12.2f}{:>12.2f}  {:>20}{:>20}".format(
                str(season), summary['games'],
                summary['modelSpreadError'], summary['bookSpreadError'],
                summary['modelTotalError'], summary['bookTotalError'],
                self.recordText(bettingModelV3.betRecord(seasonPredictions, minimumEdge)),
                self.recordText(bettingModelV3.betRecord(seasonPredictions, minimumEdge, betOnTotals = True)),
            ))

        print()
        print("Does a bigger disagreement with the book win more often? Break-even at -110 is {:.1%}.".format(bettingModelV3.BREAK_EVEN_WIN_RATE))
        print("'If model were right' is what the win rate would be if the model's number were the true one.")
        print()
        print("{:<14}{:>20}{:>22}{:>20}".format("Edge at least", "Line bets", "If model were right", "Total bets"))
        for edge in (1, 2, 3, 4, 5, 6, 7):
            lineEdges = [abs(bettingModelV3.spreadEdge(prediction.modelSpread, prediction.bookSpread)) for prediction in predictions]
            lineEdges = [lineEdge for lineEdge in lineEdges if lineEdge >= edge]
            ifRight = "-"
            if len(lineEdges) > 0:
                ifRight = "{:.1%}".format(sum(bettingModelV3.coverProbability(lineEdge) for lineEdge in lineEdges) / len(lineEdges))
            print("{:<14}{:>20}{:>22}{:>20}".format(
                str(edge) + " pts",
                self.recordText(bettingModelV3.betRecord(predictions, edge)),
                ifRight,
                self.recordText(bettingModelV3.betRecord(predictions, edge, betOnTotals = True)),
            ))

        summary = bettingModelV3.evaluatePredictions(predictions)
        if summary['edgeSlope'] != None:
            print()
            print("For every point the model disagreed with the book's line, the result moved {:+.2f} points the model's way.".format(summary['edgeSlope']))
            print("1.00 would mean the model was right and the book wrong; 0.00 means the disagreement told you nothing.")
        print()

    def printQuarterbackComparison(self, predictionsByMode):
        # Only seasons where there is passing on record to adjust with.
        seasons = sorted(set(
            withQuarterback.yearOfSeason
            for withQuarterback, without in zip(predictionsByMode["actual"], predictionsByMode["none"])
            if withQuarterback.modelSpread != without.modelSpread
        ))
        if len(seasons) == 0:
            return
        print()
        print("What the quarterback adjustment is worth, " + str(seasons[0]) + " to " + str(seasons[-1]) + " (average line miss in points):")
        print()
        labels = {
            "none": "No quarterback adjustment",
            "expected": "Assuming last game's starter",
            "actual": "Starter known at kickoff",
        }
        for mode in ("none", "expected", "actual"):
            seasonPredictions = [prediction for prediction in predictionsByMode[mode] if prediction.yearOfSeason in seasons]
            summary = bettingModelV3.evaluatePredictions(seasonPredictions)
            print("{:<34}{:>8.2f}".format(labels[mode], summary['modelSpreadError']))
        print("{:<34}{:>8.2f}".format("Book", summary['bookSpreadError']))
        print()

    def recordText(self, record):
        wins, losses, pushes = record
        if wins + losses == 0:
            return "0-0-" + str(pushes)
        return "{}-{}-{} ({:.1%})".format(wins, losses, pushes, wins / (wins + losses))
