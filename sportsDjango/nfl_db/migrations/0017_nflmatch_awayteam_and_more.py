# Generated by Django 4.1.4 on 2022-12-20 18:36

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nfl_db', '0016_remove_nflmatch_awayteam_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='nflmatch',
            name='awayTeam',
            field=models.ManyToManyField(blank=True, related_name='awayTeam', to='nfl_db.nflteam'),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='awayTeamDefensePointsScored',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='awayTeamExplosivePlays',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='awayTeamFGAllowed',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='awayTeamFGScored',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='awayTeamGiveaways',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='awayTeamReceivingTDAllowed',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='awayTeamReceivingTDScored',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='awayTeamReceivingYards',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='awayTeamReceivingYardsAllowed',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='awayTeamRushYardsAllowed',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='awayTeamRushingTDAllowed',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='awayTeamRushingTDScored',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='awayTeamRushingYarsds',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='awayTeamScore',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='awayTeamSpecialTeamsPointsScored',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='awayTeamTakeaways',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='awayTeamTotalYards',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='awayTeamYardsAllowed',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='completed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='homeTeam',
            field=models.ManyToManyField(blank=True, related_name='homeTeam', to='nfl_db.nflteam'),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='homeTeamDefensePointsScored',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='homeTeamExplosivePlays',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='homeTeamFGAllowed',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='homeTeamFGScored',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='homeTeamGiveaways',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='homeTeamPoints',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='homeTeamPointsAllowed',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='homeTeamReceivingTDAllowed',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='homeTeamReceivingTDScored',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='homeTeamReceivingYards',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='homeTeamReceivingYardsAllowed',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='homeTeamRushYardsAllowed',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='homeTeamRushingTDAllowed',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='homeTeamRushingTDScored',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='homeTeamRushingYards',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='homeTeamSpecialTeamsPointsScored',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='homeTeamTakeaways',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='homeTeamTotalYards',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='homeTeamYardsAllowed',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='matchLine',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='neutralStadium',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='overUnderLine',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='overtime',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='playoffs',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='preseason',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='weekOfSeason',
            field=models.SmallIntegerField(default=0, validators=[django.core.validators.MinValueValidator(-4), django.core.validators.MaxValueValidator(22)]),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='yearOfSeason',
            field=models.SmallIntegerField(default=2002, validators=[django.core.validators.MinValueValidator(2002)]),
        ),
    ]