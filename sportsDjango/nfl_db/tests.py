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

    def test_summary_wording_of_2021_touchdowns(self):
        self.assertEqual(passingYardsOnPlay(2, "DJ Moore Pass From Sam Darnold for 2 Yrds Z.Gonzalez extra point is GOOD, Center-J.Jansen, Holder-J.Charlton.", 2), 2)
        self.assertEqual(passingYardsOnPlay(2, "Mike Evans Pass From Tom Brady for 1 Yard R.Succop extra point is GOOD, Center-C.Tinker, Holder-B.Pinion.", 1), 1)
        self.assertEqual(yardsGainedOnPlay("Taysom Hill 44 Yard Rush B.Maher extra point is GOOD, Center-Z.Wood, Holder-B.Gillikin.", 44), 44)

    def test_description_that_is_only_a_two_point_try(self):
        description = "TWO-POINT CONVERSION ATTEMPT. L.Jackson pass to M.Andrews is incomplete. ATTEMPT FAILS.\nPenalty on DET-B.Branch, Defensive Holding, offsetting, enforced at DET 2 - No Play."
        # Used to raise: nothing is left of the description once the try is set aside.
        self.assertEqual(passingYardsOnPlay(19, description, 2), 0)
        self.assertEqual(yardsGainedOnPlay(description, 2), 0)

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


class MissingPlayTextTests(SimpleTestCase):
    # ESPN's HOU vs. MIA (2024 week 15) feed has a fake punt with only shortText.
    def playsPage(self):
        return {'pageCount': 1, 'items': [
            {'id': "1", 'text': "C.Stroud pass incomplete deep right to J.Metchie.", 'shortText': "Stroud pass incomplete"},
            {'id': "2", 'shortText': "Dare Ogunbowale 35 Yd Rush Elijah Campbell 5 Yd Pnlty"},
        ]}

    def test_play_pages_fall_back_to_the_short_text(self):
        plays = crudLogic.playByPlayData(self.playsPage())
        plays.addJSON(self.playsPage())
        for page in plays.playByPlayPages:
            self.assertEqual([play['text'] for play in page['items']],
                ["C.Stroud pass incomplete deep right to J.Metchie.", "Dare Ogunbowale 35 Yd Rush Elijah Campbell 5 Yd Pnlty"])

    def test_drive_pages_fall_back_to_the_short_text(self):
        response = mock.Mock()
        response.json.return_value = {'pageCount': 1, 'items': [{'id': "10", 'plays': self.playsPage()}, {'id': "11"}]}
        with mock.patch('nfl_db.crudLogic.requests.get', return_value = response):
            drives = crudLogic.drivesDataObj("http://drives?lang=en")
        self.assertEqual(drives.drivesPages[0]['items'][0]['plays']['items'][1]['text'], "Dare Ogunbowale 35 Yd Rush Elijah Campbell 5 Yd Pnlty")

    def test_one_bad_drive_does_not_stop_the_rest(self):
        drives = mock.Mock(drivesPages = [{'items': [{'id': "1"}, {'id': "2"}]}, {'items': [{'id': "3"}]}])

        def createDrive(individualDrive, matchData):
            if individualDrive['id'] == "1":
                raise KeyError('text')

        with mock.patch('nfl_db.crudLogic.createDriveOfPlay', side_effect = createDrive) as createDriveOfPlay:
            problems = crudLogic.storeDrives(drives, None)

        self.assertEqual([call.args[0]['id'] for call in createDriveOfPlay.call_args_list], ["1", "2", "3"])
        self.assertEqual(len(problems), 1)
        self.assertEqual(problems[0][1], {'id': "1"})


from decimal import Decimal
from nfl_db import propLines


def espnProp(line, updated = '2026-11-14T07:48Z', openLine = None, over = None, under = None):
    current = {'target': {'value': line}}
    if over != None:
        current['over'] = {'american': over}
    if under != None:
        current['under'] = {'american': under}
    prop = {'current': current, 'lastUpdated': updated}
    if openLine != None:
        prop['open'] = {'target': {'value': openLine}}
    return prop


class PropMainLineTests(SimpleTestCase):
    def test_draftkings_line_listed_twice_without_odds(self):
        line = propLines.mainLine([espnProp(269.5, openLine = 270.5), espnProp(269.5, openLine = 270.5)])
        self.assertEqual(line['line'], Decimal('269.5'))
        self.assertEqual(line['openLine'], Decimal('270.5'))
        self.assertIsNone(line['overOdds'])
        self.assertIsNone(line['underOdds'])

    def test_espn_bet_main_line_is_the_one_with_odds(self):
        props = [espnProp(149.5), espnProp(216.5, over = '-115'), espnProp(216.5, under = '-105'), espnProp(349.5)]
        line = propLines.mainLine(props)
        self.assertEqual(line['line'], Decimal('216.5'))
        self.assertEqual((line['overOdds'], line['underOdds']), (-115, -105))

    def test_plus_and_even_odds(self):
        line = propLines.mainLine([espnProp(0.5, over = '+140'), espnProp(0.5, under = 'EVEN')])
        self.assertEqual((line['overOdds'], line['underOdds']), (140, 100))

    def test_stale_pair_gives_way_to_the_newest_line(self):
        props = [espnProp(215.5, '2026-11-10T04:16Z'), espnProp(215.5, '2026-11-10T04:16Z'),
                 espnProp(218.5, '2026-11-10T04:14Z'), espnProp(218.5, '2026-11-10T04:14Z')]
        self.assertEqual(propLines.mainLine(props)['line'], Decimal('215.5'))

    def test_lines_that_disagree_at_the_same_time_are_skipped(self):
        self.assertIsNone(propLines.mainLine([espnProp(37.5), espnProp(36.5)]))

    def test_alternate_lines_without_any_odds_are_skipped(self):
        self.assertIsNone(propLines.mainLine([espnProp(149.5), espnProp(216.5), espnProp(349.5)]))


class PropTypeTests(SimpleTestCase):
    def test_full_game_over_unders_are_kept(self):
        for name in ['Total Receiving Yards (incl. overtime)', 'Longest Reception (incl. overtime)', 'Total Defensive Interceptions']:
            self.assertTrue(propLines.isFullGameOverUnder(name), name)

    def test_ladders_scorers_and_partial_game_lines_are_left_out(self):
        for name in ['Receiving Yards Milestones', 'Anytime Touchdown Scorer', '1st Half Total Receiving Yards', 'Football Player Prop']:
            self.assertFalse(propLines.isFullGameOverUnder(name), name)

    def test_labels(self):
        self.assertEqual(propLines.propTypeLabel('Total Receiving Yards (incl. overtime)'), 'Receiving Yards')
        self.assertEqual(propLines.propTypeLabel('Longest Rush (incl. overtime)'), 'Longest Rush')


from nfl_db import bettingModelV3, businessLogic
from nfl_db.models import bettingModelResult


def v3Game(year, week, home, away, homePoints, awayPoints, neutral = False):
    return bettingModelV3.pastGame(year, week, home, away, homePoints, awayPoints, neutral)


