# -*- coding: UTF-8 -*-


from django.shortcuts import render,redirect,render_to_response
from django.http import HttpResponse
import requests
import sys
import os, base64
import json
import time
from worker.sshtool import sshtool
import uuid
from worker.simple_worker import WORKERS
import logging
from worker.config import WS_IP, WS_PORT,CUSTOMER
from worker.config import node_api_token
from django.contrib.auth.decorators import login_required
from worker.mlog import Log
from http_parser.parser import HttpParser
from http_parser.util import b
from datetime import datetime, timedelta
import time
from django.contrib.auth.models import User
from django.db.models import Q
from worker.lgparse import lg_parse
from worker.lgnodesapi import lg_nodes_api , lg_instance_api
from worker.lghistoryapi import lg_history_api
from lookglass.models import TaskStatus,Task
from worker.config import operapihost
from worker.lgoperationapi import lg_operation_api
from django_celery_beat.models import PeriodicTasks, PeriodicTask, IntervalSchedule
from django.core import serializers

log = Log("lookglass","lookglasslog")

# Create your views here.
def index(request):
    try:
        username = request.GET['username']
        token =  request.GET['token']
        api =  lg_operation_api(operapihost)
        userpofile =  api.get_userprofile(token,username)
        customer =  api.get_customerinfo(token,userpofile.customer_id)
        allregionlist = api.get_regions(token)
        monitorlist = api.get_instances(token,customer.instance)
        tmpregionlist= list(set([instance.region_name for instance in monitorlist]))
        regionlist = list(region for region in allregionlist if region.ch_name in tmpregionlist)

        context_dict ={'regionlist': regionlist,'monitorlist': monitorlist}
        response = render_to_response('lookglass/index.html',context_dict)

        return response
    except Exception as e:
        message =  "Exception : "+ str(e)
        return HttpResponse( message)

def index_v2(request):
    try:
        username = request.GET['username']
        token =  request.GET['token']
        api =  lg_operation_api(operapihost)
        userpofile =  api.get_userprofile(token,username)
        customer =  api.get_customerinfo(token,userpofile.customer_id)
        allregionlist = api.get_regions(token)
        monitorlist = api.get_instances(token,customer.instance)
        tmpregionlist= list(set([instance.region_name for instance in monitorlist]))
        regionlist = list(region for region in allregionlist if region.ch_name in tmpregionlist)
        uid = uuid.uuid1()
        context_dict ={'username':username,'ws_ip': WS_IP, 'ws_port':WS_PORT,'uid':uid,'regionlist': regionlist, 'monitorlist': monitorlist}
        response = render_to_response('lookglass/index_v2.html',context_dict)
        return response
    except Exception as e:
        message =  "Exception : "+ str(e)
        return HttpResponse( message)

def looking_glass(request):
    try:
        username = request.GET['username']
        token =  request.GET['token']
        if token:
            lg_id = int(request.GET['lg_id'])
            lg_command = request.GET['lg_command']
            lg_host = request.GET['lg_host']
            lg_origin = request.GET['lg_origin']
            curl_domain = request.GET['curl_domain']
            curl_port= request.GET['curl_port']
            curl_ip= request.GET['curl_ip']
            tcp_port = request.GET['tcp_port']
            nslookup_type = request.GET['nslookup_type']
            nslookup_dns = request.GET['nslookup_dns']

            api =  lg_operation_api(operapihost)
            userpofile =  api.get_userprofile(token,username)
            node =  api.get_instance(token,lg_id)

            ## get user related information
            user_id = userpofile.user_id
            customer_name = userpofile.customer_name

            # send command to lg 
            lgnodeapi = lg_nodes_api(node.region_name,node.ch_name,node.host_ip)
            response_data = lgnodeapi.get_nodes_api(lg_command,lg_host,lg_origin,curl_domain,curl_port,curl_ip,tcp_port,nslookup_type,nslookup_dns)
            
            #create lg history
            if response_data:
                create_history(userpofile.customer_name,userpofile.user_id,node.ch_name,lg_host,tcp_port,lg_command,response_data)
            return HttpResponse(response_data)
        else:
            return HttpResponse('please use the get for this url:'+request.method)

    except Exception as e:
        message =  "Exception : "+ str(e)
        return HttpResponse( message)
        
