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
- Each team's score is then adjusted for its quarterback: how much better or worse
  this week's starter has passed than the quarterbacks who played the games the
  team's rating came from.
- It is a clear improvement on V1. Its line misses the final margin by 10.1 points
  in a typical game; V1 misses by 10.6, and predicting "home team by 1.7" for every
  game misses by 11.1.
- It is not better than the book. The closing line misses by 9.8, and V3's bets
  against the closing line won 49.3% of the time over 1,437 decided bets. Break-even
  at the usual -110 price is 52.4%.
- The quarterback adjustment closes about a quarter of the gap to the book. What
  remains is mostly information V3 does not have: injuries at other positions, a
  starter returning, and anything else that happened since the last game.

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
is worth nothing however sensible it sounds. V3's quarterback adjustment was added
this way, and several other statistics were rejected this way (both are below).

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

### The quarterback adjustment

A team's rating is earned by whoever played quarterback in its recent games. If
someone else starts this week, the rating is describing a different team. The
adjustment corrects for that, in four steps.

**1. Measure each quarterback's passing.** The measure is adjusted yards per
dropback: passing yards, plus 20 for each touchdown, minus 45 for each interception,
minus yards lost to sacks, divided by pass attempts plus sacks. It is the standard
one-number summary of passing (often written ANY/A). The league average here is
about 6.1. Each game's passing is credited to whoever dropped back most for the
team, and games count less as they age, halving every 40 weeks.

**2. Pull every quarterback toward an unproven one.** A quarterback nobody has seen
is assumed to be 2 adjusted yards per dropback worse than the league average,
because quarterbacks without a record are mostly backups and rookies. Everyone is
then treated as if he had also dropped back 200 times at that level (about six
games). One good game from a backup barely moves him; two seasons from a starter
mostly outweigh the pull.

**3. Convert to points.** One adjusted yard per dropback is worth 3 points a game.
So an unproven quarterback sits 6 points a game below a league-average passer. The
pages show each quarterback's value measured from that unproven level, which is
easier to read: going into week 5 of 2026 the best were Matthew Stafford (+8.3),
Jared Goff (+7.8) and Brock Purdy (+7.2), a new backup is 0, and a backup who has
played badly can be below zero.

**4. Compare this week's starter with the quarterbacks behind the rating.** The
team's baseline is the value of the quarterbacks who played its games, weighted the
same way the games are weighted in the rating.

    adjustment = this week's starter's value - the team's baseline

The adjustment is added to that team's expected score. If the same quarterback
played every game, the adjustment is exactly zero, and that is the usual case: 72%
of the time it is under 1 point, 21% of the time 1 to 3 points, and 7% of the time
more than 3. The largest in the backtest was 9.1.

Examples from week 5 of 2026:

- **New England, Drake Maye.** He had played every New England game in the window.
  Adjustment 0.0.
- **Las Vegas, Kirk Cousins.** His value was +4.5, but Las Vegas's rating had been
  earned partly with Kenny Pickett, Aidan O'Connell and Geno Smith, a baseline of
  +3.0. Adjustment +1.5.
- **Baltimore, Tyler Huntley** starting in place of Lamar Jackson. Huntley's value
  was +1.1 against a Baltimore baseline of +5.7. Adjustment -4.6.

**Who is "this week's starter"?** For a game that has been played, it is whoever
took the team's first dropback. For a game that has not been played, V3 assumes
the quarterback who started the team's previous game. If the availability data for
that week lists him as out, doubtful or on injured reserve, it takes the team's
next most recent quarterback, and if they are all out it assumes an unproven one.
The pages mark an assumed starter "(expected)".

That assumption was right 86% of the time in the backtest. It is wrong mainly when
a starter comes back from injury or a team changes quarterbacks by choice, and V3
has no way to see either coming. **When the expected starter is wrong, the number
is wrong by about the size of the adjustment shown**, so check the name before
trusting a large edge.

