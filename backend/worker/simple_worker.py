'''Script with celery tasks'''
# -*- coding: UTF-8 -*-

import os
import sys
import random
import io
import traceback

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_DIR = os.path.join(BACKEND_DIR, 'server')
sys.path.insert(0, SERVER_DIR)

from task_updater import TaskUpdater
from crash_methods import crash_with_segfault, crash_with_import
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
import logging

import time
from celery import Celery
from celery import shared_task
import imp
import json
import requests
from http_parser.parser import HttpParser
from http_parser.util import b
from worker.sshtool import sshtool
from worker.lgparse import lg_parse
from worker.lgnodesapi import lg_nodes_api 
from worker.lghistoryapi import lg_history_api
from worker.lgoperationapi import lg_operation_api, UserProfile,HTConfig,Instance,Protocol
from worker.config import operapihost,admin,adminpw
from mlog import Log 
from nodesapi import nodes_heartbeat_api,Node_HTConfig
from lookglass.models import Task,TaskStatus,TaskDetail,TaskReport
from django_celery_beat.models import PeriodicTask

#from config import CUSTOMER
#from config import node_api_token

#log = get_task_logger(__name__)
#CELERY_BROKER_URL = 'redis://redis:6379/0'
#CELERY_RESULT_BACKEND = 'redis://10.5.134.108:6378/0'
#WORKERS = Celery('simple_worker',broker=CELERY_BROKER_URL,backend=CELERY_RESULT_BACKEND)
#WORKERS.autodiscover_tasks()

WORKERS = Celery('simple_worker')
WORKERS.config_from_object('celeryconfig')
ymldir = '/app/heartbeat/monitors.d'
LOGDIR = '/app/backend/worker/log'

logger = get_task_logger(__name__)

@WORKERS.task(name='worker.worker.task_add',bind=True)
def task_add(self,*test_data):
    try:
        log = Log("task_addlog","task_addlog")
        channel_name = 'tools'
        print(test_data)
        channel_name = test_data[0]
        logger.info("channel_name:%s"%(channel_name))
        if channel_name == 'tools':
            user_id = test_data[1]
            customer = test_data[2]
            tag_index = test_data[3]
            group_name = test_data[4]
            region_name = test_data[5]
            monitor_name = test_data[6]
            ip = test_data[7]
            command_site =  test_data[8]
            msg_type = test_data[9]
            msg_times = int(test_data[10])

            command = command_site.split(";")[0]
            host = command_site.split(";")[1].strip()
            origin = command_site.split(";")[2]
            domain = command_site.split(";")[3]
            port = command_site.split(";")[4]
            domain_ip = command_site.split(";")[5]
            tcp_port = command_site.split(";")[6]
            dns_type = command_site.split(";")[7]
            dns_server = command_site.split(";")[8]
            for index in range(0, msg_times):
                status_code,res_data,testresult = get_lg_node_result(region_name,monitor_name,ip,command,host,origin,domain,port,domain_ip,tcp_port,dns_type,dns_server,tag_index)
                log.logger.info("[get_lg_node_result]{} : {}".format(status_code,testresult))
                update_status(self.update_state,group_name,index,msg_type,100,"case completed",testresult)
                if res_data is not None and status_code!=408:
                    history_id = create_lghistory(1,user_id,customer,monitor_name,command,host,testresult,res_data)
                    logger.info("[task_add]: create lg history : {}".format(history_id))

        elif channel_name == 'monitors':
            action =  test_data[1]
            if action == 'query':
                customer_id = test_data[2]
                customer_name = test_data[3]
                region_id = test_data[4]
                group_name = test_data[5]
                monitor_id = test_data[6]
                monitor_ip =  test_data[7]
                command = test_data[8]
                logger.info("customer_id:%s,customer_name:%s,region_id:%s,group_name:%s,monitor_id:%s,monitor_ip:%s,command:%s"%(customer_id,customer_name,region_id,group_name,monitor_id,monitor_ip,command))

                msg_type = 'monitor_query_message'
                testresult = get_monitor_htconfig(region_id,customer_id,monitor_id,customer_name,monitor_ip)

                update_status(self.update_state,group_name,1,msg_type,100,"case completed",testresult)

    except Exception as exc:
            self.retry(countdown=1, exc=exc)
            print(exc)
            #response = "error"


