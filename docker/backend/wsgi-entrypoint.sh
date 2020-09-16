#!/usr/bin/env bash

ls -al /app/backend/server/django_static/js


until cd /app/backend/server
do
    echo "Waiting for server volume..."
done

until ./manage.py migrate
do
    echo "Waiting for postgres ready..."
    sleep 2
done

./manage.py collectstatic --noinput

./manage.py makemigrations

pip3 install django-cors-headers

pip3 uninstall django

pip3 install django==2.1.2



gunicorn server.wsgi --bind 0.0.0.0:8089 --workers 4 --threads 4 
#./manage.py runserver 0.0.0.0:8000 # --settings=settings.dev_docker
