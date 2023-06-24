# Generated by Django 3.2.5 on 2023-06-24 05:09

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Emaillead',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('userdate', models.TextField(blank=True)),
                ('usertime', models.TextField(blank=True)),
                ('usermob', models.TextField(blank=True)),
                ('userdetails', models.TextField(blank=True)),
                ('emailuserdate', models.TextField(blank=True)),
                ('emailusertime', models.TextField(blank=True)),
                ('emailusermob', models.TextField(blank=True)),
                ('emailuserdetails', models.TextField(blank=True)),
                ('emailcheckstatus', models.PositiveSmallIntegerField(default=1)),
                ('emaildropdownlist', models.TextField(default='New')),
            ],
        ),
        migrations.CreateModel(
            name='Emailleadoppurtunities',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('refuserdate', models.TextField(blank=True)),
                ('refusertime', models.TextField(blank=True)),
                ('refusermob', models.TextField(blank=True)),
                ('refuserdetails', models.TextField(blank=True)),
                ('refemailuserdate', models.TextField(blank=True)),
                ('refemailusertime', models.TextField(blank=True)),
                ('refemailusermob', models.TextField(blank=True)),
                ('refemailuserdetails', models.TextField(blank=True)),
                ('refcheckstatus', models.PositiveSmallIntegerField(default=1)),
                ('refdropdownlist', models.TextField(default='New')),
            ],
        ),
        migrations.CreateModel(
            name='Film',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.TextField(blank=True)),
                ('title', models.TextField(blank=True)),
                ('year', models.TextField(blank=True)),
                ('filmurl', models.TextField(blank=True)),
                ('checkstatus', models.PositiveSmallIntegerField(default=1)),
                ('dropdownlist', models.TextField(default='New')),
            ],
        ),
        migrations.CreateModel(
            name='whatsapp',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chat', models.FileField(upload_to='media')),
            ],
        ),
    ]
