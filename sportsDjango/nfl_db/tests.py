from django.test import SimpleTestCase

from nfl_db.crudLogic import yardsGainedOnPlay, passingYardsOnPlay, receivingYardsOnPlay, playTypeBeforeFumble, descriptionNameRegex, LATERAL_RECEIVER_ROLE


class YardsGainedOnPlayTests(SimpleTestCase):
    def test_plain_run(self):
        self.assertEqual(yardsGainedOnPlay("J.Warren up the middle to PIT 30 for 5 yards (J.Battle).", 75), 5)

    def test_offensive_holding_downfield_credits_yards_to_the_spot(self):
        description = "J.Warren up the middle to CIN 5 for 87 yards (J.Battle).PENALTY on PIT-D.Metcalf, Offensive Holding, 7 yards, enforced at PIT 14."
        self.assertEqual(yardsGainedOnPlay(description, 92), 6)
        description = "J.Warren left end pushed ob at CIN 19 for 11 yards (B.Cook).PENALTY on PIT-D.Metcalf, Offensive Holding, 10 yards, enforced at CIN 27."
        self.assertEqual(yardsGainedOnPlay(description, 30), 3)

    def test_foul_at_the_end_of_the_run_keeps_the_whole_run(self):
        description = "(Shotgun) J.Dart left end ran ob at DAL 37 for 22 yards (D.Overshown).PENALTY on DAL-D.Overshown, Unnecessary Roughness, 15 yards, enforced at DAL 37."
        self.assertEqual(yardsGainedOnPlay(description, 59), 22)

    def test_catch_with_holding_downfield(self):
        description = "(Shotgun) J.Brissett pass short left to T.McBride to ARZ 20 for 8 yards (R.Green; J.Brown).PENALTY on ARZ-E.Higgins, Offensive Holding, 6 yards, enforced at ARZ 13."
        self.assertEqual(yardsGainedOnPlay(description, 88), 1)

    def test_run_ending_at_midfield(self):
        description = "J.Jacobs up the middle to 50 for 7 yards (M.Hooker; D.Bland).PENALTY on GB-J.Morgan, Offensive Holding, 10 yards, enforced at GB 45."
        self.assertEqual(yardsGainedOnPlay(description, 57), 2)

    def test_touchdown_nullified_by_holding(self):
        description = "J.Taylor left tackle for 53 yards, TOUCHDOWN NULLIFIED by Penalty.PENALTY on IND-A.Mitchell, Offensive Holding, 10 yards, enforced at LA 48."
        self.assertEqual(yardsGainedOnPlay(description, 53), 5)

    def test_without_line_of_scrimmage_reads_the_description(self):
        description = "J.Warren up the middle to CIN 5 for 87 yards (J.Battle).PENALTY on PIT-D.Metcalf, Offensive Holding, 7 yards, enforced at PIT 14."
        self.assertEqual(yardsGainedOnPlay(description), 87)

    def test_replay_reversal_reads_the_play_as_it_now_stands(self):
        description = "(Shotgun) T.Lawrence pass short left to P.Washington to CIN 16 for 39 yards (D.Hill).The Replay Official reviewed the runner was inbounds ruling, and the play was REVERSED.(Shotgun) T.Lawrence pass short left to P.Washington ran ob at CIN 48 for 7 yards."
        self.assertEqual(yardsGainedOnPlay(description, 55), 7)

    def test_reversed_two_point_try_leaves_the_touchdown_alone(self):
        description = "(Shotgun) B.Hall right end for 27 yards, TOUCHDOWN. TWO-POINT CONVERSION ATTEMPT. J.Fields pass to I.Davis is complete. ATTEMPT FAILS.The Replay Official reviewed the short of the goal line ruling, and the play was REVERSED.TWO-POINT CONVERSION ATTEMPT. J.Fields pass to I.Davis is complete. ATTEMPT SUCCEEDS."
        self.assertEqual(yardsGainedOnPlay(description, 27), 27)

    def test_espn_summary_wording(self):
        self.assertEqual(yardsGainedOnPlay("Daniel Jones Pass Complete for 48 Yds to Laquon Treadwell"), 48)
        self.assertEqual(yardsGainedOnPlay("JuJu Smith-Schuster 13 Yd pass from Patrick Mahomes"), 13)

    def test_fumble_recovered_by_the_other_team_behind_the_fumble(self):
        description = "(No Huddle, Shotgun) M.Stafford pass short middle to T.Higbee to LA 44 for 5 yards (F.Warner; D.Greenlaw). FUMBLES (F.Warner), RECOVERED by SF-K.White at LA 43."
        self.assertEqual(yardsGainedOnPlay(description, 61), 4)

    def test_fumble_credited_to_where_it_was_first_touched(self):
        description = "(Shotgun) C.Keenum pass short right to R.Odunze to GB 31 for 9 yards (Z.Franklin). FUMBLES (Z.Franklin), touched at GB 37, RECOVERED by GB-E.Williams at GB 43."
        self.assertEqual(yardsGainedOnPlay(description, 40), 3)
        description = "(Shotgun) C.Ward scrambles right end to TEN 15 for 1 yard. FUMBLES, touched at TEN 14, ball out of bounds at TEN 14."
        self.assertEqual(yardsGainedOnPlay(description, 86), 0)

    def test_teammate_recovery_behind_the_fumble(self):
        description = "(Shotgun) T.Lawrence pass deep right to Bri.Thomas to CLV 36 for 17 yards (D.Ward; C.Schwesinger). FUMBLES (D.Ward), recovered by JAX-B.Tuten at CLV 41."
        self.assertEqual(yardsGainedOnPlay(description, 53), 12)

    def test_fumbler_recovering_and_carrying_on(self):
        description = "(No Huddle, Shotgun) B.Young pass short left to T.Tremble to ATL 11 for no gain (X.Watts). FUMBLES (X.Watts), and recovers at ATL 9. T.Tremble to ATL 7 for 2 yards (X.Watts)."
        self.assertEqual(yardsGainedOnPlay(description, 11), 4)
        description = "(Shotgun) K.Cousins pass short left to J.Bech to LAC 7 for 16 yards (D.Jackson). FUMBLES (D.Jackson), and recovers at LAC 3. J.Bech ran ob at LAC 3 for no gain."
        self.assertEqual(yardsGainedOnPlay(description, 23), 20)


