# Generated by Django 3.2.5 on 2023-10-03 07:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('resume', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='candidateexperience',
            name='present',
            field=models.TextField(blank=True, default='', null=True),
        ),
    ]
