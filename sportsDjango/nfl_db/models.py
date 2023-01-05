from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator


# Create your models here.

class nflTeam(models.Model):
    geography = models.CharField(max_length = 30, default = "-")
    teamName = models.CharField(max_length = 20, default = "-")
    fullName = models.CharField(max_length = 50, default = "-")
    division = models.CharField(max_length = 10, default = "-")
    abbreviation = models.CharField(max_length = 3, default = "-")
    startYear = models.SmallIntegerField(validators = [MinValueValidator(2002)], default = 2002)
    endYear = models.SmallIntegerField(null = True, blank = True)
    espnId = models.SmallIntegerField(validators = [MinValueValidator(1), MaxValueValidator(34)], default = 1)

    

class nflMatch(models.Model):
    espnId                              = models.IntegerField(unique = True)
    datePlayed                          = models.DateTimeField(null = True, blank = True)
    homeTeam                            = models.ManyToManyField(nflTeam, related_name = 'homeTeam', blank = True)
    homeTeamEspnId                      = models.SmallIntegerField(null = True, blank = True)
    awayTeam                            = models.ManyToManyField(nflTeam, related_name = 'awayTeam', blank = True)
    awayTeamEspnId                      = models.SmallIntegerField(null = True, blank = True)
    completed                           = models.BooleanField(default = False)
    weekOfSeason                        = models.SmallIntegerField(validators = [MinValueValidator(-4), MaxValueValidator(22)], default = 0)
    yearOfSeason                        = models.SmallIntegerField(validators = [MinValueValidator(2002)], default = 2002)
    neutralStadium                      = models.BooleanField(default = False)
    overtime                            = models.BooleanField(default = False)
    playoffs                            = models.BooleanField(default = False)
    preseason                           = models.BooleanField(default = False)
    indoorStadium                       = models.BooleanField(default = False)
    temperatureForecast                 = models.SmallIntegerField(null = True, blank = True)
    precipitationTypes = (
        (0, "None"),
        (1, "Rain"),
        (2, "Snow")
    )
    precipitationForecast               = models.SmallIntegerField(choices = precipitationTypes, null=True, blank=True)
    precipitationStrengthForecast       = models.SmallIntegerField(null = True, blank = True,)
    windStrengthForecast                = models.SmallIntegerField(null = True, blank=True)
    temperature                         = models.SmallIntegerField(null = True, blank = True)
    precipitation                       = models.SmallIntegerField(choices = precipitationTypes, null=True, blank=True)
    precipitationStrength               = models.SmallIntegerField(null = True, blank = True,)
    windStrength                        = models.SmallIntegerField(null=True, blank=True)
    homeTeamPoints                      = models.SmallIntegerField(null = True, blank = True)
    homeTeamTotalYards                  = models.SmallIntegerField(null = True, blank = True)
    homeTeamRushingYards                = models.SmallIntegerField(null = True, blank = True)
    homeTeamReceivingYards              = models.SmallIntegerField(null = True, blank = True)
    homeTeamGiveaways                   = models.SmallIntegerField(null = True, blank = True)
    homeTeamExplosivePlays              = models.SmallIntegerField(null = True, blank = True)
    homeTeamPointsAllowed               = models.SmallIntegerField(null = True, blank = True)
    homeTeamYardsAllowed                = models.SmallIntegerField(null = True, blank = True)
    homeTeamRushYardsAllowed            = models.SmallIntegerField(null = True, blank = True)
    homeTeamReceivingYardsAllowed       = models.SmallIntegerField(null = True, blank = True)
    homeTeamTakeaways                   = models.SmallIntegerField(null = True, blank = True)
    homeTeamRushingTDScored             = models.SmallIntegerField(null = True, blank = True)
    homeTeamReceivingTDScored           = models.SmallIntegerField(null = True, blank = True)
    homeTeamRushingTDAllowed            = models.SmallIntegerField(null = True, blank = True)
    homeTeamReceivingTDAllowed          = models.SmallIntegerField(null = True, blank = True)
    homeTeamFGScored                    = models.SmallIntegerField(null = True, blank = True)
    homeTeamFGAllowed                   = models.SmallIntegerField(null = True, blank = True)
    homeTeamSpecialTeamsPointsScored    = models.SmallIntegerField(null = True, blank = True)
    homeTeamDefensePointsScored         = models.SmallIntegerField(null = True, blank = True)
    awayTeamPoints                      = models.SmallIntegerField(null = True, blank = True)
    awayTeamTotalYards                  = models.SmallIntegerField(null = True, blank = True)
    awayTeamRushingYards                = models.SmallIntegerField(null = True, blank = True)
    awayTeamReceivingYards              = models.SmallIntegerField(null = True, blank = True)
    awayTeamGiveaways                   = models.SmallIntegerField(null = True, blank = True)
    awayTeamExplosivePlays              = models.SmallIntegerField(null = True, blank = True)
    awayTeamPointsAllowed               = models.SmallIntegerField(null = True, blank = True)
    awayTeamYardsAllowed                = models.SmallIntegerField(null = True, blank = True)
    awayTeamRushYardsAllowed            = models.SmallIntegerField(null = True, blank = True)
    awayTeamReceivingYardsAllowed       = models.SmallIntegerField(null = True, blank = True)
    awayTeamTakeaways                   = models.SmallIntegerField(null = True, blank = True)
    awayTeamRushingTDScored             = models.SmallIntegerField(null = True, blank = True)
    awayTeamReceivingTDScored           = models.SmallIntegerField(null = True, blank = True)
    awayTeamRushingTDAllowed            = models.SmallIntegerField(null = True, blank = True)
    awayTeamReceivingTDAllowed          = models.SmallIntegerField(null = True, blank = True)
    awayTeamFGScored                    = models.SmallIntegerField(null = True, blank = True)
    awayTeamFGAllowed                   = models.SmallIntegerField(null = True, blank = True)
    awayTeamSpecialTeamsPointsScored    = models.SmallIntegerField(null = True, blank = True)
    awayTeamDefensePointsScored         = models.SmallIntegerField(null = True, blank = True)
    matchLineHomeTeam                   = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
    overUnderLine                       = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
    homeTeamMoneyLine                   = models.SmallIntegerField(null = True, blank = True)
    awayTeamMoneyLine                   = models.SmallIntegerField(null = True, blank = True)