class FumbledPlayTests(SimpleTestCase):
    def test_fumbled_catch_is_a_completion(self):
        description = "(Shotgun) D.Maye pass deep right to D.Douglas to NYJ 33 for 39 yards (J.Sherwood). FUMBLES (J.Sherwood), RECOVERED by NYJ-M.Fitzpatrick at NYJ 25."
        self.assertEqual(playTypeBeforeFumble(19, description), 2)
        self.assertEqual(passingYardsOnPlay(19, description, 72), 39)

    def test_strip_sack_is_a_sack(self):
        description = "(Shotgun) M.Penix sacked at ATL 14 for -8 yards (K.Gordon). FUMBLES (K.Gordon) [K.Gordon], RECOVERED by CHI-D.Bush at ATL 28. D.Bush to ATL 28 for no gain (M.Bergeron)."
        self.assertEqual(playTypeBeforeFumble(19, description), 4)
        self.assertEqual(passingYardsOnPlay(19, description, 78), 0)

    def test_fumbled_run_and_aborted_snap_are_carries(self):
        self.assertEqual(playTypeBeforeFumble(19, "M.Lloyd left tackle to GB 16 for 2 yards (K.Enagbare; D.Davis). FUMBLES (K.Enagbare), touched at GB 17, RECOVERED by NYJ-H.Phillips at GB 18."), 1)
        self.assertEqual(playTypeBeforeFumble(17, "(No Huddle, Shotgun) B.Nix FUMBLES (Aborted) at DEN 22, and recovers at DEN 22."), 1)

    def test_fumbled_snap_thrown_away_is_an_incompletion(self):
        description = "(Shotgun) C.Humphrey to KC 46 for -1 yards. FUMBLES, recovered by KC-P.Mahomes at KC 43. P.Mahomes pass incomplete short right to K.Walker."
        self.assertEqual(playTypeBeforeFumble(17, description), 3)

    def test_fumbled_interception_is_an_interception(self):
        description = "(Shotgun) T.Shough pass short left intended for B.Lance INTERCEPTED by H.Masses [M.Koonce] at NO 43. H.Masses to NO 8 for 35 yards (J.Johnson). FUMBLES (J.Johnson), touched at NO 7, recovered by LV-A.Butler at NO 4."
        self.assertEqual(playTypeBeforeFumble(17, description), 15)
        self.assertEqual(passingYardsOnPlay(17, description, 57), 0)

    def test_fumbled_catch_in_summary_wording(self):
        description = "Bryce Young Pass Complete for 21 Yds to Tetairoa McMillan Tetairoa McMillan Fumble Devin Bush 0 Yd Fumble Recovery"
        self.assertEqual(playTypeBeforeFumble(19, description), 2)
        self.assertEqual(passingYardsOnPlay(19, description), 21)

    def test_catch_reversed_to_an_incompletion(self):
        description = "(Shotgun) S.Rhyan to GB 33 for -5 yards. FUMBLES, recovered by GB-J.Love at GB 33. J.Love pass short right to L.Musgrave to GB 40 for 2 yards (D.Flannigan-Fowles). FUMBLES (D.Flannigan-Fowles), RECOVERED by NYG-D.Flannigan-Fowles at GB 41.The Replay Official reviewed the pass completion ruling, and the play was REVERSED.(Shotgun) S.Rhyan to GB 33 for -5 yards. FUMBLES, recovered by GB-J.Love at GB 33. J.Love pass incomplete short right to L.Musgrave (D.Flannigan-Fowles)."
        self.assertEqual(playTypeBeforeFumble(17, description), 3)

    def test_fumbled_snap_then_a_catch(self):
        description = "(Shotgun) C.Humphrey to KC 16 for -4 yards. FUMBLES, recovered by KC-P.Mahomes at KC 16. P.Mahomes pass short left to K.Walker pushed ob at KC 31 for 11 yards (J.Barron)."
        self.assertEqual(playTypeBeforeFumble(17, description), 2)
        self.assertEqual(passingYardsOnPlay(17, description, 80), 11)
        self.assertEqual(receivingYardsOnPlay(description, 80), 11)

    def test_other_play_types_are_left_alone(self):
        self.assertEqual(playTypeBeforeFumble(3, "(Shotgun) D.Maye pass incomplete deep right to R.Doubs."), 3)
        self.assertEqual(passingYardsOnPlay(3, "(Shotgun) D.Maye pass incomplete deep right to R.Doubs."), 0)


