# Betting model V3: how it works and how good it is

V3 is the model behind "V3.0 (Opponent-Adjusted Ratings)" on the Model pages. This
document explains how a betting line gets built in general, how V3 builds its own,
how its settings were chosen, and what the backtest against the stored book lines
shows. The code is in `sportsDjango/nfl_db/bettingModelV3.py`.

All figures below come from the games in this project's database (2018 through
week 10 of 2026) and were produced by `manage.py backtestModelV3Command`.

## The short version

- V3 gives every team an offense rating and a defense rating, both in points
  relative to an average team. A game's expected score is the league average,
  adjusted by the two matchups and by home field.
- The ratings are solved for all at once, so they account for who each team has
  played. Recent games count more, and every rating is pulled toward average.
- It is a clear improvement on V1. Its line misses the final margin by 10.2 points
  in a typical game; V1 misses by 10.6, and predicting "home team by 1.7" for every
  game misses by 11.1.
- It is not better than the book. The closing line misses by 9.8, and V3's bets
  against the closing line won 49.1% of the time over 1,495 decided bets. Break-even
  at the usual -110 price is 52.4%.
- The gap to the book is mostly information V3 does not have: who is playing
  quarterback, injuries, and anything else that happened since the last game.

## Why the book's number is so hard to beat

**The line is a market price, not one person's forecast.** A sportsbook opens a
number, usually from its own ratings, and takes small bets at first. Professional
bettors with their own models bet the side they think is wrong, and the book moves
the number until neither side attracts them. By kickoff the "closing line" contains
the combined opinion of everyone willing to put money on it, including people with
better injury information than any public model.

**The book does not need to be right about a game.** It charges a fee on both
sides: at -110 you risk 110 to win 100, so you need to win 52.4% of the time just
to break even. The book only needs the line to be hard to beat by more than that.

**The line is accurate on average, not game by game.** In this database:

| | Typical miss | Spread of misses (standard deviation) | Average lean |
|---|---|---|---|
| Closing spread vs final margin | 9.8 points | 12.7 points | 0.2 points |
| Closing total vs final total | 10.4 points | 13.2 points | 0.7 points |

A ten-point miss in a typical game is not "spot on". What makes the line hard to
beat is the last column: the misses do not lean in any direction you can predict.
A model beats the book only if it can say, before the game, which way the miss
will go.

## How many factors become one number

The answer to "how do you combine everything" has three parts.

**1. Put everything in the same unit: points.** A team is not "good at passing and
bad on third down". It is "4 points better than an average team". Each team gets a
**power rating**: how many points better or worse than average it is on a neutral
field. Once every factor is expressed in points, combining them is addition.

**2. A line is one rating minus the other, plus adjustments.**

    home team's expected margin = home rating - away rating + home field

Then anything the ratings do not already contain is added in points: a backup
quarterback, a short week, a cross-country trip, wind (for totals). The
quarterback is by far the biggest of these; the rest are usually under a point.

**3. Let past results set the weights.** Nobody decides by hand that offense
matters 60% and defense 40%. You write down the equation above with the ratings as
unknowns, and find the ratings that would have predicted the past games with the
smallest error. That is a regression. The same method tells you how much any other
factor is worth: add it to the equation, fit it on past seasons, and check whether
the predictions for seasons it has not seen get better. If they do not, the factor
is worth nothing however sensible it sounds.

One more idea runs through all of this: **some statistics repeat and some do
not.** A team that moves the ball well this month will probably move it well next
month. A team that has recovered every fumble or won every one-score game probably
will not keep doing it. A model's job is to lean on the first kind and discount the
second. This is the main thing wrong with V1: yards per point is driven largely by
turnovers and field position, which mostly do not repeat.

## How V3 builds its number

### What a rating is

Each team has two numbers:

- **Offense rating**: points it scores above what an average team would score
  against the same opponent.
- **Defense rating**: points it holds an opponent below what that opponent would
  usually score. Positive is good for both.

