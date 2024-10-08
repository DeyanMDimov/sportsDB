from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator




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
    divisionalMatch                     = models.BooleanField(default = False)
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
    redZoneTDConversions        = models.SmallIntegerField(null = True, blank = True)
    redZoneFumbles              = models.SmallIntegerField(null = True, blank = True)
    redZoneFumblesLost          = models.SmallIntegerField(null = True, blank = True)
    redZoneInterceptions        = models.SmallIntegerField(null = True, blank = True)
    totalOffensePenalties       = models.SmallIntegerField(null = True, blank = True)
    totalOffensePenaltyYards    = models.SmallIntegerField(null = True, blank = True)
    #offense-passing
    passCompletions             = models.SmallIntegerField(null = True, blank = True)
    passingAttempts             = models.SmallIntegerField(null = True, blank = True)
    passPlaysTwentyFivePlus     = models.SmallIntegerField(null = True, blank = True)
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

class teamMatchRoster(models.Model):
    nflMatch = models.ForeignKey(nflMatch, on_delete = models.CASCADE)
    nflTeam = models.ForeignKey(nflTeam, on_delete = models.CASCADE)

# class nflTeamSeasonByeWeek(models.Model):
#     nflTeam = models.ForeignKey(nflTeam, on_delete = models.CASCADE)
#     nflTeamEspnId = models.SmallIntegerField(null=True, blank=True)
#     yearOfSeason = models.SmallIntegerField(null = True, blank = True)
#     byeWeek = models.SmallIntegerField(null = True, blank = True)

# class nflTeamSchedule(models.Model):
#     nflTeam = models.ForeignKey(nflTeam, on_delete = models.CASCADE)
#     nflTeamEspnId = models.SmallIntegerField(null=True, blank=True)
#     yearOfSeason = models.SmallIntegerField(null = True, blank = True)



class driveOfPlay(models.Model):
    nflMatch = models.ForeignKey(nflMatch, on_delete = models.CASCADE)
    teamOnOffense = models.ForeignKey(nflTeam, on_delete = models.CASCADE)
    sequenceNumber = models.SmallIntegerField(null = True, blank = True)
    espnId = models.BigIntegerField(unique = True, null = True, blank = True)
    
    timeSpanOfDrive = models.DurationField(null = True, blank = True)
    driveResultTypes = (
        (1, "TOUCHDOWN"),
        (2, "FIELD GOAL MADE"),
        (3, "FIELD GOAL MISSED"),
        (4, "PUNT"),
        (21, "PUNT RETURN TD"),
        (5, "PUNT BLOCKED"),
        (6, "PUNT BLOCKED TD"),
        (7, "INTERCEPTION"),
        (8, "INTERCEPTION RETURNED FOR TOUCHDOWN"),
        (9, "FUMBLE LOST"),
        (10, "FUMBLE LOST RETURNED FOR TOUCHDOWN"),
        (11, "OFFENSE RECOVERED FUMBLE FOR TOUCHDOWN"),
        (12, "TURNOVER ON DOWNS"),
        (13, "END OF HALF"),
        (14, "END OF SECOND HALF"),
        (15, "END OF OVERTIME"),
        (16, "SAFETY"),
        (17, "OTHER"),
        (18, "BLOCKED FG TD"),
        (19, "BLOCKED FG")
        
    )
    driveResult = models.SmallIntegerField(choices = driveResultTypes, default = 4)
    startOfDriveYardLine = models.SmallIntegerField(null = True, blank = True)
    endOfDriveYardLine = models.SmallIntegerField(null = True, blank = True)
    numberOffensivePlays = models.SmallIntegerField(null = True, blank = True)
    timeElapsedInSeconds = models.SmallIntegerField(null = True, blank = True)
    reachedRedZone = models.BooleanField()