class PassingYardsOnPlayTests(SimpleTestCase):
    def test_plain_catch(self):
        self.assertEqual(passingYardsOnPlay(2, "(Shotgun) D.Maye pass short left to E.Chism to LV 42 for 13 yards (E.Stokes).", 55), 13)

    def test_passer_gets_the_yards_after_a_lateral(self):
        description = "(Shotgun) D.Maye pass short middle to E.Chism to NE 43 for 4 yards. Lateral to T.Henderson pushed ob at LV 45 for 12 yards (N.Dean)."
        self.assertEqual(passingYardsOnPlay(2, description, 61), 16)
        # The catcher only gets the yards up to the lateral.
        self.assertEqual(yardsGainedOnPlay(description, 61), 4)

    def test_chain_of_laterals_after_a_tackled_catch(self):
        description = "(Shotgun) J.Herbert pass short left to Q.Johnston to CLV 33 for 26 yards. Lateral to J.Palmer to CLV 24 for 9 yards. Lateral to L.McConkey to CLV 30 for -6 yards. Lateral to J.Dobbins to CLV 20 for 10 yards (M.Emerson)."
        self.assertEqual(passingYardsOnPlay(2, description, 59), 39)
        description = "(Shotgun) B.Nix pass deep right to J.Reynolds to DEN 32 for 13 yards [Ca.Heyward]. Lateral to M.Mims ran ob at DEN 34 for 2 yards (D.Kazee)."
        self.assertEqual(passingYardsOnPlay(2, description, 81), 15)

    def test_lateral_takers_get_the_yards_they_carried_it(self):
        description = "(Shotgun) J.Herbert pass short left to Q.Johnston to CLV 33 for 26 yards. Lateral to J.Palmer to CLV 24 for 9 yards. Lateral to L.McConkey to CLV 30 for -6 yards. Lateral to J.Dobbins to CLV 20 for 10 yards (M.Emerson)."
        self.assertEqual(receivingYardsOnPlay(description, 59), 26)
        self.assertEqual(receivingYardsOnPlay(description, 59, LATERAL_RECEIVER_ROLE, "Joshua Palmer"), 9)
        self.assertEqual(receivingYardsOnPlay(description, 59, LATERAL_RECEIVER_ROLE, "Ladd McConkey"), -6)
        self.assertEqual(receivingYardsOnPlay(description, 59, LATERAL_RECEIVER_ROLE, "J.K. Dobbins"), 10)
        description = "(Shotgun) B.Purdy pass short left to M.Evans to SF 20 for 2 yards. Lateral to D.Samuel for 80 yards, TOUCHDOWN."
        self.assertEqual(receivingYardsOnPlay(description, 82, LATERAL_RECEIVER_ROLE, "Deebo Samuel Sr."), 80)

    def test_lateral_taker_is_matched_by_initial_too(self):
        description = "(Shotgun) C.Williams pass short right to R.Odunze to ATL 40 for 2 yards. Lateral to R.Johnson pushed ob at ATL 28 for 12 yards (H.Perkins)."
        self.assertEqual(receivingYardsOnPlay(description, 62, LATERAL_RECEIVER_ROLE, "Roschon Johnson"), 12)
        self.assertEqual(receivingYardsOnPlay(description, 62, LATERAL_RECEIVER_ROLE, "Jaylon Johnson"), 0)
        self.assertIsNotNone(descriptionNameRegex("Amon-Ra St. Brown").match("A.St. Brown to CAR 21"))
        self.assertIsNotNone(descriptionNameRegex("Ty Johnson").match("Ty.Johnson pushed ob"))

    def test_yards_after_a_fumble_are_not_the_passers(self):
        description = "(Shotgun) S.Buechele pass short middle to T.Kelce to KC 37 for 2 yards (J.Adams). FUMBLES (J.Adams), recovered by KC-J.Smith-Schuster at KC 37. J.Smith-Schuster to KC 32 for -5 yards. Lateral to S.Buechele to KC 31 for -1 yards."
        self.assertEqual(passingYardsOnPlay(2, description, 65), 2)

    def test_lateral_overturned_on_review(self):
        description = "(Shotgun) S.Rattler pass short middle to T.Hill to NO 32 for 5 yards. Lateral to A.Kamara to CHI 42 for 26 yards (J.Brisker).Chicago challenged the backward pass ruling, and the play was REVERSED.(Shotgun) S.Rattler pass short middle to T.Hill to NO 32 for 5 yards."
        self.assertEqual(passingYardsOnPlay(2, description, 73), 5)


