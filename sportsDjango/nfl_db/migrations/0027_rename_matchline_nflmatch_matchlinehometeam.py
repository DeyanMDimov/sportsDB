# Generated by Django 4.1.4 on 2022-12-27 04:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nfl_db', '0026_teammatchperformance_totalpointsallowedbydefense'),
    ]

    operations = [
        migrations.RenameField(
            model_name='nflmatch',
            old_name='matchLine',
            new_name='matchLineHomeTeam',
        ),
    ]