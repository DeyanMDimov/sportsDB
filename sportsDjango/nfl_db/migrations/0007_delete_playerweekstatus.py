# Generated by Django 4.1.4 on 2022-12-20 18:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('nfl_db', '0006_nflmatch_delete_nflmatches'),
    ]

    operations = [
        migrations.DeleteModel(
            name='playerWeekStatus',
        ),
    ]