from datetime import date, datetime, timezone
from unittest import mock

from django.test import TestCase

from nfl_db import crudLogic
from nfl_db.models import nflTeam, nflMatch, player, playerTeamTenure, playerWeekStatus, playerInjuryReport


def espnAthlete(espnId, name, positionAbbreviation = "WR", experienceYears = 4):
    return {
        'id': str(espnId), 'displayName': name, 'height': 72, 'weight': 200,
        'experience': {'years': experienceYears},
        'position': {'abbreviation': positionAbbreviation, 'parent': {'name': "Offense"}},
    }


class TeamRosterRefreshTests(TestCase):
    def setUp(self):
        self.dallas = nflTeam.objects.create(abbreviation = "DAL", teamName = "Cowboys", espnId = 6)
        self.giants = nflTeam.objects.create(abbreviation = "NYG", teamName = "Giants", espnId = 19)
        # Last year a Cowboy; ESPN now lists him on the Giants.
        self.mover = player.objects.create(espnId = 100, name = "Moved Receiver", team = self.dallas, playerPosition = 2, firstSeason = 2022)
        playerTeamTenure.objects.create(player = self.mover, team = self.dallas, startDate = datetime(2024, 9, 1, tzinfo = timezone.utc))
        self.stayer = player.objects.create(espnId = 200, name = "Staying Receiver", team = self.giants, playerPosition = 2, firstSeason = 2022)
        playerTeamTenure.objects.create(player = self.stayer, team = self.giants, startDate = datetime(2024, 9, 1, tzinfo = timezone.utc))

    def mockRosterResponse(self, athletes):
        response = mock.Mock()
        response.json.return_value = {'athletes': [{'items': athletes}]}
        return mock.patch('nfl_db.crudLogic.requests.get', return_value = response)

    def test_refresh_moves_players_to_their_current_team(self):
        with self.mockRosterResponse([espnAthlete(100, "Moved Receiver"), espnAthlete(200, "Staying Receiver"), espnAthlete(300, "New Rookie", experienceYears = 0)]):
            roster, movedPlayers = crudLogic.refreshTeamRosterFromApi(self.giants)

        self.mover.refresh_from_db()
        self.assertEqual(self.mover.team, self.giants)
        self.assertEqual(sorted(p.espnId for p in roster), [100, 200, 300])
        # Only the player who changed teams counts as moved, not the new one.
        self.assertEqual(movedPlayers, [{'name': "Moved Receiver", 'position': "WR", 'fromTeam': "DAL", 'toTeam': "NYG"}])

    def test_roster_entry_without_experience(self):
        # ESPN leaves experience off some roster entries.
        mover = espnAthlete(100, "Moved Receiver")
        del mover['experience']
        newcomer = espnAthlete(300, "New Lineman", positionAbbreviation = "G")
        del newcomer['experience']
        with self.mockRosterResponse([mover, newcomer]):
            roster, movedPlayers = crudLogic.refreshTeamRosterFromApi(self.giants)

        self.mover.refresh_from_db()
        self.assertEqual(self.mover.team, self.giants)
        self.assertEqual(self.mover.firstSeason, 2022)
        self.assertEqual(sorted(p.espnId for p in roster), [100, 300])

    def test_failed_request_changes_nothing(self):
        with mock.patch('nfl_db.crudLogic.requests.get', side_effect = Exception("timed out")):
            self.assertEqual(crudLogic.refreshTeamRosterFromApi(self.giants), ([], []))

    def test_team_roster_tab_pull_fresh(self):
        with self.mockRosterResponse([espnAthlete(100, "Moved Receiver")]):
            page = self.client.get('/players/', {'viewRosterTeam': "NYG", 'viewRosterSeason': "2026", 'viewRosterPullFresh': "1"})

        self.assertContains(page, "Moved Receiver (WR) &mdash; was DAL")

    def test_team_roster_tab_all_teams_hands_the_page_every_team(self):
        page = self.client.get('/players/', {'viewRosterTeam': "ALL", 'viewRosterSeason': "2026", 'viewRosterPullFresh': "1"})
        self.assertEqual(page.context['rosterPull']['teams'], ["DAL", "NYG"])

        page = self.client.get('/players/', {'viewRosterTeam': "ALL", 'viewRosterSeason': "2026"})
        self.assertNotIn('rosterPull', page.context)

    def test_roster_pull_step(self):
        with self.mockRosterResponse([espnAthlete(100, "Moved Receiver")]):
            data = self.client.get('/ajax/rosterPullStep/', {'team': "NYG"}).json()

        self.assertEqual(data['status'], "ok")
        self.assertEqual(data['moved'][0]['fromTeam'], "DAL")

    def test_availability_lists_the_team_the_row_was_stored_under(self):
        # player.team still says DAL, but the week's row is filed under NYG.
        playerWeekStatus.objects.create(player = self.mover, team = self.giants, yearOfSeason = 2026, weekOfSeason = 3)
        availability = crudLogic.buildAvailabilityFromDatabase("2026", "3", "NYG")
        self.assertEqual(availability['rows'][0]['team'], "NYG")