Their sum is the team's **overall rating**: points better than an average team on a
neutral field. Zero is exactly average. Going into week 5 of 2026 the ratings ran
from +7.4 (SEA, JAX) down to -5.7 (NYJ), and two thirds of teams were within about
3.5 points of zero.

### The equation

Every game played gives two facts, one per team's score:

    home points = league average + half of home field + home offense - away defense
    away points = league average - half of home field + away offense - home defense

Depending on the week there are 250 to 550 games in the window, so 500 to 1,100
equations in 65 unknowns (32 offenses, 32 defenses, the league average). V3 finds
the ratings that fit them best.

Solving them together is what makes the ratings **opponent-adjusted**. If Team A
scored 24 against a defense that normally allows 14, and Team B scored 24 against a
defense that normally allows 30, the only ratings that fit both facts give A a much
better offense than B. V1 would call them equal.

### Recent games count more

A game's weight halves every 10 weeks:

| Game was played | Weight |
|---|---|
| Last week | 0.93 |
| 5 weeks ago | 0.71 |
| 10 weeks ago | 0.50 |
| 20 weeks ago | 0.25 |
| Last season's final regular-season week, seen from week 1 | 0.54 |
| Last season's opening week, seen from week 1 | 0.16 |

The offseason counts as 8 extra weeks, because rosters and coaches change. V3 only
looks at this season and the previous one; anything older would weigh under 3%.
This is also what lets V3 predict week 1: it starts from last season's ratings,
already discounted, and replaces them as new games arrive.

### Every rating is pulled toward average

After one game in which a team scores 14 more than expected, its true level is
probably not "+14". V3 treats every team as if it had also played 4 extra games at
exactly league average. One surprising game therefore moves a rating by about 2.6
points, not 14. Eight recent games averaging +7 produce a rating of about +4.2.
The more a team has played, the less the pull matters.

Without this, early-season ratings swing wildly and predictions get worse.
Statisticians call this shrinkage (the method is ridge regression); the idea is
only that an extreme result is partly real and partly luck.

### Home field

Home field is the average home margin over the same games, leaving out
neutral-site games, pulled toward 2.0 points as if 250 extra games had shown
exactly that. Since 2019 it has ranged from 0.7 to 2.4 points. A game flagged as
neutral gets none.

### Expected score, line and total

For an upcoming game V3 plugs the two teams into the equation. The **line** is the
difference between the two expected scores. The **total** is their sum, with one
change: the part of the total that comes from the teams (as opposed to the league
average) is multiplied by 0.8. Totals are harder to predict than margins, and
damping the team part gave slightly better totals in the backtest.

### Worked example: Las Vegas at New England, week 5 of 2026

Ratings going into the week, from 348 earlier games:

| | Offense | Defense | Overall |
|---|---|---|---|
| NE (home) | +0.45 (12th) | +4.13 (2nd) | +4.58 (4th) |
| LV | -1.41 (22nd) | -1.14 (22nd) | -2.54 (24th) |

League average 22.98 points per team; home field 2.03.

    NE points = 22.98 + 1.02 + 0.45 - (-1.14) = 25.59
    LV points = 22.98 - 1.02 + (-1.41) - 4.13 = 16.42

    margin = 25.59 - 16.42 = 9.16
             (the same as home field 2.03 + NE overall 4.58 - LV overall (-2.54))

    raw total      = 25.59 + 16.42 = 42.01, which is 3.95 under two league averages (45.96)
    damped total   = 45.96 - 0.8 x 3.95 = 42.80

    NE = (42.80 + 9.16) / 2 = 26.0        LV = (42.80 - 9.16) / 2 = 16.8

So V3 said **NE -9.2, total 42.8**. The book said NE -3.5, total 45.5. V3 liked
New England by 5.7 points more than the book and the under by 2.7. New England won
45-17: the line bet won and the under lost.

### From a number to a bet

