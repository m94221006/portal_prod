from rest_framework import status
from django.shortcuts import render
from django.core import serializers

from worker.simple_worker import WORKERS
from worker.simple_worker import task_add
from worker.OpenApiDemo import OpenApiDemo
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from celery import Celery
from worker.mlog import Log

import os
import re
import json
import logging
import urllib
from time import gmtime, strftime

WORKERS = Celery('simple_worker')
WORKERS.config_from_object('celeryconfig')


log = Log("api","run_testing")
def lg_get_nodes(request):
    try:
       if request.method == 'GET':
           username = request.GET['username']
           token =  request.GET['token']
           api =  lg_operation_api(operapihost)
           userpofile =  api.get_userprofile(token,username)

           result = list()
           monitorlist = api.get_instances(token,customer.instance)
           for monitor in monitorlist:
               result.append({'nid':monitor.id,'host_name': monitor.host_name,'region':monitor.region_name,'isp':monitor.isp_name,'host_ch_name':monitor.ch_name})
           return HttpResponse(json.dumps(result), content_type="application/json")
       else:
            message = 'Please use get to access'
            return HttpResponse(message,status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        message =  "Exception : "+ str(e)
        return HttpResponse(message,status=status.HTTP_400_BAD_REQUEST)

def lg_run_command(request):
    try:
       if request.method == 'POST':
            log = Log("api","api")
            username = request.GET['username']
            token =  request.POST['token']
            if token and username :
                nid = int(request.POST['nid'])
                lg_command = request.POST['command']
                lg_host = request.POST['host']
                lg_origin = request.POST['lg_origin']
                curl_domain = request.POST['curl_domain']
                curl_port= request.POST['curl_port']
                curl_ip= request.POST['curl_ip']
                tcp_port = request.POST['tcp_port']
                nslookup_type = request.POST['nslookup_type']
                nslookup_dns = request.POST['nslookup_dns']

                api =  lg_operation_api(operapihost)
                userpofile =  api.get_userprofile(token,username)
                node =  api.get_instance(token,lg_id)

                lgnodeapi = lg_nodes_api(node.region_name,node.ch_name,node.host_ip)
                response_data = lgnodeapi.get_nodes_api(lg_command,lg_host,lg_origin,curl_domain,curl_port,curl_ip,tcp_port,nslookup_type,nslookup_dns)
            
            return HttpResponse(response_data, content_type="application/json")

       else:
            message = 'Please use get to access'
            return HttpResponse(message,status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        message =  "Exception : "+ str(e)
        return HttpResponse(message,status=status.HTTP_400_BAD_REQUEST)

'''
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

'''