**Picking the starter yourself.** For a game that has not been played, both weekly
pages have a dropdown of the team's quarterbacks. Choosing one saves it and redoes
that game's numbers with him; he is then marked "(chosen)". Choosing "Model's
guess" undoes it. In week 11 of 2026, for example, V3 assumed Joe Milton III for
Philadelphia and made Pittsburgh a 6.4-point favorite; with Jalen Hurts chosen it
makes Pittsburgh a 1.6-point favorite. A choice only applies until the game is
played, after which the actual starter is used, and the backtest never uses
choices.

Quarterback data comes from the play-by-play, which this database has from 2021.
Games before that get no adjustment.

### Expected score, line and total

For an upcoming game V3 plugs the two teams into the equation and then adds each
team's quarterback adjustment to its score. The **line** is the difference between
the two expected scores. The **total** is their sum, with one change: the part of
the total that comes from the team ratings (as opposed to the league average) is
multiplied by 0.8. Totals are harder to predict than margins, and damping the team
part gave slightly better totals in the backtest.

### Worked example: Las Vegas at New England, week 5 of 2026

Ratings going into the week, from 348 earlier games:

| | Offense | Defense | Overall | Quarterback | QB adjustment |
|---|---|---|---|---|---|
| NE (home) | +0.45 (12th) | +4.13 (2nd) | +4.58 (4th) | Drake Maye | 0.00 |
| LV | -1.41 (22nd) | -1.14 (22nd) | -2.54 (24th) | Kirk Cousins | +1.53 |

League average 22.98 points per team; home field 2.03.

    NE points = 22.98 + 1.02 + 0.45 - (-1.14) = 25.59
    LV points = 22.98 - 1.02 + (-1.41) - 4.13 = 16.42

    margin = 25.59 - 16.42 = 9.16
             (the same as home field 2.03 + NE overall 4.58 - LV overall (-2.54))

    raw total      = 25.59 + 16.42 = 42.01, which is 3.95 under two league averages (45.96)
    damped total   = 45.96 - 0.8 x 3.95 = 42.80

    before quarterbacks:  NE = (42.80 + 9.16) / 2 = 25.98    LV = (42.80 - 9.16) / 2 = 16.82
    with quarterbacks:    NE = 25.98 + 0.00 = 26.0           LV = 16.82 + 1.53 = 18.4

So V3 said **NE -7.6, total 44.4**. The book said NE -3.5, total 45.5. V3 liked
New England by 4.1 points more than the book and the under by 1.1. New England won
45-17: the line bet won and the under lost.

### From a number to a bet

**Edge** is the gap between V3's number and the book's, in points. V3 names a bet
only when the edge is at least 1 point, and otherwise shows PASS.

A point of edge is worth roughly 3 percentage points of win probability, *if the
model's number were the true one*. Final margins land about 13.0 points (one
standard deviation) either side of V3's prediction, which gives:

| Edge | Chance of covering if V3 were right |
|---|---|
| 1 point | 53.1% |
| 2 points | 56.1% |
| 3 points | 59.1% |
| 5 points | 65.0% |
| 7 points | 70.5% |

That is the standard way to turn a model's number into a probability, and it is why
a 1-point minimum is the least you could ask for (53.1% barely clears the 52.4%
break-even). **But the backtest below shows V3 is not right when it disagrees with
the book**, so these probabilities are an upper bound, not a forecast. The pages
show the edge in points and deliberately do not show a win probability.

## How the settings were chosen

Each setting was tried over a range, predicting every week using only earlier
games, and scoring by how far the predicted margin was from the result. The team
settings were scored on 2019 on; the quarterback settings on 2022 on, the first
season with a full previous season of passing data.

