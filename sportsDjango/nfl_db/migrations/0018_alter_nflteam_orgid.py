# Generated by Django 4.1.4 on 2022-12-20 21:30

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nfl_db', '0017_nflmatch_awayteam_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nflteam',
            name='orgId',
            field=models.SmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(34)]),
        ),
    ]