def looking_glass_v2(request):
    try:
        response_data = {}

        if request.method=="GET":
          username = request.GET['username']
          token =  request.GET['token']
          if token:
            group_name ='lg_%s'%request.GET['uid']
            #lg_name = request.GET['lg_name']
            lg_id = request.GET['lg_id']
            lg_command = request.GET['lg_command']
            lg_host = request.GET['lg_host']
            lg_origin = request.GET['lg_origin']
            curl_domain = request.GET['curl_domain']
            curl_port= request.GET['curl_port']
            curl_ip= request.GET['curl_ip']
            tcp_port = request.GET['tcp_port']
            nslookup_type = request.GET['nslookup_type']
            nslookup_dns = request.GET['nslookup_dns']
            msg_type =  request.GET['msg_type']
            msg_times=  request.GET['msg_times']
            idlist = lg_id.split(";")


            api =  lg_operation_api(operapihost)
            userpofile =  api.get_userprofile(token,username)
            user_id = userpofile.user_id
            customer_name = userpofile.customer_name

            command_site = "%s;%s;%s;%s;%s;%s;%s;%s;%s"%(lg_command,lg_host,lg_origin,curl_domain,curl_port,curl_ip,tcp_port,nslookup_type,nslookup_dns)
            index = 1
            for key,value in enumerate(idlist):
                monitor_id = value.split("-")[0]
                monitor =  api.get_instance(token,monitor_id)
                monitor_ip = monitor.host_ip
                monitor_name = monitor.ch_name
                region_name = monitor.region_name
                test_param = ["tools",user_id,customer_name,monitor_id,group_name,region_name,monitor_name,monitor_ip,command_site,msg_type,msg_times]
                WORKERS.send_task('worker.worker.task_add',test_param)
            response_data['message'] = 'Success'
            response_data['status_code'] = 200
        return HttpResponse( json.dumps(response_data), content_type="application/json")
    except Exception as e:
        message =  "Exception : "+ str(e)
        response_data['message'] = message
        response_data['status_code'] = 408
        return HttpResponse( json.dumps(response_data), content_type="application/json")

from django.http import StreamingHttpResponse

def looking_glass_down(request):
    try:
        if request.user.is_authenticated:
            if request.method=="GET":
                lg_id = int(request.GET['lg_id'])
                url = request.GET['url']
                timestamp = request.GET['timestamp']
                filename = url.split("=")[1]+"-"+timestamp+".har"
                node = instance.objects.get(pk = lg_id)
                downlink = 'http://'+node.host_ip+ ":5000" + url+"&timestamp="+timestamp
                r = requests.get(downlink, stream=True)
                response = StreamingHttpResponse(streaming_content=r)
                response['Content-Type'] = 'application/octet-stream'
                response['Content-Disposition'] = 'attachment;filename="'+filename+'"'
                return response
        else:
            message ='No authentication to access.'
            return HttpResponse(message)
    except Exception as e:
        message =  "Exception : "+ str(e)
        return HttpResponse(message)

def lg_history(request):
    try:
        username = request.GET['username']
        token =  request.GET['token']
        if token:
            user_id = username
            api =  lg_operation_api(operapihost)
            userpofile =  api.get_userprofile(token,username)
            customer =  api.get_customerinfo(token,userpofile.customer_id)
            allregionlist = api.get_regions(token)
            monitorlist = api.get_instances(token,customer.instance)
            tmpregionlist= list(set([instance.region_name for instance in monitorlist]))
            regionlist = list(region for region in allregionlist if region.ch_name in tmpregionlist)
            context_dict ={'user_id': user_id,'regionlist':regionlist,'monitorlist':monitorlist}
            response = render_to_response('lookglass/history/index.html',context_dict)
            return response
        else:
            return("No auth to access")
    except Exception as e:
        message =  "Exception : "+ str(e)
        return HttpResponse( message)

