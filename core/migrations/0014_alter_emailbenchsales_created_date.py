# Generated by Django 3.2.5 on 2023-10-09 13:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_auto_20231006_1137'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailbenchsales',
            name='created_date',
            field=models.TextField(blank=True, default='2023-10-09'),
        ),
    ]