def v3League(year = 2024, weeks = 12, homeEdge = 1, extraPoints = None):
    """Four teams whose scores follow the model exactly: 20 points, plus the
    offense's strength, minus the defense's, plus or minus homeEdge."""
    offense = {1: 6, 2: 2, 3: -2, 4: -6}
    defense = {1: 3, 2: -3, 3: 3, 4: -3}
    pairings = [((1, 2), (3, 4)), ((1, 3), (2, 4)), ((1, 4), (2, 3))]
    games = []
    for week in range(1, weeks + 1):
        for teamA, teamB in pairings[(week - 1) % 3]:
            # Swap who hosts every time the pairings come round again.
            home, away = (teamA, teamB) if ((week - 1) // 3) % 2 == 0 else (teamB, teamA)
            homePoints = 20 + offense[home] - defense[away] + homeEdge
            awayPoints = 20 + offense[away] - defense[home] - homeEdge
            if extraPoints != None:
                homePoints += extraPoints(week, home)
                awayPoints += extraPoints(week, away)
            games.append(v3Game(year, week, home, away, homePoints, awayPoints))
    return games


class BettingModelV3RatingTests(SimpleTestCase):
    def test_ratings_recover_the_teams_behind_the_scores(self):
        ratings = bettingModelV3.fitRatings(v3League(), 2024, 13, shrinkageGames = 0.001)
        self.assertAlmostEqual(ratings.homeFieldPoints, 2.0, places = 3)
        self.assertAlmostEqual(ratings.leagueAveragePoints, 20, delta = 0.05)
        # Team 1 is 9 points better than average, team 4 is 9 worse.
        self.assertAlmostEqual(ratings.overallRating(1), 9, delta = 0.05)
        self.assertAlmostEqual(ratings.overallRating(4), -9, delta = 0.05)
        self.assertAlmostEqual(ratings.offenseRating(2), 2, delta = 0.05)
        self.assertAlmostEqual(ratings.defenseRating(3), 3, delta = 0.05)
        self.assertEqual(ratings.rankings()[1], (1, 1, 1))
        self.assertEqual(ratings.rankings()[4][2], 4)

    def test_expected_score_adds_home_field_and_both_matchups(self):
        ratings = bettingModelV3.fitRatings(v3League(), 2024, 13, shrinkageGames = 0.001)
        homePoints, awayPoints = ratings.expectedPoints(1, 4)
        # Margin: 2 for home field + 9 - (-9). Total: 40, plus 0.8 of the teams' lean
        # toward scoring ((6 + 3) + (-6 - 3) = 0).
        self.assertAlmostEqual(homePoints - awayPoints, 20, delta = 0.11)
        self.assertAlmostEqual(homePoints + awayPoints, 40, delta = 0.11)
        neutralHome, neutralAway = ratings.expectedPoints(1, 4, neutralStadium = True)
        self.assertAlmostEqual(neutralHome - neutralAway, 18, delta = 0.11)

    def test_totals_lean_only_part_of_the_way(self):
        ratings = bettingModelV3.fitRatings(v3League(), 2024, 13, shrinkageGames = 0.001)
        # Team 1's offense against team 2's poor defense leans the game 8 points over.
        homePoints, awayPoints = ratings.expectedPoints(1, 2)
        self.assertAlmostEqual(homePoints + awayPoints, 40 + bettingModelV3.TOTAL_RATING_WEIGHT * 8, delta = 0.11)

    def test_points_against_a_good_defense_count_for_more(self):
        # Teams 1 and 2 both score 24; team 1 did it against the stingy defense.
        games = []
        for week in range(1, 9):
            games.append(v3Game(2024, week, 1, 3, 24, 10))
            games.append(v3Game(2024, week, 2, 4, 24, 30))
            games.append(v3Game(2024, week, 5, 3, 10, 10))
            games.append(v3Game(2024, week, 6, 4, 30, 30))
        ratings = bettingModelV3.fitRatings(games, 2024, 9)
        self.assertGreater(ratings.offenseRating(1), ratings.offenseRating(2) + 2)
        self.assertGreater(ratings.offenseRating(1), 0)
        self.assertLess(ratings.offenseRating(2), 0)

    def test_shrinkage_pulls_ratings_toward_average(self):
        games = v3League(weeks = 3)
        barelyShrunk = bettingModelV3.fitRatings(games, 2024, 4, shrinkageGames = 0.001)
        shrunk = bettingModelV3.fitRatings(games, 2024, 4)
        self.assertLess(abs(shrunk.overallRating(1)), abs(barelyShrunk.overallRating(1)) * 0.7)
        self.assertGreater(shrunk.overallRating(1), 0)

    def test_recent_games_count_more(self):
        # Team 1's offense finds 14 extra points a game from week 9 on.
        games = v3League(extraPoints = lambda week, team: 14 if team == 1 and week >= 9 else 0)
        shortMemory = bettingModelV3.fitRatings(games, 2024, 13, halfLifeWeeks = 2, shrinkageGames = 0.001)
        longMemory = bettingModelV3.fitRatings(games, 2024, 13, halfLifeWeeks = 1000, shrinkageGames = 0.001)
        self.assertGreater(shortMemory.offenseRating(1), longMemory.offenseRating(1) + 2)

    def test_last_season_is_older_than_the_calendar_says(self):
        lastWeekOfLastSeason = v3Game(2023, 18, 1, 2, 20, 20)
        self.assertEqual(bettingModelV3.gameAgeInWeeks(lastWeekOfLastSeason, 2024, 1), 1 - 18 + bettingModelV3.WEEKS_BETWEEN_SEASONS)
        self.assertEqual(bettingModelV3.gameAgeInWeeks(v3Game(2024, 3, 1, 2, 20, 20), 2024, 5), 2)

    def test_only_earlier_weeks_of_this_season_and_last_are_used(self):
        games = [
            v3Game(2022, 18, 1, 2, 20, 20),
            v3Game(2023, 18, 1, 2, 20, 20),
            v3Game(2024, 4, 1, 2, 20, 20),
            v3Game(2024, 5, 1, 2, 20, 20),
            v3Game(2024, 6, 1, 2, 20, 20),
        ]
        usable = bettingModelV3.gamesBeforeWeek(games, 2024, 5)
        self.assertEqual([(game.yearOfSeason, game.weekOfSeason) for game in usable], [(2023, 18), (2024, 4)])

    def test_home_field_is_pulled_toward_the_prior(self):
        self.assertEqual(bettingModelV3.homeFieldPoints([]), bettingModelV3.HOME_FIELD_PRIOR_POINTS)
        blowouts = [v3Game(2024, 1, 1, 2, 30, 20)] * bettingModelV3.HOME_FIELD_PRIOR_GAMES
        self.assertAlmostEqual(bettingModelV3.homeFieldPoints(blowouts), 6.0)
        # Neutral-site games say nothing about home field.
        self.assertEqual(bettingModelV3.homeFieldPoints([v3Game(2024, 1, 1, 2, 50, 0, neutral = True)]), bettingModelV3.HOME_FIELD_PRIOR_POINTS)

    def test_no_earlier_games(self):
        ratings = bettingModelV3.fitRatings([], 2024, 1)
        self.assertFalse(ratings.hasEnoughGames)
        self.assertEqual(ratings.overallRating(1), 0.0)


class BettingModelV3EdgeTests(SimpleTestCase):
    def prediction(self, modelSpread, bookSpread, actualSpread, modelTotal = 44, bookTotal = 44, actualTotal = 44):
        return bettingModelV3.predictedGame(2024, 5, modelSpread, modelTotal, bookSpread, bookTotal, actualSpread, actualTotal)

    def test_edges(self):
        # Model has the home team by 6, the book by 3.
        self.assertEqual(bettingModelV3.spreadEdge(-6.0, Decimal('-3.0')), 3.0)
        self.assertEqual(bettingModelV3.spreadEdge(2.5, Decimal('-3.0')), -5.5)
        self.assertEqual(bettingModelV3.totalEdge(47.5, Decimal('44.5')), 3.0)

    def test_cover_probability(self):
        self.assertEqual(bettingModelV3.coverProbability(0), 0.5)
        self.assertAlmostEqual(bettingModelV3.coverProbability(bettingModelV3.MARGIN_STANDARD_DEVIATION), 0.8413, places = 3)
        self.assertAlmostEqual(bettingModelV3.coverProbability(3) + bettingModelV3.coverProbability(-3), 1)

    def test_bet_record(self):
        predictions = [
            self.prediction(-6.0, -3.0, -7),    # took the home team -3, won by 7
            self.prediction(-6.0, -3.0, -3),    # won by exactly 3: push
            self.prediction(1.0, -3.0, -10),    # took the away team +3, lost by 10
            self.prediction(-3.5, -3.0, -20),   # half a point apart: no bet at a 1 point minimum
        ]
        self.assertEqual(bettingModelV3.betRecord(predictions, 1), (1, 1, 1))
        self.assertEqual(bettingModelV3.betRecord(predictions, 0), (2, 1, 1))
        totals = [self.prediction(0, 0, 0, modelTotal = 48, bookTotal = 44.5, actualTotal = 51), self.prediction(0, 0, 0, modelTotal = 40, bookTotal = 44.5, actualTotal = 51)]
        self.assertEqual(bettingModelV3.betRecord(totals, 1, betOnTotals = True), (1, 1, 0))

    def test_evaluation(self):
        summary = bettingModelV3.evaluatePredictions([self.prediction(-6.0, -3.0, -7), self.prediction(1.0, -2.0, -10, modelTotal = 40, bookTotal = 45, actualTotal = 50)])
        self.assertEqual(summary['games'], 2)
        self.assertEqual(summary['modelSpreadError'], 6.0)
        self.assertEqual(summary['bookSpreadError'], 6.0)
        self.assertEqual(summary['modelTotalError'], 5.0)
        self.assertEqual(summary['bookTotalError'], 2.5)
        self.assertIsNone(bettingModelV3.evaluatePredictions([]))


class BettingModelV3BetTests(SimpleTestCase):
    def result(self, homePoints, awayPoints, bookSpread, bookTotal, actual = None):
        modelResult = businessLogic.individualV3ModelResult("KC", "DEN", homePoints, awayPoints)
        modelResult.bookProvidedSpread = bookSpread
        modelResult.bookProvidedTotal = bookTotal
        if actual != None:
            modelResult.gameCompleted = True
            modelResult.actualSpread = actual[1] - actual[0]
            modelResult.actualTotal = actual[0] + actual[1]
        return businessLogic.setModelBetsV3(modelResult)

    def test_spread_and_total_follow_the_expected_score(self):
        modelResult = businessLogic.individualV3ModelResult("KC", "DEN", 27.3, 20.1)
        self.assertEqual(modelResult.calculatedSpread, -7.2)
        self.assertEqual(modelResult.calculatedTotal, 47.4)

    def test_home_team_laying_points(self):
        modelResult = self.result(27.0, 20.0, Decimal('-3.5'), Decimal('44.5'))
        self.assertEqual((modelResult.spreadEdge, modelResult.spreadEdgeTeam), (3.5, "KC"))
        self.assertEqual(modelResult.lineBet, "KC -3.5")
        self.assertEqual((modelResult.totalEdge, modelResult.overUnderBet), (2.5, "OVER"))
        # Nothing is graded before the game is played.
        self.assertEqual((modelResult.lineBetIsCorrect, modelResult.overUnderBetIsCorrect), ("None", "None"))

    def test_away_team_getting_points(self):
        modelResult = self.result(21.0, 20.0, Decimal('-6.5'), Decimal('48.0'))
        self.assertEqual((modelResult.spreadEdge, modelResult.spreadEdgeTeam), (-5.5, "DEN"))
        self.assertEqual(modelResult.lineBet, "DEN +6.5")
        self.assertEqual(modelResult.overUnderBet, "UNDER")

    def test_passes_inside_the_minimum_edge(self):
        modelResult = self.result(23.4, 20.0, Decimal('-3.0'), Decimal('44.0'), actual = (30, 10))
        self.assertEqual((modelResult.lineBet, modelResult.overUnderBet), ("PASS", "PASS"))
        self.assertEqual((modelResult.lineBetIsCorrect, modelResult.overUnderBetIsCorrect), ("None", "None"))

    def test_pick_em_line(self):
        self.assertEqual(self.result(24.0, 20.0, Decimal('0.0'), Decimal('44.0')).lineBet, "KC ML")

    def test_grading(self):
        won = self.result(27.0, 20.0, Decimal('-3.5'), Decimal('44.5'), actual = (31, 20))
        self.assertEqual((won.lineBetIsCorrect, won.overUnderBetIsCorrect), ("True", "True"))
        lost = self.result(27.0, 20.0, Decimal('-3.5'), Decimal('44.5'), actual = (20, 17))
        self.assertEqual((lost.lineBetIsCorrect, lost.overUnderBetIsCorrect), ("False", "False"))
        push = self.result(27.0, 20.0, Decimal('-3.0'), Decimal('45.0'), actual = (24, 21))
        self.assertEqual((push.lineBetIsCorrect, push.overUnderBetIsCorrect), ("Push", "Push"))
        awayCovered = self.result(21.0, 20.0, Decimal('-6.5'), Decimal('48.0'), actual = (24, 20))
        self.assertEqual((awayCovered.lineBetIsCorrect, awayCovered.overUnderBetIsCorrect), ("True", "True"))

    def test_no_book_lines_means_no_bets(self):
        modelResult = self.result(27.0, 20.0, None, None)
        self.assertEqual((modelResult.lineBet, modelResult.overUnderBet), ("", ""))
        self.assertIsNone(modelResult.spreadEdge)

    def test_biggest_disagreements_rank_first(self):
        small = self.result(24.0, 20.0, Decimal('-3.0'), Decimal('44.0'))
        bigLine = self.result(30.0, 20.0, Decimal('-3.0'), Decimal('50.0'))
        bigTotal = self.result(24.0, 20.0, Decimal('-4.0'), Decimal('35.0'))
        ranked = businessLogic.setBetRankings([small, bigLine, bigTotal], "v3")
        self.assertEqual(ranked, [bigTotal, bigLine, small])
        self.assertEqual([modelResult.betRankScore for modelResult in ranked], [9.0, 7.0, 1.0])


class BettingModelV3PageTests(TestCase):
    def setUp(self):
        for espnId, abbreviation in ((1, "AAA"), (2, "BBB"), (3, "CCC"), (4, "DDD")):
            nflTeam.objects.create(abbreviation = abbreviation, teamName = abbreviation, espnId = espnId)
        self.nextEspnId = 1000
        for game in v3League(year = 2024, weeks = 12):
            self.match(game.yearOfSeason, game.weekOfSeason, game.homeTeamEspnId, game.awayTeamEspnId, game.homeTeamPoints, game.awayTeamPoints)
        # Week 13: one game already played, one still to come.
        self.played = self.match(2024, 13, 1, 4, 31, 13, line = Decimal('-14.5'), total = Decimal('41.5'))
        self.upcoming = self.match(2024, 13, 2, 3, None, None, line = Decimal('-1.0'), total = Decimal('40.5'))
        patcher = mock.patch.object(bettingModelV3, 'MINIMUM_GAMES_FOR_RATINGS', 10)
        patcher.start()
        self.addCleanup(patcher.stop)

    def match(self, year, week, home, away, homePoints, awayPoints, line = None, total = None):
        self.nextEspnId += 1
        return nflMatch.objects.create(
            espnId = self.nextEspnId, yearOfSeason = year, weekOfSeason = week, homeTeamEspnId = home, awayTeamEspnId = away,
            completed = homePoints != None, homeTeamPoints = homePoints, awayTeamPoints = awayPoints,
            homeTeamTotalYards = 300, awayTeamTotalYards = 300, matchLineHomeTeam = line, overUnderLine = total)

    def test_predicts_from_earlier_weeks_only(self):
        played, upcoming = businessLogic.getModelResultsForMatches([self.played, self.upcoming], "v3")
        # AAA is far better than DDD in the earlier weeks; this week's 31-13 is not in the ratings.
        self.assertLess(played.calculatedSpread, -10)
        self.assertEqual((played.team1ActualPoints, played.actualSpread, played.actualTotal), (31, -18, 44))
        self.assertTrue(played.gameCompleted)
        self.assertFalse(upcoming.gameCompleted)
        self.assertEqual(upcoming.bookProvidedTotal, Decimal('40.5'))
        self.assertIn(upcoming.overUnderBet, ("OVER", "UNDER", "PASS"))

    def test_played_games_are_stored_and_read_back_the_same(self):
        computed = businessLogic.getModelResultsForMatches([self.played, self.upcoming], "v3")[0]
        stored = bettingModelResult.objects.get(modelVersion = "v3")
        self.assertEqual(stored.nflMatch, self.played)
        with mock.patch.object(bettingModelV3.modelData, 'ratingsForWeek', side_effect = AssertionError("should have used the stored result")):
            readBack = businessLogic.getModelResultsForMatches([self.played], "v3")[0]
        self.assertIsInstance(readBack, businessLogic.individualV3ModelResult)
        for attribute in ('team1Name', 'team2Name', 'team1CalculatedPoints', 'team2CalculatedPoints', 'calculatedSpread', 'calculatedTotal',
                          'spreadEdge', 'totalEdge', 'lineBet', 'lineBetIsCorrect', 'overUnderBet', 'overUnderBetIsCorrect'):
            self.assertEqual(getattr(readBack, attribute), getattr(computed, attribute), attribute)

    def test_not_enough_history_makes_no_prediction(self):
        opener = self.match(2020, 1, 1, 2, 20, 17, line = Decimal('-3.0'), total = Decimal('44.0'))
        modelResult = businessLogic.getModelResultsForMatches([opener], "v3")[0]
        self.assertTrue(modelResult.emptyModel)
        self.assertEqual((modelResult.lineBet, modelResult.overUnderBet), ("", ""))

    def test_weekly_summary_and_breakdown_pages(self):
        for url in ('/loadModelSummary/', '/loadModel/'):
            page = self.client.get(url, {'season': "2024", 'week': "13", 'model': "v3", 'movingavg': "5"})
            self.assertEqual(page.status_code, 200)
            results = page.context['modelResults']
            self.assertEqual(len(results), 2)
            # The ratings behind each prediction are attached for display.
            self.assertEqual(results[0].team1OverallRank + results[0].team2OverallRank, 5)
            self.assertContains(page, "Offense Rating")

    def test_yearly_summary_page(self):
        page = self.client.get('/loadYearlySummary/', {'season': "2024", 'model': "v3", 'movingavg': "5", 'topNumResults': "20"})
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "disagrees with the book most")