def lg_history_detail(request):
    try:
        username = request.GET['username']
        token =  request.GET['token']
        if token:
            api =  lg_operation_api(operapihost)
            userpofile =  api.get_userprofile(token,username)
            monitorlist = api.get_instances(token,None)
            res_data = []
            count = 100
            command = request.GET['command']
            nodes_id = request.GET['nodes']
            user_id = userpofile.user_id
            customer_name = userpofile.customer_name
            if nodes_id:
                nodes_id_list =list([int(node_id) for node_id in nodes_id.split(",")])
                monitor_value =','.join(list(item.ch_name for item in monitorlist if item.id in nodes_id_list))
            else:
                monitor_value = ''
            history =lg_history_api(customer_name,user_id,count)
            response_data = history.search_lg_history(command,monitor_value)
            data_list =response_data.json()["result"]
            for item in data_list:
                red_item = item
                del red_item["header"]
                del red_item["body"]
                del red_item["result"]
                tranfer_time = datetime.strptime(red_item["published_date"],'%a, %d %b %Y %H:%M:%S %Z')+ timedelta(hours=8)
                red_item["published_date"] = tranfer_time.strftime("%Y/%m/%d %H:%M:%S")
                red_item["status_code"] =  red_item["status_code"].replace("<br/>","\n")
                red_item["total_time"] =  red_item["total_time"].replace("<br/>","\n")

                res_data.append(red_item)
            context_dict ={'detaillist':res_data, 'supportfilter':'False'}
            response = render_to_response('lookglass/history/history_detail.html',context_dict)
            return response
        else:
            return("No auth to access")
    except Exception as e:
        message =  "Exception : "+ str(e)
        return HttpResponse( message)

def lg_history_content(request):
    try:
        username = request.GET['username']
        token =  request.GET['token']
        if token:
            api =  lg_operation_api(operapihost)
            userpofile =  api.get_userprofile(token,username)           
            id = request.GET['id']
            count = 100
            history =lg_history_api(userpofile.customer_name,userpofile.user_id,count)
            response_data = history.get_lg_history(id)
            return HttpResponse(json.dumps(response_data.json()["result"][0]), content_type="application/json")
    except Exception as e:
        message =  "Exception : "+ str(e)
        return HttpResponse(message)

def lg_task(request):
    try:
        username = request.GET['username']
        token =  request.GET['token']
        if token:
            user_id = username
            api =  lg_operation_api(operapihost)
            userpofile =  api.get_userprofile(token,username)
            customer =  api.get_customerinfo(token,userpofile.customer_id)
            user_id = userpofile.user_id

            tasklist = Task.objects.filter(uid = user_id ,enabled = True)
            taskcount = len(tasklist.filter(enabled = True).exclude(status__name ='Completed'))
            context_dict ={'user_id': user_id,'task_list':tasklist, 'task_count':taskcount}
            response = render_to_response('lookglass/task/index.html',context_dict)
            return response
        else:
            return("No auth to access")
    except Exception as e:
        message =  "Exception : "+ str(e)
        return HttpResponse( message)