def espnInjury(espnId, status, details = None, shortComment = ""):
    injury = {
        'id': "9" + str(espnId), 'status': status, 'date': "2026-10-09T22:16Z",
        'shortComment': shortComment, 'longComment': "",
        'athlete': {'links': [{'href': "https://www.espn.com/nfl/player/_/id/" + str(espnId) + "/someone"}]},
    }
    if details != None:
        injury['details'] = details
    return injury


class InjuryReportTests(TestCase):
    def setUp(self):
        self.giants = nflTeam.objects.create(abbreviation = "NYG", teamName = "Giants", espnId = 19)
        self.dallas = nflTeam.objects.create(abbreviation = "DAL", teamName = "Cowboys", espnId = 6)
        # Week 4 played, week 5 next: reports pulled now are for week 5.
        nflMatch.objects.create(espnId = 1, yearOfSeason = 2026, weekOfSeason = 4, homeTeamEspnId = 19, awayTeamEspnId = 6,
                                datePlayed = datetime(2026, 10, 4, 17, tzinfo = timezone.utc), completed = True)
        nflMatch.objects.create(espnId = 2, yearOfSeason = 2026, weekOfSeason = 5, homeTeamEspnId = 6, awayTeamEspnId = 19,
                                datePlayed = datetime(2026, 10, 11, 17, tzinfo = timezone.utc), completed = False)
        self.receiver = player.objects.create(espnId = 100, name = "Hurt Receiver", team = self.giants, playerPosition = 2, firstSeason = 2022)
        self.healthy = player.objects.create(espnId = 200, name = "Healthy Back", team = self.giants, playerPosition = 4, firstSeason = 2022)

    def pullWith(self, injuries):
        response = mock.Mock()
        response.json.return_value = {'injuries': [{'id': "19", 'displayName': "New York Giants", 'injuries': injuries}]}
        # Friday before the week 5 game.
        with mock.patch('nfl_db.crudLogic.requests.get', return_value = response), \
             mock.patch('nfl_db.crudLogic.currentSeasonYear', return_value = 2026), \
             mock.patch('django.utils.timezone.now', return_value = datetime(2026, 10, 9, 18, tzinfo = timezone.utc)):
            return crudLogic.pullInjuryReports()

    def test_stores_the_injury_details_for_the_upcoming_week(self):
        self.pullWith([
            espnInjury(100, "Questionable", {'type': "Ankle", 'location': "Leg", 'detail': "Sprain", 'side': "Left", 'returnDate': "2026-10-11"}, "Limited in practice."),
            # Never on the report this week, so his "Active" entry isn't stored.
            espnInjury(200, "Active"),
        ])

        injuryReport = playerInjuryReport.objects.get()
        self.assertEqual((injuryReport.player, injuryReport.team, injuryReport.weekOfSeason), (self.receiver, self.giants, 5))
        self.assertEqual((injuryReport.status, injuryReport.injuryType, injuryReport.injurySide), ("Questionable", "Ankle", "Left"))
        self.assertEqual(injuryReport.returnDate, date(2026, 10, 11))
        self.assertEqual(injuryReport.reportedAt, datetime(2026, 10, 9, 22, 16, tzinfo = timezone.utc))

    def test_clearing_a_player_keeps_what_the_injury_was(self):
        self.pullWith([espnInjury(100, "Questionable", {'type': "Ankle", 'detail': "Sprain"}, "Limited in practice.")])
        self.pullWith([espnInjury(100, "Active")])

        injuryReport = playerInjuryReport.objects.get()
        self.assertEqual((injuryReport.status, injuryReport.injuryType, injuryReport.shortComment), ("Active", "Ankle", "Limited in practice."))

    def test_injury_status_tab(self):
        self.pullWith([
            espnInjury(100, "Questionable", {'type': "Ankle", 'detail': "Sprain", 'side': "Not Specified"}),
            espnInjury(200, "Out", {'type': "Hamstring"}),
        ])

        page = self.client.get('/players/', {'injuryTeam': "NYG", 'injurySeason': "2026", 'injuryWeek': "5"})
        # Out sorts ahead of Questionable.
        self.assertEqual([r.player.name for r in page.context['injuryReports']], ["Healthy Back", "Hurt Receiver"])
        self.assertContains(page, "Ankle \u2013 Sprain")
        self.assertNotContains(page, "Not Specified")

        page = self.client.get('/players/', {'injuryTeam': "DAL", 'injurySeason': "2026", 'injuryWeek': "5"})
        self.assertContains(page, "No injury report stored for DAL in week 5 of 2026.")