def v3QuarterbackGame(year, week, team, passer, yardsPerDropback, dropbacks = 40, starter = None):
    return bettingModelV3.quarterbackGame(year, week, team, starter if starter != None else passer, passer, dropbacks, yardsPerDropback * dropbacks)


def v3PassingLeague(weeks = 10):
    """Team 1's quarterback (id 10) passes for 8 adjusted yards a dropback; teams
    2 to 4 (ids 20, 30, 40) pass for 6."""
    games = []
    for week in range(1, weeks + 1):
        games.append(v3QuarterbackGame(2024, week, 1, 10, 8.0))
        for team in (2, 3, 4):
            games.append(v3QuarterbackGame(2024, week, team, team * 10, 6.0))
    return games


class BettingModelV3QuarterbackTests(SimpleTestCase):
    def test_adjusted_passing_yards(self):
        self.assertEqual(bettingModelV3.adjustedPassingYards(300, 2, 1, 15), 280)
        # Sack yards count against the passer whichever sign they are stored with.
        self.assertEqual(bettingModelV3.adjustedPassingYards(300, 2, 1, -15), 280)

    def test_no_passing_on_record(self):
        self.assertIsNone(bettingModelV3.fitQuarterbackValues([], 2024, 5))
        ratings = bettingModelV3.fitRatings(v3League(), 2024, 13)
        self.assertEqual(ratings.quarterbackAdjustment(1, 10), 0.0)

    def test_values_are_points_per_game_against_the_league(self):
        quarterbacks = bettingModelV3.fitQuarterbackValues(v3PassingLeague(), 2024, 11)
        self.assertAlmostEqual(quarterbacks.leagueAverage, 6.5)
        # Someone nobody has seen is 2 yards a dropback below the league: 6 points a game.
        self.assertAlmostEqual(quarterbacks.pointsAboveAverage(99), -6.0)
        self.assertAlmostEqual(quarterbacks.pointsAboveUnproven(99), 0.0)
        self.assertGreater(quarterbacks.pointsAboveAverage(10), quarterbacks.pointsAboveAverage(20) + 3)

    def test_a_quarterback_is_pulled_toward_the_unproven_level(self):
        games = v3PassingLeague() + [v3QuarterbackGame(2024, 10, 5, 50, 12.0)]
        quarterbacks = bettingModelV3.fitQuarterbackValues(games, 2024, 11)
        unproven = quarterbacks.leagueAverage - bettingModelV3.UNPROVEN_QUARTERBACK_PENALTY
        # One 40-dropback game moves him less than a fifth of the way to 12.
        self.assertGreater(quarterbacks.yardsPerDropback[50], unproven)
        self.assertLess(quarterbacks.yardsPerDropback[50], unproven + (12.0 - unproven) / 5)

    def test_the_usual_quarterback_changes_nothing(self):
        quarterbacks = bettingModelV3.fitQuarterbackValues(v3PassingLeague(), 2024, 11)
        self.assertAlmostEqual(quarterbacks.adjustment(1, 10), 0.0)

    def test_an_unseen_backup_costs_a_good_team_more(self):
        quarterbacks = bettingModelV3.fitQuarterbackValues(v3PassingLeague(), 2024, 11)
        self.assertLess(quarterbacks.adjustment(1, 99), -5)
        self.assertLess(quarterbacks.adjustment(1, 99), quarterbacks.adjustment(2, 99) - 3)
        self.assertLess(quarterbacks.adjustment(2, 99), 0)

    def test_the_starter_coming_back_adds_points(self):
        # Team 1's starter missed the last three games; a poor backup (id 11) played them.
        games = [game for game in v3PassingLeague() if not (game.teamEspnId == 1 and game.weekOfSeason >= 8)]
        games += [v3QuarterbackGame(2024, week, 1, 11, 4.0) for week in (8, 9, 10)]
        quarterbacks = bettingModelV3.fitQuarterbackValues(games, 2024, 11)
        self.assertGreater(quarterbacks.adjustment(1, 10), 1)
        self.assertLess(quarterbacks.adjustment(1, 11), -1)

    def test_unknown_starter_or_team_means_no_adjustment(self):
        quarterbacks = bettingModelV3.fitQuarterbackValues(v3PassingLeague(), 2024, 11)
        self.assertEqual(quarterbacks.adjustment(1, None), 0.0)
        self.assertEqual(quarterbacks.adjustment(7, 10), 0.0)

    def test_only_earlier_weeks_count(self):
        games = v3PassingLeague() + [v3QuarterbackGame(2024, 11, 1, 10, 0.0), v3QuarterbackGame(2024, 12, 1, 10, 0.0)]
        self.assertEqual(
            bettingModelV3.fitQuarterbackValues(games, 2024, 11).yardsPerDropback[10],
            bettingModelV3.fitQuarterbackValues(v3PassingLeague(), 2024, 11).yardsPerDropback[10])

    def test_expected_starter_is_whoever_started_last(self):
        # Week 10: the starter (10) was hurt early and the backup (11) threw most of the passes.
        games = [game for game in v3PassingLeague() if not (game.teamEspnId == 1 and game.weekOfSeason == 10)]
        games.append(v3QuarterbackGame(2024, 10, 1, 11, 5.0, starter = 10))
        quarterbacks = bettingModelV3.fitQuarterbackValues(games, 2024, 11)
        self.assertEqual(quarterbacks.expectedStarter(1), 10)
        self.assertEqual(quarterbacks.expectedStarter(1, unavailable = {10}), 11)
        self.assertEqual(quarterbacks.expectedStarter(1, unavailable = {10, 11}), bettingModelV3.UNPROVEN_QUARTERBACK)
        self.assertIsNone(quarterbacks.expectedStarter(7))
        # The stand-in for "nobody we know" is valued as unproven.
        self.assertAlmostEqual(quarterbacks.pointsAboveUnproven(bettingModelV3.UNPROVEN_QUARTERBACK), 0.0)

    def test_adjustments_move_each_teams_expected_score(self):
        ratings = bettingModelV3.fitRatings(v3League(), 2024, 13)
        homePoints, awayPoints = ratings.expectedPoints(1, 4)
        adjustedHome, adjustedAway = ratings.expectedPoints(1, 4, homeQuarterbackPoints = -3.0, awayQuarterbackPoints = 1.0)
        self.assertAlmostEqual(adjustedHome, homePoints - 3.0, delta = 0.11)
        self.assertAlmostEqual(adjustedAway, awayPoints + 1.0, delta = 0.11)