@WORKERS.task(name='worker.worker.task_deploy',bind=True)
def task_deploy(self,*test_data,**kwargs):
    log = Log("task_deploylog","task_deploylog")
    log.logger.info("start to deploy")
    Action = test_data[0]
    token = test_data[1]
    config_instance_id = test_data[2]
    userpofile,protocol,config,instance = get_deploy_data(kwargs)
    htdeploy = HeatbeatDeploy(userpofile.customer_id,userpofile.customer_name,protocol,config,instance)
    username = userpofile.user_name
    yml_file_name = config.hb_yml_name
    protocol_name = protocol.name
    instance_name = instance.ch_name
    log.logger.info("[{}:{}]{}:{},{},{}".format(Action,config_instance_id,username,yml_file_name,protocol_name,instance_name))

    ### set status to deploy
    configinstance = Update_ConfigInstance(token,config_instance_id,3,None) 
    log.logger.info("[configinstance] {} status is {}, enable is {} ".format(configinstance.id,configinstance.status,configinstance.enabled))
    if Action == 'New':   
        username = userpofile.user_name
        yml_file_name = config.hb_yml_name
        protocol_name = protocol.name
        instance_name = instance.ch_name

        ## create yml file
        createtime = 1
        status_code ,result = htdeploy.Create_yml_file()
        if status_code == 200 or status_code == 408: 
           status_code, result = htdeploy.Check_yml_file()
           log.logger.info("[{}-{}:{}]{}:{},{},{}:{}-{}".format(createtime,Action,config_instance_id,username,yml_file_name,protocol_name,instance_name,result,status_code))
           while result ==False or result == None:
                 if createtime >3:
                    break
                 else:
                    createtime +=1
                    status_code, result = htdeploy.Create_yml_file()
                    if status_code == 200 or status_code == 408:
                       status_code, result = htdeploy.Check_yml_file()
                       log.logger.info("[{}-{}:{}]{}:{},{},{}:{}-{}".format(createtime,Action,config_instance_id,username,yml_file_name,protocol_name,instance_name,result,status_code))
        if result == True:
            ### set status to ready
            configinstance = Update_ConfigInstance(token,config_instance_id,1,True) 
            log.logger.info("[configinstance] {} status is {}, enable is {} ".format(configinstance.id,configinstance.status,configinstance.enabled))
            log.logger.info("new deploy success:{}".format(config_instance_id))
        else:
            log.logger.info("new deploy fail:{}".format(config_instance_id))

    elif Action == 'Delete':
        deletedtime = 1
        result = htdeploy.Delete_yml_file()
        if result != None:
            status_code, result = htdeploy.Check_yml_file()
            log.logger.info("[{}-{}:{}]{}:{},{},{}:{}-{}".format(deletedtime,Action,config_instance_id,username,yml_file_name,protocol_name,instance_name,result,status_code))
        while status_code !=403:
            if deletedtime >3:
                break
            else:
                deletedtime +=1
                result = htdeploy.Delete_yml_file()
                if result!= None:
                    status_code, result = htdeploy.Check_yml_file()
                    log.logger.info("[{}-{}:{}]{}:{},{},{}:{}-{}".format(deletedtime,Action,config_instance_id,username,yml_file_name,protocol_name,instance_name,result,status_code))
        if status_code == 403:
            ### set status to ready and enable is false
            configinstance = Update_ConfigInstance(token,config_instance_id,1,False) 
            log.logger.info("[configinstance] {} status is {}, enable is {} ".format(configinstance.id,configinstance.status,configinstance.enabled))
            log.logger.info("delete deploy success:{}".format(config_instance_id))
        else:
            log.logger.info("delete deploy fail:{}".format(config_instance_id))
        