def lg_task_instances(request):
    response_data={}
    try:
        username = request.GET['username']
        token =  request.GET['token']
        task_id = int(request.GET['id'])
        task = Task.objects.get(id = task_id)
        api =  lg_operation_api(operapihost)
        nodelist = api.get_All_instances(token,None)
       
        if task:
            message = ""
            instance_list =  task.nodes.split(';')
            for instance_id in instance_list:
                node = [item for item in nodelist if item.id == int(instance_id)]
                if node:
                #node =  api.get_All_instances(token,instance_id)
                   message = message + node[0].ch_name+","

            response_data['command'] = task.command
            response_data['command_host'] = task.command_host
            response_data['message'] = message
            response_data['status_code'] = 200
        else:
            response_data['command'] = ""
            response_data['command_host'] = ""
            response_data['message'] ='not found'
            response_data['status_code'] = 403
        return HttpResponse(json.dumps(response_data), content_type="application/json")
    except Exception as e:
        message =  "Exception : "+ str(e)
        response_data['status_code'] = 408
        response_data['message'] = message
        response_data['command'] = ""
        response_data['command_host'] = ""
        return HttpResponse(json.dumps(response_data), content_type="application/json")

def task_config(request):
    try:
        response_data={}
        api =  lg_operation_api(operapihost)
        if request.method == 'GET':
            instancelist = list()
            username = request.GET['username']
            token =  request.GET['token']
            taskid =request.GET['taskid']
            userpofile =  api.get_userprofile(token,username)
            customer =  api.get_customerinfo(token,userpofile.customer_id)
            monitorlist = api.get_instances(token,instancelist)
            regionlist= list(set([instance.region_name for instance in monitorlist]))
            context_dict ={'customer': customer,'task_id':taskid,'region_list':regionlist ,'monitor_list':monitorlist}
            return render_to_response('lookglass/task/taskconfig.html',context_dict)

        if request.method == 'POST':
            username = request.POST['username']
            token =  request.POST['token']
            action = request.POST['action']
            if action == 'delete':
                taskid = int(request.POST['taskid'])
                task = Task.objects.get(pk =  taskid)
                if task:
                    task.enabled = False
                    temptask = task.save()
                    periodictask = PeriodicTask.objects.get(pk =  task.periodictask_id)
                    if periodictask:
                        periodictask.enabled = False
                        periodictask.save()
                        response_data['status_code'] = 200
                        response_data['message'] = "period task disable success"
                    else:
                        response_data['status_code'] = 403
                        response_data['message'] = "period task is not existed"
                else:
                    response_data['status_code'] = 403
                    response_data['message'] = "task is not existed"

            if action =='new':
                taskstarttime = datetime.strptime(request.POST['taskstarttime'], '%Y/%m/%d %H:%M')
                taskevery =  request.POST['taskevery']
                taskperiod =  request.POST['taskperiod']
                tasktimes = request.POST['tasktimes']
                taskcommand =  request.POST['taskcommand']
                taskhost =  request.POST['taskhost']
                tasknodes =  request.POST['tasknodes']
                curl_domain =  request.POST['curl_domain']
                curl_port=  request.POST['curl_port']
                curl_ip = request.POST['curl_ip']
                tcp_port = request.POST['tcp_port']
                digtype = request.POST['digtype']
                digdns = request.POST['digdns']
                msg_type = request.POST['msg_type']
                msg_times = request.POST['msg_times']
                lg_origin = ""
                userpofile =  api.get_userprofile(token,username)
                user_id = userpofile.user_id
                customer_id = userpofile.customer_id
                customer_name = userpofile.customer_name

                taskname = "{}_{}_{}_{}_task-{}".format(taskcommand,taskevery,taskperiod,tasktimes,my_random_string(6))

                ## get post data 
                lgnodeapi = lg_nodes_api("","","")
                postdata = json.dumps(lgnodeapi.get_postdata(taskcommand,taskhost,lg_origin,curl_domain,curl_port,curl_ip,tcp_port,digtype,digdns))

                ## worker task name
                task = Create_or_delete_Task(0,customer_id,user_id,0,taskname,taskstarttime,taskevery,taskperiod,tasktimes
                                                ,taskcommand,taskhost,postdata,tasknodes,"Ready",username,False)
                if task:
                    ## get task arg 
                    command_site = "%s;%s;%s;%s;%s;%s;%s;%s;%s"%(taskcommand,taskhost,lg_origin,curl_domain,curl_port,curl_ip,tcp_port,digtype,digdns)
                    test_param = [task.id,user_id,customer_name,tasknodes,tasktimes,command_site]
                    task_job_name = "worker.worker.task_lg"
                    predictask = Create_or_delete_Predic_Task(0,taskname,task_job_name,taskstarttime,taskevery,taskperiod,test_param,False)
                    if predictask:
                        savetask = Task.objects.get(pk = task.id)
                        if savetask:
                            savetask.periodictask_id = predictask.id
                            savetask.save()
                            if  savetask.periodictask_id!=0:
                                response_data['message']  = serializers.serialize('json', [task,])
                                response_data['status_code'] = 200
                            else:
                                status = TaskStatus.objects.get(name = 'Fail')
                                savetask.status = status
                                savetask.save()
                                response_data['status_code'] = 403
                                response_data['message'] = "update task fail"
                        else:
                            response_data['status_code'] = 403
                            response_data['message'] = "task not existed"

                    else:
                        status = TaskStatus.objects.get(name = 'Fail')
                        savetask.status = status
                        savetask.save()
                        response_data['status_code'] = 403
                        response_data['message'] = "Create predictask fail"

                else:
                    response_data['status_code'] = 403
                    response_data['message'] = "Create task fail"
        return HttpResponse( json.dumps(response_data), content_type="application/json")
    except Exception as e:
        message =  "Exception : "+ str(e)
        response_data['message'] = message
        response_data['status_code'] = 408
        log.logger.info('message:'+message)

        return HttpResponse( json.dumps(response_data), content_type="application/json")