class playByPlay(models.Model):
    nflMatch = models.ForeignKey(nflMatch, on_delete = models.CASCADE)
    teamOnOffense = models.ForeignKey(nflTeam, on_delete = models.CASCADE)
    driveOfPlay = models.ForeignKey(driveOfPlay, on_delete = models.CASCADE)
    espnId = models.BigIntegerField(unique = True, blank = True, null = True)
    playTypes = (
        (1, "RUSH"),
        (2, "COMPLETED PASS"),
        (3, "INCOMPLETE PASS"),
        (4, "SACK"),
        (5, "PAT KICK MADE"),
        (6, "PAT KICK MISSED"),
        (7, "2PT CONVERSION SUCCESS RUSH"),
        (8, "2PT CONVERSION SUCCESS PASS"),
        (9, "2PT CONVERSION FAILED RUSH"),
        (10, "2PT CONVERSION FAILED PASS"),
        (11, "2PT CONVERSION SUCCESS OTHER"),
        (12, "2PT CONVERSION FAILED OTHER"),
        (13, "FG KICK"),
        (14, "FG KICK MISSED"),
        (41, "FG KICK BLOCKED"),
        (15, "INTERCEPTION"),
        (16, "INTERCEPTION RETURN TOUCHDOWN"),
        (17, "OFFENSIVE FUMBLE RECOVERY"),
        (18, "OFFENSIVE FUMBLE RECOVERY TOUCHDOWN"),
        (19, "DEFENSIVE FUMBLE RECOVERY"),
        (20, "DEFENSIVE FUMBLE RECOVERY TOUCHDOWN"),
        (21, "QB FUMBLE (UNCLEAR TYPE) - DEFENSIVE RECOVERY"),
        (22, "QB FUMBLE (UNCLEAR TYPE) - OFFENSIVE RECOVERY"),
        (23, "SAFETY"),
        (24, "PUNT"),
        (25, "PUNT BLOCKED"),
        (26, "PUNT MUFFED PUNTING TEAM RECOVERY"),
        (27, "PUNT MUFFED RECEIVING TEAM RECOVERY"),
        (28, "KICKOFF"),
        (29, "KICKOFF RECOVERY KICKING TEAM"),
        (30, "KNEEL"),
        (31, "SPIKE"),
        (32, "NO PLAY/BLOWN DEAD"),
        (33, "TIMEOUT"),
        (34, "OFFICIAL TIMEOUT"),
        (35, "END PERIOD"),
        (36, "TWO MINUTE WARNING"),
        (37, "END OF HALF"),
        (38, "END OF GAME"),
        (39, "END OF REGULATION"),
        (40, "OTHER")

    )
    playType = models.SmallIntegerField(choices = playTypes, default = 1)
    playDescription = models.CharField(max_length = 800, null = True, blank = True)
    yardsFromEndzone = models.SmallIntegerField(null = True, blank = True)
    yardsOnPlay = models.SmallIntegerField(null = True, blank = True)
    playDown = models.SmallIntegerField(validators = [MinValueValidator(0), MaxValueValidator(4)], null = True, blank = True)
    distanceTilFirstDown = models.SmallIntegerField(null = True, blank = True)
    # rusher = models.ManyToManyField(player, blank = True, related_name = 'ballCarrier')
    # passer = models.ManyToManyField(player, blank = True, related_name = 'passer')
    # reciever = models.ManyToManyField(player, blank = True, related_name = 'receiver')
    # kickReciever = models.ManyToManyField(player, blank = True, related_name = 'kickReceiver')
    turnover = models.BooleanField()
    penaltyOnPlay = models.BooleanField()
    penaltyIsOnOffense = models.BooleanField(null = True, blank = True)
    yardsGainedOrLostOnPenalty = models.SmallIntegerField(null = True, blank = True)
    scoringPlay = models.BooleanField()
    offenseScored = models.BooleanField(null = True, blank = True)
    pointsScored = models.SmallIntegerField(null = True, blank = True)
    quarter = models.CharField(max_length = 5, null=True, blank=True)
    displayClockTime = models.CharField(max_length = 5, null=True, blank=True)
    secondsRemainingInPeriod = models.SmallIntegerField(null=True, blank=True)
    sequenceNumber = models.IntegerField(null=True, blank=True)


#-------Player Models-------#

