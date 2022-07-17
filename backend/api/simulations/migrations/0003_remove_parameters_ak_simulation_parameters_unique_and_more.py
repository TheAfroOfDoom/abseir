# Generated by Django 4.0.4 on 2022-07-17 06:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simulations', '0002_auto_20220715_0620'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='parameters',
            name='AK_simulation_parameters_unique',
        ),
        migrations.AlterField(
            model_name='data',
            name='cycle_index',
            field=models.PositiveIntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name='parameters',
            name='r0',
            field=models.IntegerField(editable=False),
        ),
        migrations.AlterField(
            model_name='parameters',
            name='time_horizon',
            field=models.PositiveIntegerField(editable=False),
        ),
        migrations.AlterUniqueTogether(
            name='parameters',
            unique_together={('time_horizon', 'r0')},
        ),
    ]
