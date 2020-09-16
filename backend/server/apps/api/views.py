from rest_framework import status
from django.shortcuts import render
from django.core import serializers

from worker.simple_worker import WORKERS
from worker.simple_worker import task_add
from worker.OpenApiDemo import OpenApiDemo
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from celery import Celery

import os
import re
import json
import logging
import urllib

from time import gmtime, strftime


WORKERS = Celery('simple_worker')
WORKERS.config_from_object('celeryconfig')


# Create your views here.
class Log(object):
    def __init__(self,log_file_name,log_name):
        self.logfilename = "%s%s.log"%(log_file_name,strftime("%Y%m%d%H%M", gmtime()))
        self.logname = log_name
        self.logger = self.__set_log()


    def __set_log(self):
        logpath = os.path.join(os.getcwd(), 'log')
        if not os.path.exists(logpath):
            os.makedirs(logpath)
        filepath = os.path.join(logpath, self.logfilename)
        logger = logging.getLogger(self.logname)
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh = logging.FileHandler(filepath)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        console.setFormatter(formatter)
        logger.addHandler(console)
        return logger


log = Log("api","run_testing")
@csrf_exempt
def runtool(request):
    try:
       if request.method == 'GET':
          commandlist = list()
          device_param = list()
          test_param = []
          test_kparam = {}

          MONITOR_ACTION = request.GET['monitor_action']
          MONITOR_ID = request.GET['monitor_id']
          MONITOR_HOST = request.GET['monitor_host']

          test_param.append(MONITOR_ACTION)
          test_param.append(MONITOR_ID)
          test_param.append(MONITOR_HOST)
          
          #test_param = ['192.168.250.71', 'ps aux | grep haproxy']
          #response_data = serializers.serialize("json",test_param)
          #param = ['192.168.250.71', 'ps aux | grep haproxy']
          WORKERS.send_task('worker.worker.task_add',test_param)
          return HttpResponse("pass")
    except Exception as e:
        message =  "Exception : "+ str(e)
        return HttpResponse(message,status=status.HTTP_400_BAD_REQUEST)