class player(models.Model):
    espnId = models.IntegerField(unique = True)
    name = models.CharField(max_length = 60, default = "-")
    firstSeason = models.SmallIntegerField(default = "2000")
    lastSeason = models.SmallIntegerField(null = True, blank = True)
    team = models.ForeignKey(nflTeam, on_delete = models.CASCADE, null = True, blank = True)
    playerHeightInches = models.SmallIntegerField(default = 60)
    playerWeightPounds = models.SmallIntegerField(default = 100)
    playerPositions = (
        (1, "QB"),
        (2, "WR"),
        (3, "TE"),
        (4, "RB"),
        (5, "FB"),
        (6, "O-Line"),
        (7, "D-Line"),
        (8, "LB"),
        (9, "CB"),
        (10, "S"),
        (11, "K"),
        (12, "P"),
        (13, "Other")
    )
    playerPosition = models.SmallIntegerField(choices = playerPositions, default = 13)
    starPlayer = models.BooleanField(default = False)
    currentlyHavingBigImpact = models.BooleanField(default = False)
    isStarter = models.BooleanField(default = False)
    positionCategories = (
        (1, "Offense"),
        (2, "Defense"),
        (3, "Special Teams"),
        (4, "Undefined")
    )
    sideOfBall = models.SmallIntegerField(choices = positionCategories, default = 4)

class playerTeamTenure(models.Model):
    player = models.ForeignKey(player, on_delete = models.CASCADE)
    team = models.ForeignKey(nflTeam, on_delete = models.CASCADE, null = True, blank = True)
    startDate = models.DateTimeField(null = True, blank = True)
    endDate = models.DateTimeField(null = True, blank = True)

class playerMatchPerformance(models.Model):
    nflMatch = models.ForeignKey(nflMatch, on_delete = models.CASCADE, null = True, blank = True)
    team = models.ForeignKey(nflTeam, on_delete = models.CASCADE)
    player = models.ForeignKey(player, on_delete=models.CASCADE, null = True, blank = True)
    playerPositions = (
        (1, "QB"),
        (2, "WR"),
        (3, "TE"),
        (4, "RB"),
        (5, "FB"),
        (6, "O-Line"),
        (7, "D-Line"),
        (8, "LB"),
        (9, "CB"),
        (10, "S")
    )
    position = models.SmallIntegerField(choices = playerPositions, default = 1)
    starter = models.BooleanField(default = False)

    class Meta:
        abstract = True

class playerMatchOffense(playerMatchPerformance, models.Model):
    rushingYards = models.SmallIntegerField()
    receivingYards = models.SmallIntegerField()
    passingYards = models.SmallIntegerField()
    rushingTDScored = models.PositiveSmallIntegerField()
    receivingTDScored = models.PositiveSmallIntegerField()
    passingTDScored = models.PositiveSmallIntegerField()

class playerMatchDefense(playerMatchPerformance, models.Model):
    tackles = models.SmallIntegerField()
    tacklesForALoss = models.SmallIntegerField()
    sacks = models.SmallIntegerField()
    forcedFumbles = models.SmallIntegerField()
    recoveredFumbles = models.SmallIntegerField()
    interceptions = models.SmallIntegerField()

class playerWeekStatus(models.Model):
    player = models.ForeignKey(player, on_delete = models.CASCADE)
    team = models.ForeignKey(nflTeam, on_delete = models.CASCADE, null = True, blank = True)
    weekOfSeason = models.SmallIntegerField(validators = [MinValueValidator(-4), MaxValueValidator(22)])
    yearOfSeason = models.SmallIntegerField(validators = [MinValueValidator(2002)])
    reportDate = models.DateField(null = True, blank = True)
    playerStatuses = (
        (1, "Available"),
        (2, "Questionable"),
        (3, "Doubtful"),
        (4, "Out"),
        (5, "Out For Season"),
        (6, "IR")
    )
    playerStatus = models.SmallIntegerField(choices = playerStatuses, default = 1)
    
    class Meta:
        indexes = [
            models.Index(fields=['yearOfSeason'], name = 'season_index'),
            models.Index(fields=['weekOfSeason'], name = 'week_index'),
            models.Index(fields=['player'], name = 'player_index'),
            models.Index(fields=['team'], name = 'team_index')
        ]