'''
@periodic_task(run_every=(crontab()),name="check_task", ignore_result=True)
def check_task():
    log = Log("periodiclog","periodiclog")
    log.logger.info("Start checking...")
'''
@periodic_task(run_every=(crontab(minute='*/2')),name="check_task", ignore_result=True)
def check_task():
   
    log = Log("periodiclog","periodiclog")
    log.logger.info("Start checking...")
    api =  lg_operation_api(operapihost)
    token =  api.get_jwt_token(admin,adminpw)
    htconfiglist = api.get_HTInstances(token)

    deploystatus = 3
    deployinstancelist = list([item for item in htconfiglist if item.status == deploystatus])
    log.logger.info("[re-deploy]count:{}".format(len(deployinstancelist)))

    for item in deployinstancelist:
        config = api.get_HTConfig(token,item.heartbeat)
        customer = api.get_customerinfo(token,config.cid)
        protocol = api.get_protocol(token,config.hb_protocol)
        instance = api.get_instance(token,item.instance)
        htdeploy = HeatbeatDeploy(customer.id,customer.name,protocol,config,instance)

        customer_name = customer.name
        yml_file_name = config.hb_yml_name
        protocol_name = protocol.name
        instance_name = instance.ch_name
        log.logger.info("[re-deploy]info:{},{},{},{}-{}".format(customer_name,yml_file_name,protocol_name,instance_name,item.enabled))
        if item.enabled == True:
            ## create yml file
            status_code,result = htdeploy.Create_yml_file()
            log.logger.info("[New-{}]{}:{},{},{}:{}-{}".format(item.heartbeat,customer_name,yml_file_name,protocol_name,instance_name,result,status_code))
            if status_code == 200 or status_code == 408: 
               status_code, result = htdeploy.Check_yml_file()
               log.logger.info("[New-{}]{}:{},{},{}:{}-{}".format(item.heartbeat,customer_name,yml_file_name,protocol_name,instance_name,result,status_code))
               if result == True:
                   ### set status to ready
                   configinstance = Update_ConfigInstance(token,item.id,1,True) 
                   log.logger.info("[configinstance] {} status is {}, enable is {} ".format(item.id,item.status,item.enabled))
                   log.logger.info("new deploy success:{}".format(item.id))
               else:
                   log.logger.info("new deploy fail:{}".format(item.id))

                
        elif item.enabled == False:
            result = htdeploy.Delete_yml_file()
            if result != None:
                status_code, result = htdeploy.Check_yml_file()
                log.logger.info("[Delete-{}]{}:{},{},{}:{}-{}".format(item.heartbeat,customer_name,yml_file_name,protocol_name,instance_name,result,status_code))
                if status_code == 403:
                    ### set status to ready and enable is false
                    configinstance = Update_ConfigInstance(token,item.id,1,False) 
                    log.logger.info("[configinstance] {} status is {}, enable is {} ".format(item.id,item.status,item.enabled))
                    log.logger.info("delete deploy success:{}".format(item.id))
                else:
                    log.logger.info("delete deploy fail:{}".format(item.id)) 


@WORKERS.task(name='worker.worker.task_lg',bind=True)
def task_lg(self,*test_data):
    log = Log("periodiclog","periodiclog")
    log.logger.info("[{}][task_lg]Start checking...{}".format(self.request.id,test_data))
    task_id = int(test_data[0])
    user_id = test_data[1]
    customer_name = test_data[2]
    nodes = test_data[3]
    times = int(test_data[4])
    command_site = test_data[5]
    command = command_site.split(";")[0]
    host = command_site.split(";")[1].strip()
    origin = command_site.split(";")[2]
    domain = command_site.split(";")[3]
    port = command_site.split(";")[4]
    domain_ip = command_site.split(";")[5]
    tcp_port = command_site.split(";")[6]
    dns_type = command_site.split(";")[7]
    dns_server = command_site.split(";")[8]
    node_list = nodes.split(';')
    api =  lg_operation_api(operapihost)
    token =  api.get_jwt_token(admin,adminpw)

    task =  Task.objects.get(pk = task_id)
    taskdetaillist = TaskDetail.objects.filter(task = task ,enabled =True)
    log.logger.info("[task_lg]taskdetaillist length : {} , times: {}".format(len(taskdetaillist),times))

    if len(taskdetaillist) >= times:
        status = TaskStatus.objects.get(name = 'Completed')
        task.status = status
        task.save()

        periodtask = PeriodicTask.objects.get(pk = task.periodictask_id)
        periodtask.enabled = False
        periodtask.save()
    else:
        status = TaskStatus.objects.get(name = 'Running')
        task.status = status
        task.save()
        taskdetail =  TaskDetail.objects.create(task = task, task_request_id= self.request.id)
        if taskdetail:
            for node in node_list:
                tag_index = node
                instance = api.get_instance(token,int(node))
                region_name = instance.region_name
                monitor_name = instance.ch_name
                ip = instance.host_ip
                status_code,res_data,testresult = get_lg_node_result(region_name,monitor_name,ip,command,host,origin,domain,port,domain_ip,tcp_port,dns_type,dns_server,tag_index)

                if res_data is not None and status_code!=408:
                    history_task_id = "{}-{}".format(task.name,task.id)
                    history_id = create_lghistory(history_task_id,user_id,customer_name,monitor_name,command,host,testresult,res_data)
                    log.logger.info("[task_lg]create lg history : {}".format(history_id))
                    if history_id!=0:
                        taskreport = TaskReport.objects.create(detail = taskdetail,history_id = history_id,instaince_id =int(node))
                        log.logger.info("[task_lg]create taskreport : {}".format(taskreport))