class BettingModelV3QuarterbackDataTests(TestCase):
    def setUp(self):
        from nfl_db.models import driveOfPlay, playByPlay, passerStatSplit, teamMatchPerformance
        self.home = nflTeam.objects.create(abbreviation = "AAA", teamName = "AAA", espnId = 1)
        self.away = nflTeam.objects.create(abbreviation = "BBB", teamName = "BBB", espnId = 2)
        self.match = nflMatch.objects.create(espnId = 5001, yearOfSeason = 2024, weekOfSeason = 3, homeTeamEspnId = 1, awayTeamEspnId = 2,
                                             completed = True, homeTeamPoints = 20, awayTeamPoints = 17)
        self.nextWeek = nflMatch.objects.create(espnId = 5002, yearOfSeason = 2024, weekOfSeason = 4, homeTeamEspnId = 2, awayTeamEspnId = 1)
        drive = driveOfPlay.objects.create(nflMatch = self.match, teamOnOffense = self.home, reachedRedZone = False)
        self.starter = player.objects.create(espnId = 10, name = "Starting Passer", playerPosition = 1)
        self.backup = player.objects.create(espnId = 11, name = "Backup Passer", playerPosition = 1)
        self.receiver = player.objects.create(espnId = 12, name = "Trick Receiver", playerPosition = 2)

        def passPlay(sequenceNumber, passer, playType = 2, copies = 1):
            play = playByPlay.objects.create(nflMatch = self.match, teamOnOffense = self.home, driveOfPlay = drive, playType = playType,
                                             sequenceNumber = sequenceNumber, turnover = False, penaltyOnPlay = False, scoringPlay = False)
            for copy in range(copies):
                passerStatSplit.objects.create(play = play, player = passer)

        passPlay(50, self.receiver)                  # trick play on the first snap
        passPlay(100, self.starter)
        passPlay(200, self.starter, playType = 4)    # sacked and hurt
        for sequenceNumber in (300, 400, 500):
            passPlay(sequenceNumber, self.backup)
        passPlay(600, self.backup, playType = 3, copies = 2)    # stored twice

        teamMatchPerformance.objects.create(matchEspnId = 5001, teamEspnId = 1, yearOfSeason = 2024, weekOfSeason = 3,
                                            passingAttempts = 6, sacksTaken = 1, totalPassingYards = 80, passingTouchdowns = 1,
                                            interceptionsOnOffense = 0, sackYardsLost = Decimal('8.0'))

    def test_passing_line_goes_to_the_main_passer_and_the_first_dropback_starts(self):
        quarterbackGames, names = bettingModelV3.loadSeasonQuarterbackGames(2024)
        self.assertEqual(len(quarterbackGames), 1)
        game = quarterbackGames[0]
        self.assertEqual((game.yearOfSeason, game.weekOfSeason, game.teamEspnId), (2024, 3, 1))
        # The backup's four plays outnumber the starter's two, the duplicate row not counting.
        self.assertEqual((game.starterId, game.passerId), (self.starter.id, self.backup.id))
        self.assertEqual((game.dropbacks, game.adjustedYards), (7, 80 + 20 - 8))
        self.assertEqual(names[self.backup.id], "Backup Passer")

    def test_starter_of_a_played_game_and_of_the_next_one(self):
        data = bettingModelV3.modelData()
        played = data.startingQuarterback(2024, 3, 1)
        self.assertEqual((played.playerId, played.name, played.hasPlayed), (self.starter.id, "Starting Passer", True))
        expected = data.startingQuarterback(2024, 4, 1)
        self.assertEqual((expected.playerId, expected.hasPlayed), (self.starter.id, False))
        # No passing on record for the other team.
        self.assertIsNone(data.startingQuarterback(2024, 4, 2).playerId)

    def test_a_starter_listed_as_out_gives_way_to_the_backup(self):
        playerWeekStatus.objects.create(player = self.starter, team = self.home, yearOfSeason = 2024, weekOfSeason = 4, playerStatus = 4, reportDate = date(2024, 9, 27))
        self.assertEqual(bettingModelV3.modelData().startingQuarterback(2024, 4, 1).playerId, self.backup.id)
        self.assertEqual(bettingModelV3.modelData(usePregameNews = False).startingQuarterback(2024, 4, 1).playerId, self.starter.id)
        # Both out: somebody without a track record.
        playerWeekStatus.objects.create(player = self.backup, team = self.home, yearOfSeason = 2024, weekOfSeason = 4, playerStatus = 3, reportDate = date(2024, 9, 27))
        self.assertEqual(bettingModelV3.modelData().startingQuarterback(2024, 4, 1).playerId, bettingModelV3.UNPROVEN_QUARTERBACK)

    def test_only_the_latest_status_counts(self):
        # Out on Wednesday (and in an undated row), cleared on Friday; questionable is not out.
        playerWeekStatus.objects.create(player = self.starter, team = self.home, yearOfSeason = 2024, weekOfSeason = 4, playerStatus = 4, reportDate = date(2024, 9, 25))
        playerWeekStatus.objects.create(player = self.starter, team = self.home, yearOfSeason = 2024, weekOfSeason = 4, playerStatus = 4, reportDate = None)
        playerWeekStatus.objects.create(player = self.starter, team = self.home, yearOfSeason = 2024, weekOfSeason = 4, playerStatus = 1, reportDate = date(2024, 9, 27))
        playerWeekStatus.objects.create(player = self.backup, team = self.home, yearOfSeason = 2024, weekOfSeason = 4, playerStatus = 2, reportDate = date(2024, 9, 27))
        self.assertEqual(bettingModelV3.quarterbacksOut(2024, 4), set())
        playerWeekStatus.objects.create(player = self.backup, team = self.home, yearOfSeason = 2024, weekOfSeason = 4, playerStatus = 5, reportDate = date(2024, 9, 28))
        self.assertEqual(bettingModelV3.quarterbacksOut(2024, 4), {self.backup.id})

    def test_a_starter_picked_by_hand_is_used_until_the_game_is_played(self):
        bettingModelV3.chooseStartingQuarterback(1, 2024, 4, self.backup.id)
        picked = bettingModelV3.modelData().startingQuarterback(2024, 4, 1)
        self.assertEqual((picked.playerId, picked.name, picked.hasPlayed, picked.chosen), (self.backup.id, "Backup Passer", False, True))
        # The backtest guesses the way the model would have on its own.
        self.assertEqual(bettingModelV3.modelData(usePregameNews = False).startingQuarterback(2024, 4, 1).playerId, self.starter.id)
        # Picking again replaces the choice; picking nobody goes back to the model's guess.
        bettingModelV3.chooseStartingQuarterback(1, 2024, 4, self.receiver.id)
        self.assertEqual(bettingModelV3.modelData().startingQuarterback(2024, 4, 1).playerId, self.receiver.id)
        bettingModelV3.chooseStartingQuarterback(1, 2024, 4, None)
        notPicked = bettingModelV3.modelData().startingQuarterback(2024, 4, 1)
        self.assertEqual((notPicked.playerId, notPicked.chosen), (self.starter.id, False))

    def test_a_pick_for_a_game_already_played_changes_nothing(self):
        bettingModelV3.chooseStartingQuarterback(1, 2024, 3, self.backup.id)
        played = bettingModelV3.modelData().startingQuarterback(2024, 3, 1)
        self.assertEqual((played.playerId, played.hasPlayed, played.chosen), (self.starter.id, True, False))

    def test_picking_a_starter_on_the_page(self):
        from nfl_db.models import chosenStartingQuarterback
        pick = {'season': "2024", 'week': "4", 'team': "1", 'player': str(self.backup.id), 'returnTo': "summary"}
        response = self.client.post('/setStartingQuarterback/', pick)
        self.assertRedirects(response, '/loadModelSummary/?season=2024&week=4&model=v3&movingavg=5', fetch_redirect_response = False)
        self.assertEqual(chosenStartingQuarterback.objects.get().player, self.backup)

        response = self.client.post('/setStartingQuarterback/', dict(pick, player = "", returnTo = "breakdown"))
        self.assertRedirects(response, '/loadModel/?season=2024&week=4&model=v3&movingavg=5', fetch_redirect_response = False)
        self.assertEqual(chosenStartingQuarterback.objects.count(), 0)

        self.assertEqual(self.client.post('/setStartingQuarterback/', dict(pick, team = "99")).status_code, 400)
        self.assertEqual(self.client.post('/setStartingQuarterback/', dict(pick, player = "987654")).status_code, 400)
        self.assertEqual(self.client.post('/setStartingQuarterback/', {'season': "2024"}).status_code, 400)
        self.assertEqual(chosenStartingQuarterback.objects.count(), 0)
        self.assertRedirects(self.client.get('/setStartingQuarterback/'), '/loadModelSummary/', fetch_redirect_response = False)

    def test_pages_offer_the_teams_quarterbacks_for_an_upcoming_game(self):
        player.objects.filter(id__in = [self.starter.id, self.backup.id]).update(team = self.home)
        week = {'season': "2024", 'week': "4", 'model': "v3", 'movingavg': "5"}
        with mock.patch.object(bettingModelV3, 'MINIMUM_GAMES_FOR_RATINGS', 1):
            for url in ('/loadModelSummary/', '/loadModel/'):
                page = self.client.get(url, week)
                upcoming = page.context['modelResults'][0]
                self.assertEqual(upcoming.team2QuarterbackChoices, [(self.backup.id, "Backup Passer"), (self.starter.id, "Starting Passer")])
                self.assertContains(page, "Starting Passer (expected)")
                self.assertContains(page, '<label for="starter-1"')
                # The other team has no passing on record, so there is nothing to change.
                self.assertIsNone(upcoming.team1QuarterbackChoices)
                self.assertNotContains(page, '<label for="starter-2"')

            bettingModelV3.chooseStartingQuarterback(1, 2024, 4, self.backup.id)
            page = self.client.get('/loadModelSummary/', week)
            self.assertContains(page, "Backup Passer (chosen)")
            # The option that undoes the pick says who the model would go back to.
            self.assertContains(page, "Model's guess: Starting Passer")
            self.assertRegex(page.content.decode(), r'<option value="' + str(self.backup.id) + r'"\s+selected>Backup Passer</option>')

            # A played game keeps its actual starter and offers no picker.
            page = self.client.get('/loadModelSummary/', dict(week, week = "3"))
            self.assertIsNone(page.context['modelResults'][0].team1QuarterbackChoices)
            self.assertNotContains(page, "Change Starter:")

    def test_details_name_the_quarterback(self):
        with mock.patch.object(bettingModelV3, 'MINIMUM_GAMES_FOR_RATINGS', 1):
            results = businessLogic.getModelResultsForMatches([self.nextWeek], "v3")
            businessLogic.addV3RatingDetails([self.nextWeek], results)
        upcoming = results[0]
        # AAA is the away team next week.
        self.assertEqual((upcoming.team2Quarterback, upcoming.team2QuarterbackExpected), ("Starting Passer", True))
        self.assertAlmostEqual(upcoming.team2QuarterbackAdjustment, 0.0, delta = 2.0)
        self.assertIsNone(upcoming.team1Quarterback)