def gameRosterEntry(espnId, didNotPlay = False, valid = True):
    return {'playerId': espnId, 'didNotPlay': didNotPlay, 'valid': valid}


class GameDayAvailabilityTests(TestCase):
    def setUp(self):
        self.ravens = nflTeam.objects.create(abbreviation = "BAL", teamName = "Ravens", espnId = 33)
        self.bills = nflTeam.objects.create(abbreviation = "BUF", teamName = "Bills", espnId = 2)
        nflMatch.objects.create(espnId = 1, yearOfSeason = 2026, weekOfSeason = 4, homeTeamEspnId = 33, awayTeamEspnId = 2,
                                datePlayed = datetime(2026, 10, 4, 17, tzinfo = timezone.utc), completed = True)
        # Sunday night, 7:20 Central, and not yet marked completed.
        nflMatch.objects.create(espnId = 2, yearOfSeason = 2026, weekOfSeason = 5, homeTeamEspnId = 2, awayTeamEspnId = 33,
                                datePlayed = datetime(2026, 10, 12, 0, 20, tzinfo = timezone.utc), completed = False)
        nflMatch.objects.create(espnId = 3, yearOfSeason = 2026, weekOfSeason = 6, homeTeamEspnId = 33, awayTeamEspnId = 2,
                                datePlayed = datetime(2026, 10, 18, 17, tzinfo = timezone.utc), completed = False)
        self.receiver = player.objects.create(espnId = 100, name = "Ravens Receiver", team = self.ravens, playerPosition = 2, firstSeason = 2022)

    def statuses(self):
        return list(playerWeekStatus.objects.filter(player = self.receiver, weekOfSeason = 5).order_by('reportDate').values_list('reportDate', 'playerStatus'))

    def test_game_roster_overrides_the_injury_pulls_status(self):
        # The injury pull had him Out on Friday, but he played on Sunday.
        playerWeekStatus.objects.create(player = self.receiver, team = self.ravens, yearOfSeason = 2026, weekOfSeason = 5,
                                        reportDate = date(2026, 10, 9), playerStatus = 4)

        availability = crudLogic.processGameRosterForAvailability({'entries': [gameRosterEntry(100)]}, self.ravens, 2026, 5)

        self.assertEqual(availability[0][1].playerStatus, 1)
        # Friday's report is kept as the week's history.
        self.assertEqual(self.statuses(), [(date(2026, 10, 9), 4), (date(2026, 10, 11), 1)])
        stored = crudLogic.buildAvailabilityFromDatabase("2026", "5", "BAL")
        self.assertEqual([s['label'] for s in stored['rows'][0]['statuses']], ["Out", "Available"])

    def test_pulling_again_updates_the_game_day_row(self):
        crudLogic.processGameRosterForAvailability({'entries': [gameRosterEntry(100, didNotPlay = True)]}, self.ravens, 2026, 5)
        crudLogic.processGameRosterForAvailability({'entries': [gameRosterEntry(100)]}, self.ravens, 2026, 5)

        self.assertEqual(self.statuses(), [(date(2026, 10, 11), 1)])

    def test_roster_before_kickoff_only_marks_inactives_out(self):
        # Before kickoff ESPN has every player at valid: false.
        inactive = player.objects.create(espnId = 101, name = "Ravens Inactive", team = self.ravens, playerPosition = 2, firstSeason = 2022)
        availability = crudLogic.processGameRosterForAvailability({'entries': [
            gameRosterEntry(100, valid = False), gameRosterEntry(101, didNotPlay = True, valid = False),
        ]}, self.ravens, 2026, 5)

        self.assertEqual({row[0].name: row[1].playerStatus for row in availability}, {"Ravens Receiver": 1, "Ravens Inactive": 4})

    def test_after_the_game_a_player_who_never_got_on_the_field_is_out(self):
        backup = player.objects.create(espnId = 101, name = "Ravens Backup", team = self.ravens, playerPosition = 2, firstSeason = 2022)
        availability = crudLogic.processGameRosterForAvailability({'entries': [
            gameRosterEntry(100), gameRosterEntry(101, valid = False),
        ]}, self.ravens, 2026, 5)

        self.assertEqual({row[0].name: row[1].playerStatus for row in availability}, {"Ravens Receiver": 1, "Ravens Backup": 4})

    def test_reports_after_kickoff_count_toward_the_next_game(self):
        # Monday morning: week 5 has been played but the scores pull hasn't
        # marked it completed yet.
        with mock.patch('django.utils.timezone.now', return_value = datetime(2026, 10, 12, 16, tzinfo = timezone.utc)):
            self.assertEqual(crudLogic.getCurrentWeekForTeam(33, 2026), 6)

        with mock.patch('django.utils.timezone.now', return_value = datetime(2026, 10, 11, 17, tzinfo = timezone.utc)):
            self.assertEqual(crudLogic.getCurrentWeekForTeam(33, 2026), 5)

    def test_questionable_is_not_out_but_doubtful_is(self):
        for reportDay, playerStatus in [(7, 2), (8, 3), (9, 4), (10, 6)]:
            playerWeekStatus.objects.create(player = self.receiver, team = self.ravens, yearOfSeason = 2026, weekOfSeason = 5,
                                            reportDate = date(2026, 10, reportDay), playerStatus = playerStatus)

        stored = crudLogic.buildAvailabilityFromDatabase("2026", "5", "BAL")
        self.assertEqual([(s['label'], s['token']) for s in stored['rows'][0]['statuses']],
                         [("Questionable", "available"), ("Doubtful", "out"), ("Out", "out"), ("IR", "out")])