| Setting | Value | What the range showed |
|---|---|---|
| Half-life of a game | 10 weeks | 6 to 12 weeks all miss by 10.2. Longer is worse: 16 weeks misses by 10.3, 24 weeks by 10.4, 40 weeks by 10.5. |
| Offseason, in weeks of aging | 8 extra | 4 to 12 extra weeks are within about 0.02 of each other. |
| Pull toward average | 4 games | 3 to 6 games are the same. 1 game is worse by about 0.1. |
| Team part of the total | 0.8 | 0.6 to 0.8 are the same; 1.0 (no damping) is worse by 0.04. |
| Home field prior | 2.0 points, 250 games | 100 to 600 games, and 1.5 points, all within 0.01. |
| Seasons of history | 2 | 3 seasons gives the same result, for teams and for quarterbacks. |
| Quarterback half-life | 40 weeks | 20 to 60 weeks all miss by 9.80. |
| Unproven quarterback | 2.0 yards below average | 2.0 to 3.0 all miss by 9.80. Smaller is worse: 1.5 misses by 9.81, 0.75 by 9.85. |
| Pull toward unproven | 200 dropbacks | 150 to 300 are the same. |
| Points per adjusted yard | 3.0 | 2.5 to 3.5 are the same. |

The useful finding is how flat this is. No setting is doing clever work, so there
is little risk that the values were tuned to fit these particular seasons. The
values are round numbers from the middle of each flat region.

One caution about the quarterback settings: they were chosen on the same 2022 to
2026 games they are scored on, because there are only five seasons of passing data.
When the points-per-yard value was instead fitted on earlier seasons and applied to
later ones, the miss was the same (9.80), which is some reassurance.

## Backtest results

Every prediction uses only games from earlier weeks. Lines are the ones stored on
each match, which are closing lines. Each team is rated with the quarterback who
took its first dropback in the game, which is known by kickoff.

### V3 against the book, by season

| Season | Games | V3 line miss | Book line miss | V3 total miss | Book total miss | Line bets | Total bets |
|---|---|---|---|---|---|---|---|
| 2019 | 253 | 10.43 | 10.19 | 10.95 | 10.80 | 86-88-5 | 86-88-0 |
| 2020 | 255 | 10.13 | 9.83 | 10.73 | 10.12 | 97-89-0 | 79-98-5 |
| 2021 | 272 | 11.24 | 10.79 | 10.98 | 10.81 | 91-109-2 | 93-98-2 |
| 2022 | 284 | 9.09 | 8.82 | 10.70 | 10.43 | 106-95-7 | 92-113-3 |
| 2023 | 272 | 10.23 | 9.88 | 10.48 | 10.31 | 93-93-3 | 92-92-1 |
| 2024 | 272 | 10.08 | 9.65 | 9.77 | 9.69 | 97-111-0 | 106-84-0 |
| 2025 | 284 | 9.93 | 9.64 | 10.76 | 10.45 | 96-98-0 | 102-106-0 |
| 2026 (to week 10) | 137 | 9.64 | 9.43 | 10.81 | 10.53 | 42-46-3 | 52-43-0 |
| **All** | **2,029** | **10.11** | **9.79** | **10.63** | **10.38** | **708-729-20 (49.3%)** | **702-722-11 (49.3%)** |

"Miss" is the average distance in points between the number and the result. Bets
are games where V3 was at least 1 point from the book; records are wins-losses-pushes.
2019 and 2020 have no quarterback adjustment, and 2021 only a partial one.

The book's line is closer to the result in every season. V3's bets win in some
seasons and lose in others, with no pattern, which is what chance looks like.

### What the quarterback adjustment is worth

Line miss on the 1,249 games from 2022 on:

| | Line miss |
|---|---|
| V3 with no quarterback adjustment | 9.91 |
| Assuming each team's previous starter (what V3 does before a game) | 9.86 |
| With the starter known at kickoff | 9.80 |
| Closing line | 9.48 |

Knowing the starter closes about a quarter of the gap between V3 and the book.
Even the guessed starter helps, because the guess is usually right. Totals improve
too (10.56 to 10.48). In weeks 15 to 18, when quarterbacks change most, V3's line
miss went from 10.7 to 10.5.

It does not turn V3 into a winner. Line bets from 2022 on went 434-443 with the
adjustment and 450-475 without it.

### Does a bigger disagreement win more often?