import io
from contextlib import redirect_stdout

from django.core.management import call_command

from nfl_db.models import driveOfPlay, playByPlay, passerStatSplit, rusherStatSplit, receiverStatSplit, returnerStatSplit, teamMatchPerformance


def espnParticipant(participantType, athleteEspnId, stats = None):
    participant = {
        'type': participantType,
        'athlete': {'$ref': "http://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/2024/athletes/" + str(athleteEspnId) + "?lang=en&region=us"},
    }
    if stats != None:
        # What ESPN used to send: the player's totals for the whole game.
        participant['stats'] = [{'name': name, 'value': value} for name, value in stats.items()]
    return participant


class StatSplitTestCase(TestCase):
    def setUp(self):
        self.offense = nflTeam.objects.create(abbreviation = "AAA", teamName = "AAA", espnId = 1)
        self.defense = nflTeam.objects.create(abbreviation = "BBB", teamName = "BBB", espnId = 2)
        self.match = nflMatch.objects.create(espnId = 6001, yearOfSeason = 2024, weekOfSeason = 3, homeTeamEspnId = 1, awayTeamEspnId = 2,
                                             completed = True, homeTeamPoints = 20, awayTeamPoints = 17)
        self.drive = driveOfPlay.objects.create(nflMatch = self.match, teamOnOffense = self.offense, reachedRedZone = False)
        self.passer = player.objects.create(espnId = 10, name = "Sam Passer", playerPosition = 1)
        self.catcher = player.objects.create(espnId = 12, name = "Ray Catcher", playerPosition = 2)
        self.runner = player.objects.create(espnId = 14, name = "Rob Runner", playerPosition = 4)
        self.defender = player.objects.create(espnId = 20, name = "Dee Back", playerPosition = 9)
        self.tenure = playerTeamTenure.objects.create(player = self.passer, team = self.offense)
        self.sequenceNumber = 0

    def play(self, playType, description, yardsFromEndzone = 60, yardsOnPlay = 0, **fields):
        self.sequenceNumber += 100
        fields = dict(dict(turnover = False, penaltyOnPlay = False, scoringPlay = False), **fields)
        return playByPlay.objects.create(nflMatch = self.match, teamOnOffense = self.offense, driveOfPlay = self.drive, playType = playType,
                                         sequenceNumber = self.sequenceNumber, playDescription = description,
                                         yardsFromEndzone = yardsFromEndzone, yardsOnPlay = yardsOnPlay, **fields)