def update_status(update_state,channel_name,index,msg_type,task_progress,test_case,test_result):
    #update_state(state='PROGRESS', meta={'progress': task_progress,'db_id': 1000})
    #updatetask = TaskUpdater()
    TaskUpdater.update_ws(channel_name,{"round": index,"type": msg_type,"progress":task_progress,"test_case":test_case ,"test_result": test_result})
    logger.info("TaskUpdater send finish.")
    #del updatetask
    
def get_lg_node_result(region_name,monitor_name,lg_ip,lg_command,lg_host,lg_origin,curl_domain,
                        curl_port,curl_ip,tcp_port,nslookup_type,nslookup_dns,tag_index):
    json_obj={}
    res_data=None
    status_code =408
    json_obj["command"] = lg_command
    json_obj["region_name"] =  region_name
    json_obj["monitor_name"] = monitor_name
    json_obj["tag_index"] = str(tag_index)
    lgnodeapi = lg_nodes_api(region_name,monitor_name,lg_ip)
    try:
        res_data = lgnodeapi.get_nodes_api(lg_command,lg_host,lg_origin,curl_domain,curl_port,curl_ip,tcp_port,nslookup_type,nslookup_dns)
        
        ## parsing lg history
        parsing = lg_parse(lg_host,tcp_port,lg_command,res_data)
        status_code,total_time,down_link,header,body  = parsing.parsing_content()

        json_obj["monitor_ip"] = lg_ip
        json_obj["status_code"]=status_code
        json_obj["total_time"] = total_time
        json_obj["header"] = header
        json_obj["body"]= body
        json_obj["downlink"] = down_link ## for har         
    except requests.exceptions.RequestException as e:
            message =  "Exception : "+ str(e)
            json_obj["tag_index"] = str(tag_index)
            json_obj["result"] = message
            json_obj["status_code"] = 408
            json_obj["total_time"] = 5
    return status_code,res_data, json.dumps(json_obj)

def get_monitor_htconfig(region_id,customer_id,monitor_id,customer_name,host_ip):

    try:
        json_obj={}
        ssh_tool = sshtool("","","","")
        ssh_tool.host = host_ip
        ssh_tool.port = '20022'
        if customer_id ==0:
            json_obj["tag_index"] = "%s-%s"%(monitor_id,region_id)
        else:
            json_obj["tag_index"] = "%s-%s-%s"%(monitor_id,region_id,customer_id)
        if ssh_tool.connect():
            logger.info("connect")
            command = 'ls /opt/heartbeat/monitors.d/ | grep %s'%(customer_name)
            result =  ssh_tool.exec_command(command)
            if result:
                output = ssh_tool.output
                itemlist = output.strip().split("\n")
                json_obj["file"] =  itemlist
                file_list = list()
                content_list = list()
                for item in itemlist:
                    command = 'cat /opt/heartbeat/monitors.d/%s'%(item)
                    result =  ssh_tool.exec_command(command)
                    output = ssh_tool.output.strip()
                    if output :
                        file_list.append(item)
                        content_list.append(output.replace("\n","<br/>"))
                json_obj["status_code"] =200
                json_obj["file"] = file_list
                json_obj["content"] = content_list
                response_data = json.dumps(json_obj)
    except Exception as e:
                json_obj["status_code"] = 408
                message =  "Exception : "+ str(e)
                json_obj["file"]=''
                json_obj["content"] = message
                response_data = json.dumps(json_obj)
    return response_data

def get_ssh_result(command,ssh_host,ssh_port):
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
            return json_obj

    except Exception as e:
        json_obj = {"command": command}
        json_obj["status_code"] = 404
        json_obj["result"] =   "Exception : "+ str(e)
        return json_obj

