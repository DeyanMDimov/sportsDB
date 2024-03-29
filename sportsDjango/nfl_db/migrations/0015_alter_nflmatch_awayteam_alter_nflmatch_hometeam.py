# Generated by Django 4.1.4 on 2022-12-20 18:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nfl_db', '0014_alter_nflmatch_awayteam_alter_nflmatch_hometeam'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nflmatch',
            name='awayTeam',
            field=models.ManyToManyField(blank=True, related_name='awayTeam', to='nfl_db.nflteam'),
        ),
        migrations.AlterField(
            model_name='nflmatch',
            name='homeTeam',
            field=models.ManyToManyField(blank=True, related_name='homeTeam', to='nfl_db.nflteam'),
        ),
    ]