def lg_task_history(request):
    try:
        username = request.GET['username']
        token =  request.GET['token']
        taskid = request.GET['taskid']
        if token:
            api =  lg_operation_api(operapihost)
            userpofile =  api.get_userprofile(token,username)
            user_id = userpofile.user_id
            customer_name = userpofile.customer_name
            monitorlist = api.get_instances(token,None)
            res_data = []
            count = 200
            task =  Task.objects.get(pk = int(taskid))
            query_task_id = "{}-{}".format(task.name,taskid)
            history =lg_history_api(customer_name,user_id,count)
            response_data = history.search_lg_history_bytask(query_task_id)
            data_list =response_data.json()["result"]
            for item in data_list:
                red_item = item
                del red_item["header"]
                del red_item["body"]
                del red_item["result"]
                tranfer_time = datetime.strptime(red_item["published_date"],'%a, %d %b %Y %H:%M:%S %Z')+ timedelta(hours=8)
                red_item["published_date"] = tranfer_time.strftime("%Y/%m/%d %H:%M")
                red_item["status_code"] =  red_item["status_code"].replace("<br/>","\n")
                red_item["total_time"] =  red_item["total_time"].replace("<br/>","\n")
                res_data.append(red_item)
            context_dict ={'detaillist':res_data, 'supportfilter':'True'}
            response = render_to_response('lookglass/history/history_detail.html',context_dict)
            return response
        else:
            return("No auth to access")
    except Exception as e:
        message =  "Exception : "+ str(e)
        return HttpResponse( message)

def get_ssh_result(command,ssh_host,ssh_port,curl_host,domain,_ip,_port):
    try:
        json_obj = {"command": command}
        ssh_tool = sshtool("","","","")
        ssh_tool.host = ssh_host
        ssh_tool.port = ssh_port
        if ssh_host == '112.74.176.96':
            ssh_tool.host = ssh_host
            ssh_tool.port = 22
            ssh_tool.username = 'root'
            ssh_tool.password ='L3tr0n&mlytics'

        start = time.time()
        if ssh_tool.connect():
            ssh_tool.exec_command(command)
            if ssh_tool.output:
                status_code=200
            else:
                status_code=400

            json_obj["result"] = ssh_tool.output.replace("\n","<br/>")
            json_obj["status_code"] = status_code

            json_obj["total_time"] = ssh_tool.output.split("\n")[-1]
            ssh_tool.client.close()
        return json.dumps(json_obj)

    except Exception as e:
        json_obj = {"command": "curl", "domain": domain, "host": curl_host, "port": _port, "ip": _ip}
        json_obj["status_code"] = 404
        json_obj["result"] =   "Exception : "+ str(e)
        return json.dumps(json_obj)