class teamMatchPerformance(models.Model):
    matchEspnId     = models.IntegerField()
    nflMatch        = models.ManyToManyField(nflMatch)
    team            = models.ManyToManyField(nflTeam, related_name = "team", blank = True)
    teamEspnId      = models.SmallIntegerField(null = True, blank = True)
    opponent        = models.ManyToManyField(nflTeam, related_name = "opponent", blank = True)
    weekOfSeason    = models.SmallIntegerField(validators = [MinValueValidator(-4), MaxValueValidator(22)], default = 0)
    yearOfSeason    = models.SmallIntegerField(validators = [MinValueValidator(2002)], default = 2002)
    atHome          = models.BooleanField(null=True, blank=True)
    #general
    totalPointsScored       = models.SmallIntegerField(null = True, blank = True)
    totalPointsAllowed      = models.SmallIntegerField(null = True, blank = True)
    totalTouchdownsScored   = models.SmallIntegerField(null = True, blank = True)
    totalPenalties          = models.SmallIntegerField(null = True, blank = True)
    totalPenaltyYards       = models.SmallIntegerField(null = True, blank = True)
    #offense
    totalYardsGained            = models.SmallIntegerField(null = True, blank = True)
    totalExplosivePlays         = models.SmallIntegerField(null = True, blank = True)
    totalGiveaways              = models.SmallIntegerField(null = True, blank = True)
    redZoneAttempts             = models.SmallIntegerField(null = True, blank = True)
    redZoneTDConversionPct      = models.SmallIntegerField(null = True, blank = True)
    redZoneFumbles              = models.SmallIntegerField(null = True, blank = True)
    redZoneFumblesLost          = models.SmallIntegerField(null = True, blank = True)
    redZoneInterceptions        = models.SmallIntegerField(null = True, blank = True)
    totalOffensePenalties       = models.SmallIntegerField(null = True, blank = True)
    totalOffensePenaltyYards    = models.SmallIntegerField(null = True, blank = True)
    #offense-passing
    passCompletions             = models.SmallIntegerField(null = True, blank = True)
    passingAttempts             = models.SmallIntegerField(null = True, blank = True)
    passPlaysTwentyPlus     = models.SmallIntegerField(null = True, blank = True)
    totalPassingYards           = models.SmallIntegerField(null = True, blank = True)
    qbHitsTaken                 = models.SmallIntegerField(null = True, blank = True)
    sacksTaken                  = models.SmallIntegerField(null = True, blank = True)
    sackYardsLost               = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
    twoPtPassConversions        = models.SmallIntegerField(null = True, blank = True)
    twoPtPassAttempts           = models.SmallIntegerField(null = True, blank = True)
    #offense-rushing
    rushingAttempts             = models.SmallIntegerField(null = True, blank = True)
    rushingYards                = models.SmallIntegerField(null = True, blank = True)
    stuffsTaken                 = models.SmallIntegerField(null = True, blank = True)
    stuffYardsLost              = models.SmallIntegerField(null = True, blank = True)
    rushingPlaysTenPlus         = models.SmallIntegerField(null = True, blank = True)
    twoPtRushConversions        = models.SmallIntegerField(null = True, blank = True)
    twoPtRushAttempts           = models.SmallIntegerField(null = True, blank = True)
    totalReceivingYards         = models.SmallIntegerField(null = True, blank = True)
    receivingYardsAfterCatch    = models.SmallIntegerField(null = True, blank = True)
    interceptionsOnOffense      = models.SmallIntegerField(null = True, blank = True)
    passingFumbles              = models.SmallIntegerField(null = True, blank = True)
    passingFumblesLost          = models.SmallIntegerField(null = True, blank = True)
    rushingFumbles              = models.SmallIntegerField(null = True, blank = True)
    rushingFumblesLost          = models.SmallIntegerField(null = True, blank = True)
    #defense
    totalPointsAllowedByDefense     = models.SmallIntegerField(null = True, blank = True)
    totalYardsAllowedByDefense      = models.SmallIntegerField(null = True, blank = True)
    totalPassYardsAllowed           = models.SmallIntegerField(null = True, blank = True)
    totalRushYardsAllowed           = models.SmallIntegerField(null = True, blank = True)
    totalTakeaways                  = models.SmallIntegerField(null = True, blank = True)
    defensiveTouchdownsScored       = models.SmallIntegerField(null = True, blank = True)
    passesBattedDown                = models.SmallIntegerField(null = True, blank = True)
    qbHits                          = models.SmallIntegerField(null = True, blank = True)
    defenseSacks                    = models.SmallIntegerField(null = True, blank = True)
    sackYardsGained                 = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
    safetiesScored                  = models.SmallIntegerField(null = True, blank = True)
    defenseStuffs                   = models.SmallIntegerField(null = True, blank = True)
    defenseInterceptions            = models.SmallIntegerField(null = True, blank = True)
    defenseInterceptionTouchdowns   = models.SmallIntegerField(null = True, blank = True)
    defenseInterceptionYards        = models.SmallIntegerField(null = True, blank = True)
    defenseForcedFumbles            = models.SmallIntegerField(null = True, blank = True)
    defenseFumblesRecovered         = models.SmallIntegerField(null = True, blank = True)
    defenseFumbleTouchdowns         = models.SmallIntegerField(null = True, blank = True)
    totalDefensePenalties           = models.SmallIntegerField(null = True, blank = True)
    totalDefensePenaltyYards        = models.SmallIntegerField(null = True, blank = True)
    firstDownsByPenaltyGiven        = models.SmallIntegerField(null = True, blank = True)
    #specialTeams
    blockedFieldGoals           = models.SmallIntegerField(null = True, blank = True)
    blockedFieldGoalTouchdowns  = models.SmallIntegerField(null = True, blank = True)
    blockedPunts                = models.SmallIntegerField(null = True, blank = True)
    blockedPuntTouchdowns       = models.SmallIntegerField(null = True, blank = True)
    specialTeamsPenalties       = models.SmallIntegerField(null = True, blank = True)
    specialTeamsPenaltyYards    = models.SmallIntegerField(null = True, blank = True)
    #punting
    totalPunts                  = models.SmallIntegerField(null = True, blank = True)
    opponentPinnedInsideTen     = models.SmallIntegerField(null = True, blank = True)
    opponentPinnedInsideFive    = models.SmallIntegerField(null = True, blank = True)
    #scoring
    passingTouchdowns           = models.SmallIntegerField(null = True, blank = True)
    rushingTouchdowns           = models.SmallIntegerField(null = True, blank = True)
    totalTwoPointConvs          = models.SmallIntegerField(null = True, blank = True)
    fieldGoalAttempts           = models.SmallIntegerField(null = True, blank = True)
    fieldGoalsMade              = models.SmallIntegerField(null = True, blank = True)
    extraPointAttempts          = models.SmallIntegerField(null = True, blank = True)
    extraPointsMade             = models.SmallIntegerField(null = True, blank = True)
    #down and distance
    firstDowns                  = models.SmallIntegerField(null = True, blank = True)
    firstDownsRushing           = models.SmallIntegerField(null = True, blank = True)
    firstDownsPassing           = models.SmallIntegerField(null = True, blank = True)
    firstDownsByPenalty         = models.SmallIntegerField(null = True, blank = True)
    thirdDownAttempts           = models.SmallIntegerField(null = True, blank = True)
    thirdDownConvs              = models.SmallIntegerField(null = True, blank = True)
    fourthDownAttempts          = models.SmallIntegerField(null = True, blank = True)
    fourthDownConvs             = models.SmallIntegerField(null = True, blank = True)
    drivePinnedInsideTen        = models.SmallIntegerField(null = True, blank = True)
    drivePinnedInsideFive       = models.SmallIntegerField(null = True, blank = True)
    rushPctFirstDown            = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
    passPctFirstDown            = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
    completionPctFirstDown      = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
    rushPctSecondDown           = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
    passPctSecondDown           = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
    completionPctSecondDown     = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
    rushPctThirdDown            = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
    passPctThirdDown            = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
    completionPctThirdDown      = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
    #miscellaneous
    twoPtReturns                = models.SmallIntegerField(null = True, blank = True)
    onePtSafetiesMade           = models.SmallIntegerField(null = True, blank = True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['matchEspnId', 'teamEspnId'], name="UniqueTeamsPerMatch")
        ]