| Edge at least | Line bets | If V3 were right | Total bets |
|---|---|---|---|
| 1 point | 708-729-20 (49.3%) | 58.8% | 702-722-11 (49.3%) |
| 2 points | 480-476-11 (50.2%) | 61.0% | 449-456-8 (49.6%) |
| 3 points | 286-275-6 (51.0%) | 63.6% | 252-263-4 (48.9%) |
| 4 points | 153-149-4 (50.7%) | 66.3% | 130-147-0 (46.9%) |
| 5 points | 79-81-1 (49.4%) | 69.1% | 72-76-0 (48.6%) |
| 6 points | 38-39-1 (49.4%) | 72.4% | 34-34-0 (50.0%) |
| 7 points | 22-27-0 (44.9%) | 74.4% | 17-19-0 (47.2%) |

If V3's numbers were the true ones, the win rate would climb from 59% to 74% as the
edge grows. It stays near 50% at every size.

The plainest summary is one number. For every point V3 disagreed with the book's
line, the result moved **+0.02 points** V3's way. A value of 1 would mean V3 was
right and the book wrong; 0 means the disagreement carried no information. When
both numbers are used together to predict the margin, the best blend puts a weight
of about 0.99 on the book's line and 0.10 on V3's.

When V3 and the book disagree by a lot, the usual reason is something V3 cannot
see. In the worked example it worked out; across 2,029 games it did not.

### V3 against V1 and V1.5

The same 1,774 games (2020 through week 10 of 2026, where all three models made a
prediction and the book had a line):

| | Line miss | Total miss | Line bets won | Total bets won |
|---|---|---|---|---|
| Home team by 1.7 every game / league-average total | 11.05 | 10.99 | | |
| V1 | 10.60 | 11.03 | 50.5% | 48.8% |
| V1.5 (5-game average) | 10.45 | 11.07 | 50.7% | 48.2% |
| V3 without the quarterback adjustment | 10.15 | 10.68 | 49.8% | 49.8% |
| **V3** | **10.07** | **10.59** | 48.7% | 50.6% |
| Closing line | 9.74 | 10.32 | | |

(The first row is over all 2,029 games with lines from 2019 on, so it is a rough
yardstick.) Here every model bets every game it disagrees on, to compare like with
like.

Knowing nothing but home field misses the margin by about 11.1 points and the book
misses by 9.7, so the whole range a model can occupy is about 1.3 points wide. V1
covers about a third of it and V3 about three quarters. V1's totals are slightly
worse than guessing the league average every time.

On picking sides against the book all of them are near 50%, and none is near 52.4%.
V1.5 won 53.0% of line bets with 5 or more points of edge, on 541 bets; with a
margin of error of about 4 points either way that is not evidence of an edge.

**A better model of the game is not the same as a model that beats the line.** V3
is the first; nothing here is the second.

## What was tried and did not help

Before the quarterback adjustment, each of these was rated the same way as points
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

For the quarterback, a cruder version was also tried: a flat penalty whenever the
starter is not the team's usual quarterback, ignoring how good either one is. It
helped about half as much as valuing each quarterback.

## What V3 does not know

- **A starter coming back, or a quarterback change by choice**, unless you tell it.
  Before a game V3 assumes last game's starter. It can drop a quarterback who is
  listed as out, but nothing tells it that an injured starter has returned; that
  is what the starter dropdown is for.
- **How much of a quarterback's value is running.** Only passing is measured.
- **Other injuries, suspensions and players rested late in the season.**
- **Rest and travel**: byes, Thursday games, long trips.
- **Weather**, which matters for totals.
- **Luck in the scores themselves.** A defensive touchdown counts the same as a
  long drive.
- **Line movement.** The `nflMatchOdds` table has columns for opening and closing
  lines but no rows, so the backtest can only compare against one line per game,
  the closing one. That is the hardest possible test. Bettors who beat the market
  mostly do it by betting early and then seeing the line move toward them (closing
  line value). Measuring that needs opening lines to be stored.

## Notes on the data

Things found in the database while building this, which shaped how V3 reads it:

- **`passerStatSplit` has duplicate rows for some 2025 plays** (about 16,000 rows
  for 11,700 completed passes). V3 counts distinct plays, so it is not affected.
- **`passerStatSplit.passingYards` is not usable for 2023, 2024 and part of 2025**:
  summed per game it comes to thousands of yards more than the team's box score.
- **Interceptions have no passer row**, so they cannot be credited from the splits.