def get_ssh_result_with_ws(group_name,index,msg_type,command,ssh_host,ssh_port):
    try:
        port = 20022
        json_obj = {"command": command}
        ssh = paramiko.SSHClient()  
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) 
        if ssh_host == '112.74.176.96':
            ssh.connect(hostname=ssh_host, username=conf.USERNAME, password=conf.PASSWORD,port=port)     
            stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
            while True:
                nextline = stdout.readline()
                test_result = nextline.strip().encode('utf-8')
                update_status(self.update_state,group_name,index,msg_type,100,"case completed",)
                if nextline == "" and nextline != None:
                        break

    except Exception as e:
        json_obj = {"command": command}
        json_obj["status_code"] = 404
        json_obj["result"] =   "Exception : "+ str(e)
        return json_obj

    body = res["result"]
    total_time= 0
    totalsize = 0
    downlink = ""
    status_code =res["status_code"]
    if status_code== 200:
        if res["load_time"]:
            total_time = round(int(res["load_time"]) / 1000,2) 
        if res["total_size"]:
            totalsize = round(int(res["total_size"]) / (1024*1024),2)
        
        if res["url"]:
            downlink = res["url"]
        header = "request: {} ,total size:{} MB,total loading:{}s".format(res["requests"],totalsize,total_time)
    else:
        header = "status_code: {} ,testing fail, please refresh this node.".format(status_code)
    
    return status_code,total_time,downlink,header,body

def get_deploy_data(kwargs):

    userprofile =None
    protocol = None
    config = None
    instance =  None
    if kwargs['user']:
        tmpuser = kwargs['user']
        userprofile = UserProfile(tmpuser['id'],tmpuser['user_id'],tmpuser['user_name'],tmpuser['customer_id'],tmpuser['customer_name'],tmpuser['credential'])

    if kwargs['protocol']:
        tmpprotocol = kwargs['protocol']
        protocol = Protocol(tmpprotocol['id'],tmpprotocol['name'])

    if kwargs['config']:
        tmpconfig = kwargs['config']
        config = HTConfig(tmpconfig['id'],tmpconfig['cid'],tmpconfig['hb_protocol'],tmpconfig['hb_tag'],tmpconfig['hb_yml_name'],tmpconfig['schedule']
                          ,tmpconfig['origin'],tmpconfig['enabled'],tmpconfig['created_by'],tmpconfig['created_time'],tmpconfig['updated_by'],tmpconfig['updated_time']
                          ,tmpconfig['url_heartbeat'],tmpconfig['detail_heartbeat'])

    if kwargs['instance']:
        tmpinstance = kwargs['instance']
        instance = Instance(tmpinstance['id'],tmpinstance['nid'],tmpinstance['host_name'],tmpinstance['region_name']
                            ,tmpinstance['isp_name'],tmpinstance['ch_name'],tmpinstance['host_ip'],tmpinstance['status_name'])
    
    return userprofile,protocol,config,instance

def create_lghistory(task_id,user_id,customer,monitor_name,lg_command,lg_host,test_data,res_data):
    try:
        ## create lg history
        log = Log("lg_history_api","lg_history_api_log")
        test_data = json.loads(test_data)
        status_code = test_data['status_code']
        total_time = test_data['total_time']
        down_link = test_data['downlink']
        header = test_data['header']
        body = test_data['body']
        history =lg_history_api(customer,user_id,100)
        res = history.create_lg_history(task_id,monitor_name,lg_command,lg_host,status_code,total_time,down_link,header,body,res_data)
        log.logger.info("create lg history res:{}".format(res))
        if res:
            resjson = res.json()
            log.logger.info("create lg history resjson:{}".format(resjson))
            if 'successfully' in resjson["msg"] :
                return resjson['id']
            else:
                return 0
    except Exception as e:
        log.logger.error("create lg history error:"+ str(e))
        return 0

def Update_ConfigInstance(token,config_instance_id,status,enabled):
    api =  lg_operation_api(operapihost)
    return api.patch_HTConfigInstance(token,config_instance_id,status,enabled)