**Edge** is the gap between V3's number and the book's, in points. V3 names a bet
only when the edge is at least 1 point, and otherwise shows PASS.

A point of edge is worth roughly 3 percentage points of win probability, *if the
model's number were the true one*. Final margins land about 13.1 points (one
standard deviation) either side of V3's prediction, which gives:

| Edge | Chance of covering if V3 were right |
|---|---|
| 1 point | 53.0% |
| 2 points | 56.1% |
| 3 points | 59.1% |
| 5 points | 64.9% |
| 7 points | 70.3% |

That is the standard way to turn a model's number into a probability, and it is why
a 1-point minimum is the least you could ask for (53.0% barely clears the 52.4%
break-even). **But the backtest below shows V3 is not right when it disagrees with
the book**, so these probabilities are an upper bound, not a forecast. The pages
show the edge in points and deliberately do not show a win probability.

## How the settings were chosen

Each setting was tried over a range, predicting every week from 2019 on using only
earlier games, and scoring by how far the predicted margin was from the result.

| Setting | Value | What the range showed |
|---|---|---|
| Half-life of a game | 10 weeks | 6 to 12 weeks all miss by 10.2. Longer is worse: 16 weeks misses by 10.3, 24 weeks by 10.4, 40 weeks by 10.5. |
| Offseason, in weeks of aging | 8 extra | 4 to 12 extra weeks are within about 0.02 of each other. |
| Pull toward average | 4 games | 3 to 6 games are the same. 1 game is worse by about 0.1. |
| Team part of the total | 0.8 | 0.6 to 0.8 are the same; 1.0 (no damping) is worse by 0.04. |
| Home field prior | 2.0 points, 250 games | 100 to 600 games, and 1.5 points, all within 0.01. |
| Seasons of history | 2 | 3 seasons gives the same result. |

The useful finding is how flat this is. No setting is doing clever work, so there
is little risk that the values were tuned to fit these particular seasons. The
values are round numbers from the middle of each flat region.

## Backtest results

Every prediction uses only games from earlier weeks. Lines are the ones stored on
each match, which are closing lines.

### V3 against the book, by season

| Season | Games | V3 line miss | Book line miss | V3 total miss | Book total miss | Line bets | Total bets |
|---|---|---|---|---|---|---|---|
| 2019 | 254 | 10.40 | 10.15 | 10.93 | 10.97 | 86-89-5 | 87-88-0 |
| 2020 | 255 | 10.13 | 9.83 | 10.73 | 10.12 | 97-89-0 | 79-98-5 |
| 2021 | 272 | 11.23 | 10.79 | 11.18 | 10.81 | 101-108-2 | 93-104-2 |
| 2022 | 284 | 9.00 | 8.82 | 10.81 | 10.43 | 110-94-9 | 91-109-2 |
| 2023 | 272 | 10.36 | 9.88 | 10.53 | 10.31 | 94-107-5 | 102-90-1 |
| 2024 | 272 | 10.19 | 9.65 | 9.95 | 9.69 | 101-107-0 | 101-87-0 |
| 2025 | 284 | 10.16 | 9.64 | 10.64 | 10.45 | 101-112-0 | 117-103-0 |
| 2026 (to week 10) | 137 | 9.84 | 9.43 | 11.19 | 10.53 | 44-55-3 | 50-57-0 |
| **All** | **2,030** | **10.18** | **9.79** | **10.71** | **10.40** | **734-761-24 (49.1%)** | **720-736-10 (49.5%)** |

"Miss" is the average distance in points between the number and the result. Bets
are games where V3 was at least 1 point from the book; records are wins-losses-pushes.

The book's line is closer to the result in every season. V3's bets win in some
seasons and lose in others, with no pattern, which is what chance looks like.

### Does a bigger disagreement win more often?