class playerPlayParticipant(models.Model):
    play = models.ForeignKey(playByPlay, on_delete = models.CASCADE)
    player = models.ForeignKey(player, on_delete = models.CASCADE)
    currentTenure = models.ForeignKey(playerTeamTenure, on_delete = models.CASCADE, blank = True, null = True)
    playerRoles = (
        (1, "passer"),
        (2, "rusher"),
        (3, "receiver"),
        (4, "returner"),
        (5, "kicker"), 
        (6, "punter"),
        (7, "sackedby"),
        (8, "tackledby"),
        (9, "tackle_assistedby"),
        (10, "interceptedby"),
        (11, "fumbledby"),
        (12, "forcedby"), 
        (13, "recoveredby"),
        (14, "penalized"),
        (20, "other")
    )
    playerRole = models.SmallIntegerField(choices = playerRoles, default = 1)
    playerPositions = (
        (1, "passer"),
        (2, "rusher"),
        (3, "receiver"),
        (4, "returner"),
        (5, "kicker"), 
        (6, "punter"),
        (7, "defender"),
    )
    playerPosition = models.SmallIntegerField(choices = playerPositions, default = 1)
    
    class Meta:
        abstract = True

class passerStatSplit(playerPlayParticipant):
    passingYards = models.SmallIntegerField(blank = True, null = True)
    interception = models.BooleanField(default = False)
    fumble = models.BooleanField(default = False)
    fumbleLost = models.BooleanField(default = False)
    passingTdScored = models.BooleanField(default = False)

class rusherStatSplit(playerPlayParticipant):
    rushingYards = models.SmallIntegerField(blank = True, null = True)
    fumble = models.BooleanField(default = False)
    fumbleLost = models.BooleanField(default = False)
    rushingTdScored = models.BooleanField(default = False)

class receiverStatSplit(playerPlayParticipant):
    receivingYards = models.SmallIntegerField(blank = True, null = True)
    yardsAfterCatch = models.SmallIntegerField(blank = True, null = True) 
    fumble = models.BooleanField(default = False)
    fumbleLost = models.BooleanField(default = False)
    receivingTdScored = models.BooleanField(default = False)

class returnerStatSplit(playerPlayParticipant):
    returnYards = models.SmallIntegerField(blank = True, null = True)
    fumble = models.BooleanField(default = False)
    fumbleLost = models.BooleanField(default = False)
    returnTypes = (
        (1, "kickoff"),
        (2, "punt"),
        (3, "fieldGoal"),
        (4, "interception"),
        (5, "fumbleRecovery"),
    )
    returnType = models.SmallIntegerField(choices = returnTypes, default = 1)

class kickerFgStatSplit(playerPlayParticipant):
    isPointAfterAttempt = models.BooleanField(default = False)
    attemptDistance = models.SmallIntegerField(blank = True, null = True)
    kickMade = models.BooleanField(default = False)

class punterStatSplit(playerPlayParticipant):
    puntYards = models.SmallIntegerField(blank = True, null = True)
    isTouchBack = models.BooleanField(default = False)

class defenderStatSplit(playerPlayParticipant):
    tackle = models.SmallIntegerField(blank = True, null = True)
    soloTackle = models.BooleanField(default = False)
    sack = models.BooleanField(default = False)
    tackleForLoss = models.BooleanField(default = False)
    intercepted = models.BooleanField(default = False)
    fumbleForced = models.BooleanField(default = False)
    fumbleRecovered = models.BooleanField(default = False)
    passDefended = models.BooleanField(default = False)
    hitOpposingQB = models.BooleanField(default = False)

class penalizedStatSplit(playerPlayParticipant):
    penaltyYards = models.SmallIntegerField(blank = True, null = True)
    
#-------Odds Models-------#

class nflMatchOdds(models.Model):
    nflMatch                            = models.ForeignKey(nflMatch, on_delete = models.CASCADE)
    matchLineHomeTeam_Open              = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
    overUnderLine_Open                  = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
    homeTeamMoneyLine_Open              = models.SmallIntegerField(null = True, blank = True)
    awayTeamMoneyLine_Open              = models.SmallIntegerField(null = True, blank = True)
    openOddsDate                        = models.DateTimeField(null = True, blank = True)
    matchLineHomeTeam                   = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
    overUnderLine                       = models.DecimalField(max_digits = 5, decimal_places = 1, null = True, blank = True)
    homeTeamMoneyLine                   = models.SmallIntegerField(null = True, blank = True)
    awayTeamMoneyLine                   = models.SmallIntegerField(null = True, blank = True)