class StatSplitWriterTests(StatSplitTestCase):
    def test_yards_are_the_plays_not_the_game_totals_espn_sends(self):
        catch = self.play(2, "(Shotgun) S.Passer pass short left to R.Catcher to AAA 43 for 14 yards (D.Back).", yardsOnPlay = 14)
        crudLogic.processPlayParticipants(catch, [
            espnParticipant('passer', 10, {'passingYards': 310}),
            espnParticipant('receiver', 12, {'receivingYards': 120}),
        ])
        carry = self.play(1, "R.Runner up the middle to AAA 45 for 5 yards (D.Back).", yardsOnPlay = 5)
        crudLogic.processPlayParticipants(carry, [espnParticipant('rusher', 14, {'rushingYards': 88})])

        self.assertEqual(passerStatSplit.objects.get(play = catch).passingYards, 14)
        self.assertEqual(receiverStatSplit.objects.get(play = catch).receivingYards, 14)
        self.assertEqual(rusherStatSplit.objects.get(play = carry).rushingYards, 5)

    def test_penalty_yards_are_not_the_players(self):
        # statYardage counts the 15 yards tacked on; the catch was 5.
        catch = self.play(2, "S.Passer pass short left to R.Catcher to AAA 45 for 5 yards (D.Back). PENALTY on BBB-D.Back, Unnecessary Roughness, 15 yards, enforced at AAA 45.", yardsOnPlay = 20)
        nullified = self.play(2, "S.Passer pass deep right to R.Catcher to BBB 30 for 30 yards (D.Back). PENALTY on AAA-R.Runner, Offensive Holding, 10 yards, enforced at AAA 40 - No Play.", yardsOnPlay = -10)
        for play in (catch, nullified):
            crudLogic.processPlayParticipants(play, [espnParticipant('passer', 10), espnParticipant('receiver', 12)])

        self.assertEqual(passerStatSplit.objects.get(play = catch).passingYards, 5)
        self.assertEqual(receiverStatSplit.objects.get(play = catch).receivingYards, 5)
        self.assertEqual(passerStatSplit.objects.get(play = nullified).passingYards, 0)
        self.assertEqual(receiverStatSplit.objects.get(play = nullified).receivingYards, 0)

    def test_sack_and_incompletion_gain_no_passing_yards(self):
        sack = self.play(4, "S.Passer sacked at AAA 32 for -8 yards (D.Back).", yardsOnPlay = -8)
        incompletion = self.play(3, "S.Passer pass incomplete short left to R.Catcher.")
        for play in (sack, incompletion):
            crudLogic.processPlayParticipants(play, [espnParticipant('passer', 10, {'passingYards': 310})])
        self.assertEqual(list(passerStatSplit.objects.order_by('id').values_list('passingYards', 'interception')), [(0, False), (0, False)])

    def test_interception_is_credited_to_the_passer(self):
        interception = self.play(15, "S.Passer pass short left intended for R.Catcher INTERCEPTED by D.Back at AAA 45. D.Back to AAA 40 for 5 yards (R.Catcher).", turnover = True)
        pickSix = self.play(16, "S.Passer pass deep right intended for R.Catcher INTERCEPTED by D.Back at BBB 30. D.Back for 70 yards, TOUCHDOWN.",
                            turnover = True, scoringPlay = True, offenseScored = False)
        fumbledReturn = self.play(19, "S.Passer pass short middle intended for R.Catcher INTERCEPTED by D.Back at AAA 30. D.Back to AAA 28 for 2 yards (R.Runner). FUMBLES (R.Runner), RECOVERED by AAA-R.Catcher at AAA 26.")
        for play in (interception, pickSix, fumbledReturn):
            crudLogic.processPlayParticipants(play, [espnParticipant('passer', 10), espnParticipant('returner', 20)])
            passerSplit = passerStatSplit.objects.get(play = play)
            self.assertEqual((passerSplit.player, passerSplit.currentTenure, passerSplit.interception, passerSplit.passingYards, passerSplit.passingTdScored),
                             (self.passer, self.tenure, True, 0, False))
            self.assertEqual(returnerStatSplit.objects.get(play = play).player, self.defender)

    def test_interception_wiped_out_by_a_penalty_is_not_one(self):
        nullified = self.play(15, "S.Passer pass short left intended for R.Catcher INTERCEPTED by D.Back at AAA 45. PENALTY on BBB-D.Back, Defensive Pass Interference, 12 yards, enforced at AAA 40 - No Play.")
        crudLogic.processPlayParticipants(nullified, [espnParticipant('passer', 10)])
        self.assertFalse(passerStatSplit.objects.get(play = nullified).interception)

    def test_pulling_a_play_again_writes_no_second_row(self):
        catch = self.play(2, "S.Passer pass short left to R.Catcher to AAA 43 for 14 yards (D.Back).", yardsOnPlay = 14)
        for pull in range(2):
            crudLogic.processPlayParticipants(catch, [espnParticipant('passer', 10), espnParticipant('receiver', 12)])
        self.assertEqual((passerStatSplit.objects.count(), receiverStatSplit.objects.count()), (1, 1))

    def test_lateral_takers_row_carries_their_yards(self):
        lateraled = self.play(2, "S.Passer pass short left to R.Catcher to AAA 44 for 4 yards. Lateral to R.Runner pushed ob at BBB 44 for 12 yards (D.Back).", yardsOnPlay = 16)
        crudLogic.processPlayParticipants(lateraled, [espnParticipant('passer', 10), espnParticipant('receiver', 12), espnParticipant('other', 14)])
        self.assertEqual(passerStatSplit.objects.get(play = lateraled).passingYards, 16)
        self.assertEqual(receiverStatSplit.objects.get(play = lateraled, player = self.catcher).receivingYards, 4)
        self.assertEqual(receiverStatSplit.objects.get(play = lateraled, player = self.runner).receivingYards, 12)

    def test_backfill_fetches_the_passer_of_an_interception(self):
        interception = self.play(15, "S.Passer pass short left intended for R.Catcher INTERCEPTED by D.Back at AAA 45.", espnId = 600101)
        returnerStatSplit.objects.create(play = interception, player = self.defender, returnType = 4)
        participants = {"600101": [espnParticipant('passer', 10), espnParticipant('returner', 20)]}
        commandPath = 'nfl_db.management.commands.backfillPlayStatSplitsCommand.'
        with mock.patch(commandPath + 'fetchPlayParticipantsForMatch', return_value = participants), mock.patch(commandPath + 'clock.sleep'), redirect_stdout(io.StringIO()):
            call_command('backfillPlayStatSplitsCommand', dryRun = True)
            self.assertEqual(passerStatSplit.objects.count(), 0)
            call_command('backfillPlayStatSplitsCommand')
        self.assertTrue(passerStatSplit.objects.get(play = interception, player = self.passer).interception)
        self.assertEqual(returnerStatSplit.objects.count(), 1)


