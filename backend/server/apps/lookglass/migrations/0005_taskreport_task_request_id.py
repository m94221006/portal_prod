# Generated by Django 2.1.2 on 2020-04-16 08:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lookglass', '0004_auto_20200415_1039'),
    ]

    operations = [
        migrations.AddField(
            model_name='taskreport',
            name='task_request_id',
            field=models.CharField(default='', max_length=200),
        ),
    ]
