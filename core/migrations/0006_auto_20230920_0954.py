# Generated by Django 3.2.5 on 2023-09-20 09:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20230915_1253'),
    ]

    operations = [
        migrations.AddField(
            model_name='custombenchsales',
            name='bsEmail_attachment',
            field=models.TextField(blank=True),
        ),
        migrations.AlterField(
            model_name='emailbenchsales',
            name='created_date',
            field=models.TextField(blank=True, default='2023-09-20'),
        ),
    ]
