# Generated by Django 2.1.2 on 2020-04-15 07:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cid', models.IntegerField(default=0)),
                ('uid', models.IntegerField(default=0)),
                ('periodictask_id', models.IntegerField(default=1)),
                ('name', models.CharField(max_length=50)),
                ('starttime', models.DateField()),
                ('period', models.CharField(max_length=50)),
                ('every', models.IntegerField(default=1)),
                ('times', models.IntegerField(default=3)),
                ('command', models.CharField(max_length=50)),
                ('command_postdata', models.TextField()),
                ('nodes', models.TextField()),
                ('enabled', models.BooleanField(default=True)),
                ('created_by', models.CharField(default='system', max_length=50)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('updated_by', models.CharField(default='system', max_length=50)),
                ('updated_time', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'task',
            },
        ),
        migrations.CreateModel(
            name='TaskReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('history_id', models.CharField(max_length=100)),
                ('enabled', models.BooleanField(default=True)),
                ('created_by', models.CharField(default='system', max_length=50)),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lookglass.Task')),
            ],
            options={
                'db_table': 'taskreport',
            },
        ),
        migrations.CreateModel(
            name='TaskStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('enabled', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'task_status',
            },
        ),
        migrations.AddField(
            model_name='task',
            name='status',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lookglass.TaskStatus'),
        ),
    ]
