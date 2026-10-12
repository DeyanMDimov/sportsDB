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


def gameRosterEntry(espnId, didNotPlay = False):
    return {'playerId': espnId, 'didNotPlay': didNotPlay, 'valid': True}


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
