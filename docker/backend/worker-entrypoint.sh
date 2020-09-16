#!/usr/bin/env bash

#pip3 install django-celery-beat
#pip3 install django-json-widget
#until cd /app/heartbeat
#do 
#    echo "waiting for heartbeat volume..."
#done

#./heartbeat -e -c heartbeat.yml
#export PYTHONIOENCODING=utf-8


#./heartbeat -e -v -c heartbeat.yml &
until cd /app/backend/worker
do
    echo "Waiting for worker volume..."
done
celery -A simple_worker worker --loglevel=info -E --hostname=x@%h
