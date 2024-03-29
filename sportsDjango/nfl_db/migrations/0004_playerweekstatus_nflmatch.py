# Generated by Django 4.1.4 on 2022-12-20 18:19

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nfl_db', '0003_delete_nflmatch_delete_playbyplay_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='playerWeekStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('weekOfSeason', models.SmallIntegerField(validators=[django.core.validators.MinValueValidator(-4), django.core.validators.MaxValueValidator(22)])),
                ('yearOfSeason', models.SmallIntegerField(validators=[django.core.validators.MinValueValidator(2002)])),
                ('reportDate', models.DateField()),
                ('playerStatus', models.SmallIntegerField(choices=[(1, 'Available'), (2, 'Questionable'), (3, 'Doubtful'), (4, 'Out'), (5, 'Out For Season'), (6, 'IR')], default=1)),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='nfl_db.player')),
                ('team', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='nfl_db.nflteam')),
            ],
        ),
        migrations.CreateModel(
            name='nflMatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datePlayed', models.DateTimeField(blank=True, null=True)),
                ('completed', models.BooleanField(default=False)),
                ('weekOfSeason', models.SmallIntegerField(default=0, validators=[django.core.validators.MinValueValidator(-4), django.core.validators.MaxValueValidator(22)])),
                ('yearOfSeason', models.SmallIntegerField(default=2002, validators=[django.core.validators.MinValueValidator(2002)])),
                ('neutralStadium', models.BooleanField(default=False)),
                ('overtime', models.BooleanField(default=False)),
                ('playoffs', models.BooleanField(default=False)),
                ('preseason', models.BooleanField(default=False)),
                ('homeTeamPoints', models.SmallIntegerField(blank=True, null=True)),
                ('homeTeamTotalYards', models.SmallIntegerField(blank=True, null=True)),
                ('homeTeamRushingYards', models.SmallIntegerField(blank=True, null=True)),
                ('homeTeamReceivingYards', models.SmallIntegerField(blank=True, null=True)),
                ('homeTeamGiveaways', models.SmallIntegerField(blank=True, null=True)),
                ('homeTeamExplosivePlays', models.SmallIntegerField(blank=True, null=True)),
                ('homeTeamPointsAllowed', models.SmallIntegerField(blank=True, null=True)),
                ('homeTeamYardsAllowed', models.SmallIntegerField(blank=True, null=True)),
                ('homeTeamRushYardsAllowed', models.SmallIntegerField(blank=True, null=True)),
                ('homeTeamReceivingYardsAllowed', models.SmallIntegerField(blank=True, null=True)),
                ('homeTeamTakeaways', models.SmallIntegerField(blank=True, null=True)),
                ('homeTeamRushingTDScored', models.SmallIntegerField(blank=True, null=True)),
                ('homeTeamReceivingTDScored', models.SmallIntegerField(blank=True, null=True)),
                ('homeTeamRushingTDAllowed', models.SmallIntegerField(blank=True, null=True)),
                ('homeTeamReceivingTDAllowed', models.SmallIntegerField(blank=True, null=True)),
                ('homeTeamFGScored', models.SmallIntegerField(blank=True, null=True)),
                ('homeTeamFGAllowed', models.SmallIntegerField(blank=True, null=True)),
                ('homeTeamSpecialTeamsPointsScored', models.SmallIntegerField(blank=True, null=True)),
                ('homeTeamDefensePointsScored', models.SmallIntegerField(blank=True, null=True)),
                ('awayTeamScore', models.SmallIntegerField(blank=True, null=True)),
                ('awayTeamTotalYards', models.SmallIntegerField(blank=True, null=True)),
                ('awayTeamRushingYarsds', models.SmallIntegerField(blank=True, null=True)),
                ('awayTeamReceivingYards', models.SmallIntegerField(blank=True, null=True)),
                ('awayTeamGiveaways', models.SmallIntegerField(blank=True, null=True)),
                ('awayTeamExplosivePlays', models.SmallIntegerField(blank=True, null=True)),
                ('awayTeamYardsAllowed', models.SmallIntegerField(blank=True, null=True)),
                ('awayTeamRushYardsAllowed', models.SmallIntegerField(blank=True, null=True)),
                ('awayTeamReceivingYardsAllowed', models.SmallIntegerField(blank=True, null=True)),
                ('awayTeamTakeaways', models.SmallIntegerField(blank=True, null=True)),
                ('awayTeamRushingTDScored', models.SmallIntegerField(blank=True, null=True)),
                ('awayTeamReceivingTDScored', models.SmallIntegerField(blank=True, null=True)),
                ('awayTeamRushingTDAllowed', models.SmallIntegerField(blank=True, null=True)),
                ('awayTeamReceivingTDAllowed', models.SmallIntegerField(blank=True, null=True)),
                ('awayTeamFGScored', models.SmallIntegerField(blank=True, null=True)),
                ('awayTeamFGAllowed', models.SmallIntegerField(blank=True, null=True)),
                ('awayTeamSpecialTeamsPointsScored', models.SmallIntegerField(blank=True, null=True)),
                ('awayTeamDefensePointsScored', models.SmallIntegerField(blank=True, null=True)),
                ('matchLine', models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True)),
                ('overUnderLine', models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True)),
                ('awayTeam', models.ManyToManyField(related_name='awayTeam', to='nfl_db.nflteam')),
                ('homeTeam', models.ManyToManyField(related_name='homeTeam', to='nfl_db.nflteam')),
            ],
        ),
    ]
