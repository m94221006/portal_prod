# Generated by Django 2.1.2 on 2019-10-03 10:53

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0006_region_chinese_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='template',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.CharField(max_length=300)),
                ('config', django.contrib.postgres.fields.jsonb.JSONField(default={}, verbose_name='配置')),
                ('deleted', models.BooleanField(default=False)),
                ('creator', models.CharField(default='system', max_length=50)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('lastupdatedby', models.CharField(default='system', max_length=50)),
                ('lastupdatedtime', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
