#!/usr/bin/env bash

pip3 install django-celery-beat

pip3 uninstall django

pip3 install django==2.1.2

until cd /app/backend/worker
do
    echo "Waiting for beat volume..."
done

celery -A simple_worker beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