class player(models.Model):
    name = models.CharField(max_length = 60, default = "-")
    firstSeason = models.SmallIntegerField(default = "2000")
    lastSeason = models.SmallIntegerField(null = True, blank = True)
    team = models.ForeignKey(nflTeam, on_delete = models.CASCADE, null = True, blank = True)

# class playByPlay(models.Model):
#     nflMatch = models.ForeignKey(nflMatch, on_delete = models.CASCADE)
#     teamOnOffense = models.ForeignKey(nflTeam, on_delete = models.CASCADE)
#     playTypes = (
#         (1, "RUSH"),
#         (2, "COMPLETED PASS"),
#         (3, "INCOMPLETE PASS"),
#         (4, "SACK"),
#         (5, "INTERCEPTION"),
#         (6, "OFFENSIVE FUMBLE RECOVERY"),
#         (7, "DEFENSIVE FUMBLE RECOVERY"),
#         (8, "PUNT"),
#         (9, "FG KICK"),
#         (10, "KICKOFF"),
#         (11, "PAT KICK"),
#         (12, "2PT CONVERSION"),
#         (13, "KNEEL"),
#         (14, "SPIKE"),
#         (15, "NO PLAY/BLOWN DEAD"),
#         (16, "TIMEOUT")
#     )
#     playType = models.SmallIntegerField(choices = playTypes, default = 1)
#     yardsFromEndzone = models.SmallIntegerField(null = True, blank = True)
#     yardsOnPlay = models.SmallIntegerField(null = True, blank = True)
#     playDown = models.SmallIntegerField(validators = [MinValueValidator(1), MaxValueValidator(4)], null = True, blank = True)
#     rusher = models.ManyToManyField(player, blank = True, related_name = 'ballCarrier')
#     passer = models.ManyToManyField(player, blank = True, related_name = 'passer')
#     reciever = models.ManyToManyField(player, blank = True, related_name = 'receiver')
#     kickReciever = models.ManyToManyField(player, blank = True, related_name = 'kickReceiver')
#     turnover = models.BooleanField()
#     penaltyOnPlay = models.BooleanField()
#     penaltyIsOnOffense = models.BooleanField(null = True, blank = True)
#     yardsGainedOrLostOnPenalty = models.SmallIntegerField(null = True, blank = True)
#     scoringPlay = models.BooleanField()
#     offenseScored = models.BooleanField(null = True, blank = True)
#     pointsScored = models.SmallIntegerField(null = True, blank = True)
    

    

