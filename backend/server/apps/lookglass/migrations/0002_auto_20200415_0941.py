# Generated by Django 2.1.2 on 2020-04-15 09:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lookglass', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='command_postdata',
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name='task',
            name='nodes',
            field=models.CharField(max_length=300),
        ),
    ]
