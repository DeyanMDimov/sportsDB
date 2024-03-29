# Generated by Django 4.1.4 on 2022-12-22 17:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nfl_db', '0022_teammatchperformance_weekofseason_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='nflmatch',
            name='indoorStadium',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='precipitation',
            field=models.SmallIntegerField(blank=True, choices=[(0, 'None'), (1, 'Rain'), (2, 'Snow')], null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='precipitationForecast',
            field=models.SmallIntegerField(blank=True, choices=[(0, 'None'), (1, 'Rain'), (2, 'Snow')], null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='precipitationStrength',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='precipitationStrengthForecast',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='temperature',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='temperatureForecast',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='windStrength',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='nflmatch',
            name='windStrengthForecast',
            field=models.SmallIntegerField(blank=True, null=True),
        ),
    ]