# class playerMatchOffense(models.Model):
#     nflMatch = models.ForeignKey(nflMatch, on_delete = models.CASCADE)
#     team = models.ForeignKey(nflTeam, on_delete = models.CASCADE)
#     player = models.ManyToManyField(player, blank = True)
#     playerPositions = (
#         (1, "QB"),
#         (2, "WR"),
#         (3, "TE"),
#         (4, "RB"),
#         (5, "FB"),
#         (6, "O-Line"),
#         (7, "D-Line"),
#         (8, "LB"),
#         (9, "CB"),
#         (10, "S")
#     )
#     position = models.SmallIntegerField(choices = playerPositions, default = 1)
#     rushingYards = models.SmallIntegerField()
#     receivingYards = models.SmallIntegerField()
#     passingYards = models.SmallIntegerField()
#     rushingTDScored = models.PositiveSmallIntegerField()
#     receivingTDScored = models.PositiveSmallIntegerField()
#     passingTDScored = models.PositiveSmallIntegerField()

# class playerWeekStatus(models.Model):
#     player = models.ForeignKey(player, on_delete = models.CASCADE)
#     team = models.ForeignKey(nflTeam, on_delete = models.CASCADE, null = True, blank = True)
#     weekOfSeason = models.SmallIntegerField(validators = [MinValueValidator(-4), MaxValueValidator(22)])
#     yearOfSeason = models.SmallIntegerField(validators = [MinValueValidator(2002)])
#     reportDate = models.DateField()
#     playerStatuses = (
#         (1, "Available"),
#         (2, "Questionable"),
#         (3, "Doubtful"),
#         (4, "Out"),
#         (5, "Out For Season"),
#         (6, "IR")
#     )
#     playerStatus = models.SmallIntegerField(choices = playerStatuses, default = 1)