| Edge at least | Line bets | If V3 were right | Total bets |
|---|---|---|---|
| 1 point | 734-761-24 (49.1%) | 59.4% | 720-736-10 (49.5%) |
| 2 points | 501-509-12 (49.6%) | 61.9% | 473-496-9 (48.8%) |
| 3 points | 333-339-8 (49.6%) | 64.2% | 289-309-3 (48.3%) |
| 4 points | 210-192-6 (52.2%) | 66.9% | 163-184-2 (47.0%) |
| 5 points | 121-111-4 (52.2%) | 69.6% | 88-95-1 (48.1%) |
| 6 points | 69-64-2 (51.9%) | 72.2% | 42-52-1 (44.7%) |
| 7 points | 41-36-1 (53.2%) | 74.7% | 23-28-0 (45.1%) |

If V3's numbers were the true ones, the win rate would climb from 59% to 75% as the
edge grows. It stays near 50%. Line bets with 4 or more points of edge won 52.2%,
which is below break-even and, on 402 bets, well within what luck produces (the
margin of error is about 5 percentage points either way).

The plainest summary is one number. For every point V3 disagreed with the book's
line, the result moved **-0.03 points** V3's way. A value of 1 would mean V3 was
right and the book wrong; 0 means the disagreement carried no information. When
both numbers are used together to predict the margin, the best blend puts a weight
of about 1.03 on the book's line and 0.05 on V3's.

When V3 and the book disagree by a lot, the usual reason is something V3 cannot
see. In the example above it worked out; across 2,030 games it did not.

### V3 against V1 and V1.5

The same 1,774 games (2020 through week 10 of 2026, where all three models made a
prediction and the book had a line):

| | Line miss | Total miss | Line bets won | Total bets won |
|---|---|---|---|---|
| Home team by 1.7 every game / league-average total | 11.05 | 10.99 | | |
| V1 | 10.60 | 11.03 | 50.5% | 48.8% |
| V1.5 (5-game average) | 10.45 | 11.07 | 50.7% | 48.2% |
| **V3** | **10.15** | **10.68** | 49.8% | 49.8% |
| Closing line | 9.74 | 10.32 | | |

(The first row is over all 2,029 games with lines from 2019 on, so it is a rough
yardstick.) Here every model bets every game it disagrees on, to compare like with
like.

Knowing nothing but home field misses the margin by about 11.1 points and the book
misses by 9.7, so the whole range a model can occupy is about 1.3 points wide. V1
covers about a third of it and V3 about two thirds. V1's totals are slightly worse
than guessing the league average every time.

On picking sides against the book all three are at 50%, and none is near 52.4%.
V1.5 won 53.0% of line bets with 5 or more points of edge, on 541 bets; with a
margin of error of about 4 points either way that is not evidence of an edge.

**A better model of the game is not the same as a model that beats the line.** V3
is the first; nothing here is the second.

## What was tried and did not help

Before settling on points alone, each of these was rated the same way
(opponent-adjusted, recency-weighted) and added to the points ratings, with its
weight fitted on earlier seasons and tested on later ones:

| Added to the points ratings | Line miss on seasons it had not seen |
|---|---|
| Nothing (points only) | 10.14 |
| Yards per play | 10.15 |
| Net yards per pass play | 10.15 |
| Points per drive | 10.14 |
| First downs per play | 10.17 |
| Total yards | 10.18 |
| Yards per play and turnovers | 10.16 |
| Yards per play and third-down rate | 10.17 |

Used alone, without points, they were all worse: yards per play 10.35, total yards
10.36, third-down rate 10.6, turnovers 10.75.

None of them improved on points. Two caveats. These are box-score statistics, which
are blunt. And the efficiency measures analysts favor, expected points added and
success rate per play, were not tried because they need a model of what each
down-and-distance is worth, built from play-by-play, and this database has plays
only from 2021.

## What V3 does not know

- **Who is playing quarterback.** This is the single biggest thing the market knows
  and V3 does not. A team whose starter was hurt last week has the same rating
  today.
