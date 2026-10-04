from django.test import SimpleTestCase

from nfl_db.crudLogic import yardsGainedOnPlay


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


from datetime import datetime, timezone
from unittest import mock

from django.test import TestCase

from nfl_db import crudLogic
from nfl_db.models import nflTeam, player, playerTeamTenure, playerWeekStatus


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