class HeatbeatDeploy(object):
    def __init__(self,customer_id,customer_name,protocol,config,instance):
        self.config = config
        self.instance =  instance
        self.protocol = protocol
        self.customer_id = customer_id
        self.customer_name = customer_name
        self.is_asia = False
        if self.instance.region_name=='亞太':
            self.is_asia = True
   
    def Create_yml_file(self):
        log = Log("lg_operation_api","lg_operation_api_log")
        try:
            log.logger.info("Create_yml_file.{} ,{} , {}".format(self.config.id,self.customer_name ,self.instance.id))
            ### get url string ###
            tmpurl=''
            for url in sorted(self.config.url_heartbeat, key=lambda k: k.get('id', 0),reverse=True):
                if url['enabled'] == True:
                    tmpurl = tmpurl +'\"{}\"'.format(url['full_url'])+","

            log.logger.info("tmpurl:{}".format(tmpurl))
            ### get detail ##
            checkrequest = ''
            checkreponse=''
            log.logger.info("protocol:{}".format(self.protocol.name))

            if self.protocol.name == 'http':
                log.logger.info("detail_heartbeat:{}".format(self.config.detail_heartbeat))
                if self.config.detail_heartbeat:
                    checkrequest = next((detail['value'] for detail in self.config.detail_heartbeat if detail['key'] =='check.request'), None)
                    checkreponse= next((detail['value'] for detail in self.config.detail_heartbeat if detail['key'] =='check.response'), None)
            
            node_ht = nodes_heartbeat_api(self.instance.host_ip,self.is_asia)
            if node_ht.token:
                if self.customer_name == 'SSM':
                   customer_id = 2
                else:                  
                   customer_id = self.customer_id
                customer_name = self.customer_name
                region =  self.instance.region_name
                isp =   self.instance.isp_name
                monitor =  self.instance.ch_name
                schedule =  self.config.schedule
                url = tmpurl
                ht_yml_file =  self.config.hb_yml_name
                ht_type =   self.protocol.name
                origin =  self.config.origin
                node_config = Node_HTConfig(customer_id,customer_name,region,isp,monitor,schedule,url,ht_yml_file,ht_type,origin)
                return node_ht.New_HTConfig(node_config,checkrequest,checkreponse)
            else:
                return False
        except Exception as e:
            message =  "Exception : "+ str(e)
            error_class = e.__class__.__name__ #取得錯誤類型
            detail = e.args[0] #取得詳細內容
            cl, exc, tb = sys.exc_info() #取得Call Stack
            lastCallStack = traceback.extract_tb(tb)[-1] #取得Call Stack的最後一筆資料
            fileName = lastCallStack[0] #取得發生的檔案名稱
            lineNum = lastCallStack[1] #取得發生的行號
            funcName = lastCallStack[2] #取得發生的函數名稱
            errMsg = "File \"{}\", line {}, in {}: [{}] {}".format(fileName, lineNum, funcName, error_class, detail)
            log.logger.info(errMsg)
            return False

    def Delete_yml_file(self):
        log = Log("lg_operation_api","lg_operation_api_log")
        try:
            #log.logger.info("Delete_yml_file")
            node_ht = nodes_heartbeat_api(self.instance.host_ip,self.is_asia)
            if node_ht.token:
                return node_ht.Delete_HTConfig( self.config.hb_yml_name)
            else:
                return False
        except Exception as e:
            message =  "Exception : "+ str(e)
            log.logger.info(message)
            return False

    def Check_yml_file(self):
        log = Log("lg_operation_api","lg_operation_api_log")
        result = True
        status_code = 0
        status_code,yml_file = self.Get_yml_file_info()
        if status_code == 200 :
            url_content = ','.join(yml_file['content'])
            for url in self.config.url_heartbeat:
                if url['enabled']== True:
                   if url['full_url'] not in url_content:
                      result =  False
                      break
        else:
            result = False
        log.logger.info("[Check_yml_file]{} : {}".format(status_code,result))
        return status_code,result
        
    def Get_yml_file_info(self):
        log = Log("lg_operation_api","lg_operation_api_log")
        try:
            #log.logger.info("Get_yml_file")
            node_ht = nodes_heartbeat_api(self.instance.host_ip,self.is_asia)
            if node_ht.token:

                return node_ht.Get_HTConfig(self.config.hb_yml_name)
            else:
                return 0,None
        except Exception as e:
            message =  "Exception : "+ str(e)
            log.logger.info(message)
            return None
