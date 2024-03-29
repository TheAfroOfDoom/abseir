# Generated by Django 4.0.4 on 2022-07-18 23:57

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simulations', '0009_alter_parameters_sample_size'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parameters',
            name='r0',
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name='parameters',
            name='sample_size',
            field=models.PositiveIntegerField(null=True, validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.AlterField(
            model_name='parameters',
            name='time_horizon',
            field=models.PositiveIntegerField(null=True),
        ),
    ]