- **Other injuries, suspensions and players rested late in the season.** V3's worst
  stretch is weeks 15 to 18 (line miss 10.7 against the book's 10.0).
- **Rest and travel**: byes, Thursday games, long trips.
- **Weather**, which matters for totals.
- **Luck in the scores themselves.** A defensive touchdown counts the same as a
  long drive.
- **Line movement.** The `nflMatchOdds` table has columns for opening and closing
  lines but no rows, so the backtest can only compare against one line per game,
  the closing one. That is the hardest possible test. Bettors who beat the market
  mostly do it by betting early and then seeing the line move toward them (closing
  line value). Measuring that needs opening lines to be stored.

## Using it

**Pages.** Pick "V3.0 (Opponent-Adjusted Ratings)" in the Model dropdown.

- *Weekly Summary*: each game's expected score, V3's line and total next to the
  book's, and the bet (or PASS). Bets show before the game and are graded after.
  Games are ordered by edge, largest first. Expanding a row shows both teams'
  ratings and ranks, home field, and the edges.
- *Model Breakdown*: the same week with the ratings laid out as a table per game.
- *Yearly Summary*: week-by-week records for a season. "Number of top results"
  keeps only each week's largest disagreements.

**Reading a line.** Lines are the home team's: "NE -9.2" means V3 expects New
England to win by 9.2. A bet shown as "NE -3.5" means: take New England at the
book's -3.5.

**Commands.**

    python3 manage.py backtestModelV3Command                  # the tables above, 2019 on
    python3 manage.py backtestModelV3Command --from 2023 --to 2025
    python3 manage.py modelResultsCommand --season 2025 --model v3     # precompute a season
    python3 manage.py modelResultsCommand --clear --model v3           # drop stored V3 results

The backtest reads the database and writes nothing.

**Stored results.** Like V1, results for finished games are saved in
`bettingModelResult` so pages load quickly, and are dropped when a game in an
earlier week is pulled again. The team ratings shown on the weekly pages are not
stored; they are refitted on each load, which takes a few milliseconds. After
changing a setting, run the `--clear --model v3` command so old results are not
shown.

**Settings** are the constants at the top of `bettingModelV3.py`. Change one, clear
the stored results, and rerun the backtest to see the effect.

**No previous season in the database.** V3 needs at least 100 earlier games from
this season and last. Where the previous season is missing (2016, 2017 and early
2018 here) it makes no prediction and shows zeros.

**Tests** are in `nfl_db/tests.py` (the classes starting `BettingModelV3`).

## Where to go next

In rough order of likely value:

1. **A quarterback adjustment.** Identify each team's passer per game from the
   play-by-play (2021 on), rate quarterbacks alongside teams, and predict with the
   expected starter. This is the largest known gap.
2. **Store opening lines** (fill `nflMatchOdds`) so the model can be tested against
   openers and for closing line value, which is a fairer test than the close.
3. **Per-play efficiency** from the play-by-play: build an expected-points table by
   down, distance and field position, and rate teams on that.
4. **Rest and travel** as point adjustments, fitted the same way.
5. **Other markets.** Player props and other smaller markets get less attention
   from professional bettors than NFL sides and totals do. The Props page already
   stores prop lines.

Each of these should be judged the way V3 was: fit on earlier seasons, score on
later ones, and keep it only if the miss goes down.

## Glossary

- **Spread / line**: the handicap on a game. "KC -3.5" means Kansas City must win
  by more than 3.5 for a bet on it to win.
- **Total / over-under**: the combined points line.
- **Cover**: to win against the spread.
- **Push**: the result lands exactly on the line; the bet is refunded.
- **-110**: risk 110 to win 100. Break-even is 110 / 210 = 52.4%.
- **Closing line**: the line at kickoff.
- **Edge**: the gap between the model's number and the book's, in points.
- **Power rating**: a team's strength in points relative to average.
- **Opponent-adjusted**: corrected for the strength of the teams played.
- **Walk-forward backtest**: predicting each past game using only what was known
  before it.