Because of the last two, V3 takes only the identity of the passers from the
play-by-play (who dropped back, how often, and who went first) and takes the
passing numbers from the team's box score in `teamMatchPerformance`, which is
complete from 2018. Pass attempts and sacks from the two sources agree to within
one play a game.

- **Availability data is patchy**: `playerWeekStatus` is well filled for 2022,
  2023 and 2025, thin for 2024, and for 2026 nearly empty after week 5. For any
  week without it, V3 simply assumes last game's starter.

## Using it

**Pages.** Pick "V3.0 (Opponent-Adjusted Ratings)" in the Model dropdown.

- *Weekly Summary*: each game's expected score, V3's line and total next to the
  book's, and the bet (or PASS). Bets show before the game and are graded after.
  Games are ordered by edge, largest first. Expanding a row shows both teams'
  ratings and ranks, each quarterback and his adjustment, home field, and the edges.
- *Model Breakdown*: the same week with the ratings laid out as a table per game,
  including each quarterback's value over an unproven quarterback.
- *Yearly Summary*: week-by-week records for a season. "Number of top results"
  keeps only each week's largest disagreements.

**Reading a line.** Lines are the home team's: "NE -7.6" means V3 expects New
England to win by 7.6. A bet shown as "NE -3.5" means: take New England at the
book's -3.5.

**Before betting an upcoming game**, look at the quarterback names. One marked
"(expected)" is V3's assumption. If someone else will start, pick him: on Weekly
Summary, expand the game and use "Change Starter"; on Model Breakdown, use the
dropdown in the Quarterback row. The dropdown lists the quarterbacks on the team's
roster. Pulling player availability for the week (Players, Player Availability
tab) also lets V3 replace a starter who is out on its own.

Choices are kept in the `chosenStartingQuarterback` table. It was added with a
migration, so any other copy of the database (the web host's) needs `migrate` run
before the V3 pages will load there.

**Commands.**

    python3 manage.py backtestModelV3Command                  # the tables above, 2019 on
    python3 manage.py backtestModelV3Command --from 2023 --to 2025
    python3 manage.py backtestModelV3Command --quarterbacks expected   # rate teams with last game's starter
    python3 manage.py backtestModelV3Command --quarterbacks none       # no quarterback adjustment
    python3 manage.py modelResultsCommand --season 2025 --model v3     # precompute a season
    python3 manage.py modelResultsCommand --clear --model v3           # drop stored V3 results

The backtest reads the database and writes nothing. It ignores availability data
when guessing a starter, because past weeks' statuses were often updated after the
game.

**Stored results.** Like V1, results for finished games are saved in
`bettingModelResult` so pages load quickly, and are dropped when a game in an
earlier week is pulled again. The ratings and quarterbacks shown on the weekly
pages are not stored; they are refitted on each load, which takes a fraction of a
second. After changing a setting, run the `--clear --model v3` command so old
results are not shown.

**Settings** are the constants at the top of `bettingModelV3.py`. Change one, clear
the stored results, and rerun the backtest to see the effect.

**No previous season in the database.** V3 needs at least 100 earlier games from
this season and last. Where the previous season is missing (2016, 2017 and early
2018 here) it makes no prediction and shows zeros.

**Tests** are in `nfl_db/tests.py` (the classes starting `BettingModelV3`).

## Where to go next

In rough order of likely value:

1. **A depth chart pull.** The adjustment is only as good as the name it is given.
   You can now set the starter by hand; pulling each team's depth chart would do
   it without you.
2. **Store opening lines** (fill `nflMatchOdds`) so the model can be tested against
   openers and for closing line value, which is a fairer test than the close.
3. **Per-play efficiency** from the play-by-play: build an expected-points table by
   down, distance and field position, and rate teams and quarterbacks on that. It
   would also capture quarterback running.
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
- **Dropback**: a pass attempt or a sack.
- **Adjusted yards per dropback**: passing yards, plus 20 per touchdown, minus 45
  per interception, minus sack yards, per dropback.
- **Walk-forward backtest**: predicting each past game using only what was known
  before it.
