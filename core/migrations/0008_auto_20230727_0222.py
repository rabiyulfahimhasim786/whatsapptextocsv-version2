# Generated by Django 3.2.5 on 2023-07-27 09:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_alter_emailbenchsales_created_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='custombenchsales',
            name='bsEmail_Bodyhtml',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='emailbenchsales',
            name='created_date',
            field=models.TextField(blank=True, default='2023-07-27'),
        ),
    ]