from nfl_db.views import sortInjuries


class SortInjuriesTests(SimpleTestCase):
    def injury(self, name, position, status):
        return playerWeekStatus(player = player(name = name, playerPosition = position), playerStatus = status)

    def test_out_quarterback_goes_first(self):
        injuries = [self.injury("Tackle", 6, 2), self.injury("Guard", 6, 4), self.injury("Quarterback", 1, 4)]
        self.assertEqual([i.player.name for i in sortInjuries(injuries)], ["Quarterback", "Tackle", "Guard"])

    def test_questionable_quarterback_keeps_status_order(self):
        injuries = [self.injury("Guard", 6, 4), self.injury("Quarterback", 1, 2), self.injury("Tackle", 6, 3)]
        self.assertEqual([i.player.name for i in sortInjuries(injuries)], ["Quarterback", "Tackle", "Guard"])
        injuries = [self.injury("Guard", 6, 2), self.injury("Quarterback", 1, 2)]
        self.assertEqual([i.player.name for i in sortInjuries(injuries)], ["Guard", "Quarterback"])


class GameDataPullTests(TestCase):
    def setUp(self):
        nflTeam.objects.create(abbreviation = "BUF", teamName = "Bills", espnId = 2)
        nflTeam.objects.create(abbreviation = "NYJ", teamName = "Jets", espnId = 20)

    def gameResponse(self):
        response = mock.Mock()
        response.json.return_value = {'competitions': [{'competitors': [{'id': "2"}, {'id': "20"}]}]}
        return response

    def test_load_hands_the_page_the_weeks_to_pull(self):
        page = self.client.get('/getGames/', {'season': "2023", 'startWeek': "3", 'endWeek': "5"})
        self.assertEqual(page.context['gamePull']['weeks'], [3, 4, 5])
        self.assertNotIn('message', page.context)

    def test_finished_pull_keeps_the_dropdowns_and_pulls_nothing(self):
        page = self.client.get('/getGames/', {'season': "2023", 'startWeek': "3", 'endWeek': "5", 'pulled': "1"})
        self.assertNotIn('gamePull', page.context)
        self.assertEqual(page.context['message'], "Games loaded for Week 3 through Week 5 of 2023 season.")
        self.assertRegex(page.content.decode(), r'<option value="2023"\s+selected')
        self.assertContains(page, '<option value="3" selected> 3</option>', count = 1)
        self.assertContains(page, '<option value="5" selected> 5</option>', count = 1)

    def test_super_bowl_is_espn_playoff_week_five(self):
        # ESPN's playoff week 4 is the Pro Bowl.
        response = mock.Mock()
        response.json.return_value = {'items': [{'$ref': "http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/events/401547378?lang=en&region=us"}]}
        with mock.patch('nfl_db.crudLogic.requests.get', return_value = response) as get:
            self.assertEqual(crudLogic.gameIdsForWeek(2023, 22), ["401547378"])
        self.assertIn('/seasons/2023/types/3/weeks/5/events', get.call_args[0][0])

    def test_game_pull_step(self):
        with mock.patch('nfl_db.crudLogic.requests.get', return_value = self.gameResponse()), \
             mock.patch('nfl_db.crudLogic.processGameData') as processGameData:
            data = self.client.get('/ajax/gamePullStep/', {'season': "2023", 'week': "3", 'game': "401547353"}).json()

        self.assertEqual(data, {'status': "pulled", 'label': "BUF vs. NYJ"})
        processGameData.assert_called_once_with(mock.ANY, 3, 2023)

    def test_game_pull_step_reports_what_could_not_be_stored(self):
        problem = ["There was an exception when pulling game 401547353 from week 3 of year 2023.", "Line 12: x = y", {'drives': 1}, "4015473532"]
        with mock.patch('nfl_db.crudLogic.requests.get', return_value = self.gameResponse()), \
             mock.patch('nfl_db.crudLogic.processGameData', side_effect = Exception([problem])):
            data = self.client.get('/ajax/gamePullStep/', {'season': "2023", 'week': "3", 'game': "401547353"}).json()

        self.assertEqual(data['status'], "error")
        self.assertEqual(data['label'], "BUF vs. NYJ")
        self.assertEqual(data['problems'][0]['heading'], problem[0])
        self.assertEqual(data['problems'][0]['detail'], "Line 12: x = y")
        self.assertIn('"drives": 1', data['problems'][0]['data'])

    def test_game_pull_step_reports_a_crash(self):
        with mock.patch('nfl_db.crudLogic.requests.get', side_effect = Exception("timed out")):
            data = self.client.get('/ajax/gamePullStep/', {'season': "2023", 'week': "3", 'game': "401547353"}).json()
        self.assertEqual(data, {'status': "error", 'error': "timed out"})