class StatSplitRepairTests(StatSplitTestCase):
    def setUp(self):
        super().setUp()
        # A touchdown catch stored three times with the passer's game total; only the newest copy has the touchdown and the tenure.
        self.catch = self.play(2, "(Shotgun) S.Passer pass short left to R.Catcher for 14 yards, TOUCHDOWN.", yardsFromEndzone = 14, yardsOnPlay = 14, scoringPlay = True, offenseScored = True)
        for copy in range(3):
            newest = copy == 2
            passerStatSplit.objects.create(play = self.catch, player = self.passer, passingYards = 310, passingTdScored = newest, currentTenure = self.tenure if newest else None)
            receiverStatSplit.objects.create(play = self.catch, player = self.catcher, playerRole = 3, receivingYards = 120, receivingTdScored = newest)
        self.carry = self.play(1, "R.Runner up the middle to AAA 45 for 5 yards (D.Back).", yardsOnPlay = 5)
        rusherStatSplit.objects.create(play = self.carry, player = self.runner, playerRole = 2, rushingYards = 88)
        self.sack = self.play(4, "S.Passer sacked at AAA 32 for -8 yards (D.Back).", yardsOnPlay = -8)
        passerStatSplit.objects.create(play = self.sack, player = self.passer, passingYards = 310)
        # Already right: left alone.
        self.goodCatch = self.play(2, "S.Passer pass short right to R.Catcher to AAA 47 for 7 yards (D.Back).", yardsOnPlay = 7)
        passerStatSplit.objects.create(play = self.goodCatch, player = self.passer, passingYards = 7)
        receiverStatSplit.objects.create(play = self.goodCatch, player = self.catcher, playerRole = 3, receivingYards = 7)

        self.interception = self.play(15, "S.Passer pass short left intended for R.Catcher INTERCEPTED by D.Back at AAA 45. D.Back to AAA 40 for 5 yards (S.Passer).", turnover = True)
        returnerStatSplit.objects.create(play = self.interception, player = self.defender, returnType = 4)
        self.nullifiedInterception = self.play(15, "S.Passer pass deep left intended for R.Catcher INTERCEPTED by D.Back at BBB 20. PENALTY on BBB-D.Back, Defensive Holding, 5 yards, enforced at AAA 40 - No Play.")
        # ESPN's summary wording names no passer.
        self.pickSix = self.play(16, "Dee Back 34 Yd Interception Return (Kit Kicker Kick)", turnover = True, scoringPlay = True, offenseScored = False)

        teamMatchPerformance.objects.create(matchEspnId = 6001, teamEspnId = 1, yearOfSeason = 2024, weekOfSeason = 3, totalPassingYards = 21)

    def storedRows(self):
        return [list(splitModel.objects.order_by('id').values_list()) for splitModel in (passerStatSplit, rusherStatSplit, receiverStatSplit, returnerStatSplit)]

    def test_dry_run_reports_and_changes_nothing(self):
        before = self.storedRows()
        report = crudLogic.runStatSplitRepair()
        self.assertEqual(self.storedRows(), before)

        self.assertFalse(report['applied'])
        self.assertEqual([(entry['label'], entry['bySeason']) for entry in report['duplicates']],
                         [("passerStatSplit", {2024: 2}), ("rusherStatSplit", {}), ("receiverStatSplit", {2024: 2}), ("returnerStatSplit", {})])
        # The kept copy of the catch and the sack; the carry; the kept copy of the catch.
        self.assertEqual([(entry['label'], entry['bySeason']) for entry in report['yards']],
                         [("passerStatSplit.passingYards", {2024: 2}), ("rusherStatSplit.rushingYards", {2024: 1}), ("receiverStatSplit.receivingYards", {2024: 1})])
        self.assertEqual(report['yards'][1]['samples'][0]['player'], "Rob Runner")
        self.assertEqual((report['yards'][1]['samples'][0]['stored'], report['yards'][1]['samples'][0]['credited']), (88, 5))
        self.assertEqual((report['interceptions']['bySeason'], report['interceptions']['withoutPasserBySeason']), ({2024: 2}, {2024: 1}))
        self.assertEqual(report['interceptions']['samples'][0]['player'], "Sam Passer")
        self.assertIn("Interception Return", report['interceptions']['withoutPasserSamples'][0]['play'])
        self.assertEqual(report['totalChanges'], 4 + 4 + 2)
        self.assertEqual(report['boxScoreCheck'], [{'season': 2024, 'teamGames': 1, 'exact': 1, 'close': 1, 'largestGap': 0}])

    def test_apply_leaves_one_right_row_per_play(self):
        crudLogic.runStatSplitRepair(applyChanges = True)

        passerSplit = passerStatSplit.objects.get(play = self.catch)
        self.assertEqual((passerSplit.passingYards, passerSplit.passingTdScored, passerSplit.currentTenure), (14, True, self.tenure))
        receiverSplit = receiverStatSplit.objects.get(play = self.catch)
        self.assertEqual((receiverSplit.receivingYards, receiverSplit.receivingTdScored), (14, True))
        self.assertEqual(rusherStatSplit.objects.get(play = self.carry).rushingYards, 5)
        self.assertEqual(passerStatSplit.objects.get(play = self.sack).passingYards, 0)
        self.assertEqual(passerStatSplit.objects.get(play = self.goodCatch).passingYards, 7)

        thrown = passerStatSplit.objects.get(play = self.interception)
        self.assertEqual((thrown.player, thrown.currentTenure, thrown.interception, thrown.passingYards, thrown.playerRole), (self.passer, self.tenure, True, 0, 1))
        self.assertFalse(passerStatSplit.objects.get(play = self.nullifiedInterception).interception)
        self.assertFalse(passerStatSplit.objects.filter(play = self.pickSix).exists())
        self.assertEqual(sum(passerStatSplit.objects.values_list('passingYards', flat = True)), 21)
        self.assertEqual(returnerStatSplit.objects.count(), 1)

        # Nothing left to do the second time round.
        self.assertEqual(crudLogic.runStatSplitRepair()['totalChanges'], 0)

    def test_passer_must_be_on_the_offense(self):
        # Stored under AAA, but thrown by a passer who isn't one of theirs.
        visitor = player.objects.create(espnId = 30, name = "Vic Visitor", playerPosition = 1)
        misfiled = self.play(15, "V.Visitor pass short left intended for R.Catcher INTERCEPTED by D.Back at AAA 45.")
        found, withoutPasser = crudLogic.findInterceptionPassers()
        self.assertNotIn(misfiled.id, [passerFound['playId'] for passerFound in found])
        self.assertIn(misfiled.id, [playId for playId, season in withoutPasser])

        # On the team's roster that week, with no other pass in the game.
        playerWeekStatus.objects.create(player = visitor, team = self.offense, yearOfSeason = 2024, weekOfSeason = 3, playerStatus = 1)
        found, withoutPasser = crudLogic.findInterceptionPassers()
        self.assertIn((misfiled.id, visitor.id), [(passerFound['playId'], passerFound['playerId']) for passerFound in found])

    def test_only_the_season_asked_for(self):
        report = crudLogic.runStatSplitRepair(applyChanges = True, seasonYear = 2023)
        self.assertEqual(report['totalChanges'], 0)
        self.assertEqual(passerStatSplit.objects.filter(play = self.catch).count(), 3)

    def test_command_is_a_dry_run_unless_told_to_apply(self):
        before = self.storedRows()
        output = io.StringIO()
        with redirect_stdout(output):
            call_command('repairPlayStatSplitsCommand')
        self.assertEqual(self.storedRows(), before)
        self.assertIn("Dry run: nothing was changed. 10 rows would be deleted, corrected or added", output.getvalue())
        self.assertIn("passingYards 310 -> 14, 2024 wk 3, Sam Passer", output.getvalue())

        with redirect_stdout(output):
            call_command('repairPlayStatSplitsCommand', apply = True)
        self.assertEqual(passerStatSplit.objects.filter(play = self.catch).count(), 1)
        self.assertIn("Done. 10 rows deleted, corrected or added.", output.getvalue())

    def test_page_cleanup_keeps_the_newest_copy_too(self):
        crudLogic.runPlayerDataCleanup(applyChanges = True)
        self.assertTrue(passerStatSplit.objects.get(play = self.catch).passingTdScored)
        self.assertTrue(receiverStatSplit.objects.get(play = self.catch).receivingTdScored)