def create_history(customer,user_id,monitor_name,host,port,command,res_data):
    try:
        ## parsing content
        parsing = lg_parse(host,port,command,res_data)
        status_code,total_time,down_link,header,body  = parsing.parsing_content()

        ## create lg history
        if status_code:
            task_id = "1"
            history =lg_history_api(customer,user_id,100)
            res = history.create_lg_history(task_id,monitor_name,command,host,status_code,total_time,down_link,header,body,res_data)
            log.logger.info("create_history post status:"+res.text)
    except Exception as e:
        message =  "Exception : "+ str(e)
        log.logger.info("[message]create_history post status:{}".format(message))

def rebuld_instance(datalist):

    #delete all item
    instance.objects.all().delete()

    #new item list
    for item in datalist:
        tmp_region = region.objects.get(chinese_name = item.region)
        tmp_isp =  isp.objects.get(name = item.isp)
        tmp_status = status.objects.get(name = item.status_name)
        tmp_instance = instance(instance_id = item.nid,host_name = "",chinese_name = item.ch_name,host_ip = item.host_ip ,i_region = tmp_region,
                                        i_isp = tmp_isp, i_status = tmp_status)
        tmp_instance.save()

#### task ####
def Create_or_delete_Predic_Task(periodtask_id,taskname,taskjobname,taskstarttime,taskevery,taskperiod,taskarg,deleted):
    result = None
    try:
        if periodtask_id == 0:
            if deleted == False:
                periodvalue = IntervalSchedule.MINUTES
                if taskperiod == 'Days':
                    periodvalue = IntervalSchedule.DAYS
                if taskperiod == 'Hours':
                    periodvalue = IntervalSchedule.HOURS
                if taskperiod == "Seconds":
                    periodvalue = IntervalSchedule.SECONDS

                schedule, created = IntervalSchedule.objects.get_or_create(every=taskevery, period=periodvalue)

                periodictask = PeriodicTask.objects.create(interval=schedule, name=taskname,
                                                           task=taskjobname, args=json.dumps(taskarg), start_time=taskstarttime)
                
                return periodictask
        else:
            if deleted == True:
               periodtask =  PeriodicTask.objects.get(pk =periodtask_id)
               periodtask.enabled = False
               return periodtask.save()
    except Exception as e:
        message = "Exception : "+ str(e)
        log.logger.info('message:'+message)
        return  None

def Create_or_delete_Task(taskid,cid,uid,period_id,name,starttime,every,period,times,
                          command,command_host,command_postdata,nodes,status_name,created_by,deleted):
    try:
        if taskid == 0:
            status = TaskStatus.objects.get(name = status_name)
            log.logger.info('status:{}'.format(status))
            task =  Task.objects.create(cid=cid,uid=uid,periodictask_id=taskid,name=name,starttime=starttime,period=period
                        ,every=every,times=times,command=command,command_host=command_host,command_postdata=command_postdata
                        ,nodes=nodes,status=status,created_by=created_by,updated_by=created_by)
            return task
        else:
            if deleted ==  True:
                task = Task.objects.get(pk = taskid)
                task.enabled = False
                return task.save()
            else:
                return None
    except Exception as e:
        message = "Exception : "+ str(e)
        log.logger.info('message:'+message)
        return None

import uuid
def my_random_string(string_length=10):
    """Returns a random string of length string_length."""
    random = str(uuid.uuid4()) # Convert UUID format to a Python string.
    random = random.upper() # Make all characters uppercase.
    random = random.replace("-","") # Remove the UUID '-'.
    return random[0:string_length] # Return the random string.


