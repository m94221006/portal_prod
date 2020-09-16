# -*- coding: UTF-8 -*-

from django.shortcuts import render
from django.shortcuts import render_to_response
from django.http import HttpResponse

#from worker.sshtool import 
import json
from worker.lgoperationapi import lg_operation_api,JobInstanceDetail,Monitorsummary
from worker.mlog import Log
from worker.config import WS_IP, WS_PORT,USERID
from worker.config import operapihost
from worker.simple_worker import WORKERS , HeatbeatDeploy
import sys, traceback
from worker.lgmessage import lg_message_api



log = Log("over","lookglasslog")
# Create your views here.
def index(request):
    try:
        username = request.GET['username']
        token =  request.GET['token']
        api =  lg_operation_api(operapihost)
        userpofile =  api.get_userprofile(token,username)
        urllist = get_config_list(token,userpofile.customer_id)
        cid=  userpofile.customer_id


        alertstatus = 0
        notifytype = api.get_notifytypebyname(token,"telegram")
        customercontact = api.get_customercontactbynotify(token,cid,notifytype.id)
        if customercontact and customercontact.subject !='disable':
            alertstatus = 1

        context_dict ={'username':username,'urllist':urllist,'alertstatus':alertstatus}
        return render_to_response('monitor/monitor_index.html',context_dict)
    except Exception as e:
        message =  "Exception : "+ str(e)
        return HttpResponse( message)

def Config_Detail(request):
    try:
        username = request.GET['username']
        token =  request.GET['token']
        config_id = int(request.GET['config_id'])
        configdetail = get_configdetail(token,config_id,True)
        return HttpResponse(json.dumps(configdetail.__dict__), content_type="application/json")
    except Exception as e:
        message =  "Exception : "+ str(e)
        log.logger.info(message)

        return HttpResponse( message)

def Config_Deploy(request):
    try:
        response_data={}
        action = request.GET['action']
        config_id = int(request.GET['config_id'])
        protocol = request.GET['protocol']
        token =  request.GET['token']
        username = request.GET['username']
        api =  lg_operation_api(operapihost)

        userpofile =  api.get_userprofile(token,username)
        customer =  api.get_customerinfo(token,userpofile.customer_id)

        protocollist = api.get_protocols(token)
        instancelist = customer.instance
        monitorlist = api.get_instances(token,instancelist)
        regionlist = list()
        if monitorlist:
            regionlist= list(set([instance.region_name for instance in monitorlist]))

        configlist = api.get_HTConfigs(token,userpofile.customer_id)
        configmaxurlcount = customer.max_url_num
        configurlcount=0
        if configlist:
            configurlcount = get_existed_url_count(configlist)
        configmininterval = customer.min_interval_num
        configintervallist = get_interval_list(configmininterval)

        context_dict={}
        if action == 'new':
            configinterval=0
            configurl = ""
            configothers=""
            confignodes=""
            confignodeids =""


        elif action == 'edit':
            config = api.get_HTConfig(token,config_id)
            configdetail = get_configdetail(token,config_id,True)
            configinterval = config.schedule
            configurl = configdetail.urls
            configothers = configdetail.others
            confignodes = configdetail.nodes
            confignodeids = configdetail.node_ids
            configprotocol = api.get_protocol(token,config.hb_protocol)
            configreponse = ''
            configreponse = ''
            configrequest_method =''
            configrequest_header =''
            configrequest_body=''
            configresponse_status=''
            configresponse_body=''
            
            configcheckreponse =''
            if configdetail.checkrequest: 
                configrequest = json.loads(configdetail.checkrequest)
                if configrequest['method']:
                    configrequest_method = configrequest['method']
                if configrequest['headers']:
                    configrequest_header = configrequest['headers']
                    if '\n' in configrequest_header:
                        configrequest_header =  configrequest_header.replace("\n",",")
                if configrequest['body']:
                    configrequest_body = configrequest['body']
            if configdetail.checkresponse: 
                configreponse = json.loads(configdetail.checkresponse)
                if configreponse['status']:
                    configresponse_status = configreponse['status']
                if configreponse['body']:
                    configresponse_body = configreponse['body'].replace("\n",',')        
        return render_to_response('monitor/partial/HTdeploy.html',locals())
    
    except Exception as e:
        message = "Exception : "+ str(e)
        log.logger.info('message:{}'.format(message))

        response_data['message'] = message        
        return HttpResponse( json.dumps(response_data), content_type="application/json")

def Heartbeat_Config(request):
    response_data = {}
    try:
        log.logger.info("request:{}".format(request))
        if request.method=="POST":
            token =  request.POST['token']
            username = request.POST['username']
            action = int(request.POST["action"])
            config_id = int(request.POST["config_id"])
            protocol_id = request.POST["protocol_id"]
            interval = request.POST["interval"]
            jobs = request.POST["jobs"]
            nodes = request.POST["nodes"]
            checkrequest = request.POST["checkrequest"]
            checkresponse = request.POST["checkresponse"]
            wsorigin= request.POST["wsorigin"]
            message = {}
            details ={}
            config =None
            log.logger.info('checkrequest::{}'.format(checkrequest))
            log.logger.info('checkresponse:{}'.format(checkresponse))


            htoperation = HTConfigOperation(operapihost,token,username)
            api =  lg_operation_api(operapihost)
            userpofile =  api.get_userprofile(token,username)
            customer_id =  userpofile.customer_id

            if action == -1: # delete 
                    config = htoperation.Delete_config(config_id)
                    
                    ## alert update
                    if config:
                        notifytype = api.get_notifytypebyname(token,"telegram")
                        customercontact = api.get_customercontactbynotify(token,customer_id,notifytype.id)
                        if customercontact and customercontact.recipient_id:
                            alert_down_rtt_monitor_updatebyhid(token,username,action,config.id)
            
            elif  action ==  1: # new config
                    hb_tag=''
                    config = htoperation.New_Config(nodes,customer_id,protocol_id,hb_tag,interval,wsorigin,jobs,checkrequest,checkresponse)

            elif action == 2:  # Edit
                    config = htoperation.Edit_Config(nodes,config_id,jobs,interval,wsorigin,checkrequest,checkresponse)
                    
                    ## alert update
                    if config:
                        notifytype = api.get_notifytypebyname(token,"telegram")
                        if notifytype:
                           customercontact = api.get_customercontactbynotify(token,customer_id,notifytype.id)
                           if customercontact and  customercontact.subject !='disable':
                              alert_down_rtt_monitor_updatebyhid(token,username,action,config.id)
                
            
            # response result 
            if config:
                data ={}
                data['user'] = userpofile.__dict__
                data['config'] = config.__dict__
                data['protocol'] = api.get_protocol(token,config.hb_protocol).__dict__
                log.logger.info('data:'+str(data))
                log.logger.info('new config instance:'+str(len(htoperation.new_config_list)))
                log.logger.info('del config instance:'+str(len(htoperation.delete_config_list)))

                ### deploy to node ##
                newitem ={}
                delitem={}
                if htoperation.new_config_list:
                    test_param =['New',token]
                    for new_item in htoperation.new_config_list:
                         log.logger.info('new config instance id:'+str(new_item.id))
                         test_param =['New',token,new_item.id]
                         instance = api.get_instance(token,new_item.instance)
                         data['instance'] = instance.__dict__
                         WORKERS.send_task('worker.worker.task_deploy',args=test_param, kwargs = data)
                         newitem[new_item.id] = instance.ch_name


                if htoperation.delete_config_list:
                    for delete_item in htoperation.delete_config_list:
                         log.logger.info('del config instance id:'+str(delete_item.id))
                         test_param =['Delete',token,delete_item.id]
                         instance = api.get_instance(token,delete_item.instance)
                         data['instance'] = instance.__dict__
                         WORKERS.send_task('worker.worker.task_deploy',args=test_param, kwargs = data)
                         delitem[delete_item.id] = instance.ch_name

              
                response_data['newitem'] = newitem
                response_data['delitem'] = delitem
                response_data['config'] = config.__dict__
                response_data['message'] ="Create Heartbeat Config instance success"
                response_data['status_code'] = 200
            else:
                response_data['message'] = "Create Heartbeat Config instance Fail"
                response_data['status_code'] = 404

        return HttpResponse(json.dumps(response_data), content_type="application/json")

    except Exception as e:
        message = "Exception : "+ str(e)
        log.logger.info('message:'+message)
        response_data['message'] = message
        response_data['status_code'] = 408
        return HttpResponse( json.dumps(response_data), content_type="application/json")

def Heartbeat_Instance_Config(request):
    response_data = {}
    try:
        token =  request.POST['token']
        username = request.POST['username']
        config_id = request.POST['config_id']
        if token and config_id:
            api =  lg_operation_api(operapihost)
            userpofile =  api.get_userprofile(token,username)
            configinstance = api.get_HTInstance(token,int(config_id))
            config = api.get_HTConfig(token,configinstance.heartbeat)
            instance = api.get_instance(token,configinstance.instance)
            protocol = api.get_protocol(token,config.hb_protocol)
            htdeploy = HeatbeatDeploy(userpofile.customer_id,userpofile.customer_name,protocol,config,instance)
            enabled = True
            if config.enabled == True:
                status_code,result = htdeploy.Create_yml_file()
                if status_code == 200 or status_code == 408: 
                   log.logger.info('Create_yml_file result:{}'.format(result))
                   if result != None:
                      status_code, result = htdeploy.Check_yml_file()
            else:
                log.logger.info('Delete_yml_file result:{}'.format(result))
                result = htdeploy.Delete_yml_file()
                if result == False  or result == None :
                    status_code, result = htdeploy.Check_yml_file()
                    if status_code == 403:
                        result = True
                        enabled = False
            if result:
                status =1 
                saveconfiginstance =api.patch_HTConfigInstance(token,
                                                        int(config_id),
                                                        status,
                                                        enabled)
                if saveconfiginstance:
                    response_data['message'] = saveconfiginstance.__dict__
                    response_data['status_code'] = 200
                else:
                    response_data['message'] = "fail"
                    response_data['status_code'] = 400  

            else:
                response_data['message'] = "fail"
                response_data['status_code'] = 400  
            
        else:
            response_data['message'] = "not access right"
            response_data['status_code'] = 408
        return HttpResponse( json.dumps(response_data), content_type="application/json")

    except Exception as e:
        message = "Exception : "+ str(e)
        log.logger.info('message:'+message)
        response_data['message'] = message
        response_data['status_code'] = 408
        return HttpResponse( json.dumps(response_data), content_type="application/json")

def Heartbeat_Config_status(request):
    response_data = {}
    try:
        config_id = request.GET['config_id']
        token = request.GET['token']
        username = request.GET['username']
        item ={}
        if config_id and token :
            api =  lg_operation_api(operapihost)
            datalist = api.get_HTInstancebyconfig(token,int(config_id))
            response_data['configstatus'] = 1
            if datalist:
                for data in datalist:
                    item[data.id] = data.__dict__
                    if data.status != 1:
                        response_data['configstatus'] = 0
                response_data['item'] = item
                response_data['message'] ='success'
                response_data['status_code'] = 200
            else:
                response_data['message'] ='fail'
                response_data['status_code'] = 400
        else:

            response_data['message'] ='fail'
            response_data['status_code'] = 400
        return HttpResponse(json.dumps(response_data), content_type="application/json")


    except Exception as e:
        message = "Exception : "+ str(e)
        response_data['message'] = message
        response_data['status_code'] = 408
        return HttpResponse( json.dumps(response_data), content_type="application/json")


### instance ##
def instance(request):
    try:
        if request.method == 'GET':
            try:
                instancelist = list()
                username = request.GET['username']
                token =  request.GET['token']
                api =  lg_operation_api(operapihost)
                userpofile =  api.get_userprofile(token,username)
                customer =  api.get_customerinfo(token,userpofile.customer_id)

                ## all instance 
                allinstancelist = sorted(api.get_instances(token,None) , key=lambda x: x.region_name, reverse=True)

                ### in-selected
                instance_list = list([ instance for instance in allinstancelist if instance.id in customer.instance])

                ### in-used for heartbeat instance
                monitor_list = list()
                monitor_id_list = get_customer_monitor_nodes_id_list(token,userpofile.customer_id)
                if monitor_id_list:
                    monitor_list = ";".join([ str(instance_id) for instance_id in monitor_id_list])

                context_dict ={'instance_list':instance_list,'monitor_id_list':monitor_id_list,'monitor_list':monitor_list}
                return render_to_response('monitor/instance_index.html',context_dict)
            except Exception as e:
                error_class = e.__class__.__name__ #取得錯誤類型
                detail = e.args[0] #取得詳細內容
                cl, exc, tb = sys.exc_info() #取得Call Stack
                lastCallStack = traceback.extract_tb(tb)[-1] #取得Call Stack的最後一筆資料
                fileName = lastCallStack[0] #取得發生的檔案名稱
                lineNum = lastCallStack[1] #取得發生的行號
                funcName = lastCallStack[2] #取得發生的函數名稱
                errMsg = "File \"{}\", line {}, in {}: [{}] {}".format(fileName, lineNum, funcName, error_class, detail)
                log.logger.info('errMsg:'+errMsg)


        elif request.method == 'POST':
            response_data = {}
            try:
                api =  lg_operation_api(operapihost)
                customer_id = int(request.POST['customer_id'])
                username = request.POST['username']
                token =  request.POST['token']
                userpofile =  api.get_userprofile(token,username)
                instances =  request.POST['instances']
                monitor_removed =  request.POST['monitor_removed']

                ##### update customer instance
                updateinstances = instances.split(';')
                if len(updateinstances) > 0:
                    update_customer = api.patch_CustomerInstances(token,customer_id,updateinstances)


                ## remove the htconfig for no used instances
                if monitor_removed:
                   notifytype = api.get_notifytypebyname(token,"telegram")
                   customercontact = api.get_customercontactbynotify(token,customer_id,notifytype.id)
                   removed_monitor_list = monitor_removed.split(';')
                   if len(removed_monitor_list) > 0:
                        for instance_id in removed_monitor_list:
                            configinstancelist = get_customer_monitor_list_byinstanceid(token,customer_id,int(instance_id))
                            log.logger.info(len(configinstancelist))
                            for configinstance in configinstancelist:
                                log.logger.info(configinstance.id)
                                tmpconfiginstances = api.patch_HTConfigInstance(token,
                                                                                configinstance.id,
                                                                                None,
                                                                                False)
                                if tmpconfiginstances:
                                    ## deploy to the node
                                    data ={}
                                    config = api.get_HTConfig(token,configinstance.heartbeat)
                                    instance = api.get_instance(token,tmpconfiginstances.instance)
                                    data['user'] = userpofile.__dict__
                                    data['config'] = config.__dict__
                                    data['protocol'] = api.get_protocol(token,config.hb_protocol).__dict__
                                    data['instance'] = instance.__dict__
                                    test_param =['Delete',token,tmpconfiginstances.id]
                                    WORKERS.send_task('worker.worker.task_deploy',args=test_param, kwargs = data)

                                    ## alert update
                                    if customercontact and customercontact.recipient_id:
                                        alert_down_rtt_monitor_updatebyhid(token,username,1,configinstance.heartbeat)
                

                response_data['message'] = 'update success'
                response_data['status_code'] = 200
                return HttpResponse( json.dumps(response_data), content_type="application/json")

            except Exception as e:
                message = "Exception : "+ str(e)
                response_data['message'] = message
                response_data['status_code'] = 408
                
                return HttpResponse( json.dumps(response_data), content_type="application/json")
            


    except Exception as e:
        message =  "Exception : "+ str(e)
        return HttpResponse( message)


def instance_config(request):
    instancelist = list()
    username = request.GET['username']
    token =  request.GET['token']
    monitor_list =  request.GET['monitor_list']

    api =  lg_operation_api(operapihost)
    userpofile =  api.get_userprofile(token,username)
    customer =  api.get_customerinfo(token,userpofile.customer_id)
     
    ## all instance 
    allinstancelist = sorted(api.get_instances(token,None) , key=lambda x: x.region_name, reverse=True)

    ### in-selected
    instance_id_list = list([instance.id for instance in allinstancelist if instance.id in customer.instance])

    ##
    monitor_id_list = list()
    monitor_id_list = get_customer_monitor_nodes_id_list(token,userpofile.customer_id)
    if monitor_id_list and len(monitor_id_list)>0:
        monitor_id_list = list([int(instance_id) for instance_id in monitor_list.split(';')])
        monitor_list =  monitor_list

    context_dict ={'customer': customer ,'allinstancelist':allinstancelist,'instance_id_list':instance_id_list,'monitor_id_list':monitor_id_list,'monitor_list':monitor_list}
    return render_to_response('monitor/partial/instanceconfig.html',context_dict)


def allinstance(request):

    try:
        if request.method == 'GET':
            username = request.GET['username']
            token =  request.GET['token']
            api =  lg_operation_api(operapihost)
            userpofile =  api.get_userprofile(token,username)
            customer =  api.get_customerinfo(token,userpofile.customer_id)

            ## all instance 
            allinstancelist = sorted(api.get_instances(token,None) , key=lambda x: x.region_name, reverse=True)

            #all region
            allregionlist = sorted(api.get_regions(token) , key=lambda x: x.ch_name, reverse=True)

            #all isp
            allisplist= sorted(api.get_isps(token) , key=lambda x: x.name, reverse=True)

            #all status 
            allstatuslist= {"Pending","Running","Removed"}



            context_dict ={'allstatuslist':allstatuslist,'allregionlist':allregionlist,'allisplist':allisplist,'allinstancelist':allinstancelist}
            return render_to_response('monitor/allinstance_index.html',context_dict)

    except Exception as e:
        message =  "Exception : "+ str(e)
        log.logger.info('errMsg:{}'.format(message))
        return render_to_response('error/404.html', {})
        
### alert ###
'''
def Alert(request):
    try:
        context_dict ={}


        return render_to_response('monitor/alert_index.html',context_dict)
    except Exception as e:
        message =  "Exception : "+ str(e)
        return HttpResponse( message)
'''

def Alert_Confg(request):
    try:
        if request.method == 'GET':
            response_data={}
            username = request.GET['username']
            token =  request.GET['token']
            api =  lg_operation_api(operapihost)
            userpofile =  api.get_userprofile(token,username)
            notifytype = api.get_notifytypebyname(token,"telegram")
            cid = int(userpofile.customer_id)
            n_type_id = notifytype.id

            customercontact = api.get_customercontactbynotify(token,cid,notifytype.id)
            level40xerror = api.get_levelerrorbycid(token,cid,"40x")
            level50xerror = api.get_levelerrorbycid(token,cid,"50x")
            level20030xerror = api.get_levelnot20030xbycid(token,cid)
            alertstatus = 0
            if customercontact:
                if customercontact.subject !='disable':
                    alertstatus = 1
        
            context_dict ={'alertstatus': alertstatus ,'customercontact':customercontact,'level40xerror':level40xerror,
                            'level50xerror':level50xerror,'level20030xerror':level20030xerror}
            return render_to_response('monitor/partial/alertconfig.html',context_dict)

        if request.method == 'POST':
            response_data={}
            username = request.POST['username']
            token =  request.POST['token']
            alertvalue =  request.POST['alertvalue']

            api =  lg_operation_api(operapihost)
            userpofile =  api.get_userprofile(token,username)
            notifytype = api.get_notifytypebyname(token,"telegram")
            cid = userpofile.customer_id
            n_type_id = notifytype.id

            if alertvalue =="disable":
                customercontact = api.get_customercontactbynotify(token,cid,n_type_id)
                if customercontact:
                    post_result = None
                    post_result = api.patch_customercontact(token,customercontact.id,notifytype.id,customercontact.recipient_id,"disable")
                    level40xerror = api.get_levelerrorbycid(token,userpofile.customer_id,"40x")
                    if level40xerror:
                        post_result = api.patch_levelerror(token,"40x",level40xerror.id,'','','','',False)

                    level50xerror = api.get_levelerrorbycid(token,userpofile.customer_id,"50x")
                    if level50xerror:
                        post_result = api.patch_levelerror(token,"50x",level50xerror.id,'','','','',False)

                    level20030xerror = api.get_levelnot20030xbycid(token,userpofile.customer_id)
                    if level20030xerror:
                        post_result = api.patch_levelnot20030x(token,level20030xerror.id,'','','','',False)

                    leveldown= api.get_leveldownsbycid(token,userpofile.customer_id)
                    if leveldown:
                        post_result = api.patch_leveldown(token,leveldown.id,'','','','',False)

                    levelrtt = api.get_levelrttsbycid(token,userpofile.customer_id)
                    if levelrtt:
                        post_result = api.patch_levelrtt(token,leveldown.id,'','','','','',False)
                    
                    if post_result:
                        response_data['message'] = 'update success'
                        response_data['status_code'] = 200  
                    else:
                        response_data['message'] = 'update fail'
                        response_data['status_code'] = 400
                else:
                    response_data['message'] = 'uppdate success'
                    response_data['status_code'] = 200 

                return HttpResponse( json.dumps(response_data), content_type="application/json")
            if alertvalue =="enable":
                recipient_id =  request.POST['recipient_id']
                customercontact = api.get_customercontactbynotify(token,cid,n_type_id)
                #log.logger.info('customercontact id:{}'.format(customercontact.id))

                if customercontact:
                    customercontact = api.patch_customercontact(token,customercontact.id,n_type_id,recipient_id,'enable')
                else:
                    customercontact = api.post_customercontact(token,cid,n_type_id,recipient_id,'enable')
                log.logger.info('customercontact:{}'.format(customercontact))
                if customercontact:
                    post_result = customercontact
                    alert40 = request.POST["alert40X"]
                    alert50 = request.POST["alert50X"]
                    alert20030X = request.POST["alert20030X"]

                    level40xerror = api.get_levelerrorbycid(token,cid,"40x")
                    level50xerror = api.get_levelerrorbycid(token,cid,"50x")
                    level20030xerror = api.get_levelnot20030xbycid(token,cid)

            
                    if int(alert40) == 1:
                        threshold=request.POST["threshold40X"]
                        total_bucket= request.POST["tb40X"]
                        error_bucket= request.POST["eb40X"]
                        interval= request.POST["interval40X"]
                        log.logger.info('[alert40]threshold:{},total_bucket:{},error_bucket:{},interval:{}'.format(threshold,total_bucket,error_bucket,interval))
                        if level40xerror:
                            post_result = api.patch_levelerror(token,"40x",level40xerror.id,threshold,total_bucket,error_bucket,interval,True)
                        else:
                            post_result = api.post_levelerror(token,"40x",cid,threshold,total_bucket,error_bucket,False,interval,True)
                    elif int(alert40) == 0:
                        if level40xerror:
                            post_result = api.patch_levelerror(token,"40x",level40xerror.id,None,None,None,None,False)
                        
                    
                    if int(alert50) == 1:
                         threshold=request.POST["threshold50X"]
                         total_bucket= request.POST["tb50X"]
                         error_bucket= request.POST["eb50X"]
                         interval= request.POST["interval50X"]
                         log.logger.info('[alert50]threshold:{},total_bucket:{},error_bucket:{},interval:{}'.format(threshold,total_bucket,error_bucket,interval))

                         if level50xerror:
                             post_result = api.patch_levelerror(token,"50x",level50xerror.id,threshold,total_bucket,error_bucket,interval,True)
                         else:
                             post_result = api.post_levelerror(token,"50x",cid,threshold,total_bucket,error_bucket,False,interval,True)  
                    elif int(alert50) == 0:
                        if level50xerror:
                            post_result = api.patch_levelerror(token,"50x",level50xerror.id,None,None,None,None,False)
                            
                    
                    if int(alert20030X) == 1:
                         interval = request.POST["interval20030X"]
                         alerting_time = request.POST["at20030X"]
                         recovery_time = request.POST["rt20030X"]
                         bucket = request.POST["tb20030X"]
                         log.logger.info('[alert20030X]alerting_time:{},recovery_time:{},bucket:{},interval:{}'.format(alerting_time,recovery_time,bucket,interval))
                         if level20030xerror:
                            post_result = api.patch_levelnot20030x(token,level20030xerror.id,alerting_time,recovery_time,bucket,interval,True)
                         else:
                            post_result = api.post_levelnot20030x(token,cid,alerting_time,recovery_time,bucket,0,False,interval,True)
                    elif int(alert20030X) == 0:
                        if level20030xerror:
                            post_result = api.patch_levelnot20030x(token,level20030xerror.id,None,None,None,None,False)
                                
                    if post_result:
                        response_data['message'] = 'update success'
                        response_data['status_code'] = 200  
                    else:
                        response_data['message'] = 'update fail'
                        response_data['status_code'] = 400
                return HttpResponse( json.dumps(response_data), content_type="application/json")
    except Exception as e:
        message = "Exception : "+ str(e)
        error_class = e.__class__.__name__ #取得錯誤類型
        detail = e.args[0] #取得詳細內容
        cl, exc, tb = sys.exc_info() #取得Call Stack
        lastCallStack = traceback.extract_tb(tb)[-1] #取得Call Stack的最後一筆資料
        fileName = lastCallStack[0] #取得發生的檔案名稱
        lineNum = lastCallStack[1] #取得發生的行號
        funcName = lastCallStack[2] #取得發生的函數名稱
        errMsg = "File \"{}\", line {}, in {}: [{}] {}".format(fileName, lineNum, funcName, error_class, detail)
        log.logger.info('errMsg:'+errMsg)
        response_data['message'] = message        
        response_data['status_code'] = 408
        return HttpResponse( json.dumps(response_data), content_type="application/json")

def Alert_Deploy(request):
    try:
        response_data={}
        if request.method == 'GET':
            username = request.GET['username']
            token =  request.GET['token']
            hid =  int(request.GET['hid'])
            api =  lg_operation_api(operapihost)
            userpofile =  api.get_userprofile(token,username)
            leveldown_list = api.get_leveldownsbyhid(token,hid)
            levelrtt_list = api.get_levelrttsbyhid(token,hid)
            leveldown = None
            levelrtt = None
            if leveldown_list:
                leveldown = leveldown_list[0]
            if levelrtt_list:
                levelrtt = levelrtt_list[0]

            valuelist =list()
            for i in range(1,11):
                valuelist.append(i*10)
            context_dict ={'hid':hid,'leveldown':leveldown, 'levelrtt':levelrtt,
                            'statusalertvalues':valuelist,'statusrecovervalues':valuelist}
            return render_to_response('monitor/partial/alertdeploy.html',context_dict)
        
        if request.method == 'POST':
            username = request.POST['username']
            token =  request.POST['token']
            hid =  int(request.POST['hid'])
            api =  lg_operation_api(operapihost)
            userpofile =  api.get_userprofile(token,username)
            leveldown_list = api.get_leveldownsbyhid(token,hid)
            levelrtt_list = api.get_levelrttsbyhid(token,hid)
            configinstancelist = api.get_HTInstancebyconfig(token,hid)
            level_monitors = get_level_monitors(configinstancelist)
            cid = int(userpofile.customer_id)
            alertdown = request.POST["alertdown"]
            alertrtt = request.POST["alertrtt"]
            log.logger.info('level_monitors:{}'.format(level_monitors))


            ######### alert down ##########
            if int(alertdown) == 1:
                downbucket = request.POST["downbucket"]
                downalert =  int(request.POST["downalert"])/100
                downrecover = int(request.POST["downrecover"])/100
                if leveldown_list:
                    count = 0
                    if len(level_monitors) >= len(leveldown_list):
                        for level_down_monitor in level_monitors:
                            if count < len(leveldown_list):
                                level_down = leveldown_list[count]
                                post_result = api.patch_leveldown(token,level_down.id,downalert,downrecover,downbucket,level_down_monitor,True)
                            else:
                                post_result = api.post_leveldown(token,cid,hid,downalert,downrecover,downbucket,level_down_monitor,True)
                            count+=1
                    else:
                        for level_down in sorted(leveldown_list,key=lambda x: x.id):
                            if count < len(level_monitors):
                                level_down_monitor = level_monitors[count]
                                post_result = api.patch_leveldown(token,level_down.id,downalert,downrecover,downbucket,level_down_monitor,True)
                            else:
                                post_result = api.patch_leveldown(token,level_down.id,None,None,None,None,False)
                            count+=1
                else:
                    for level_down_monitor in level_monitors:
                        post_result = api.post_leveldown(token,cid,hid,downalert,downrecover,downbucket,level_down_monitor,True)
            elif int(alertdown) == 0:
                if leveldown_list:
                    for level_down in leveldown_list:
                        post_result = api.patch_leveldown(token,level_down.id,None,None,None,None,False)

            ######### alert rtt ##########
            if int(alertrtt) == 1:
                rttbucket = request.POST["rttbucket"]
                rttalert = int(request.POST["rttalert"])/100
                rttrecover = int(request.POST["rttrecover"])/100
                rttthreshold = request.POST["rttthreshold"]
                log.logger.info('level_monitors:{}'.format(level_monitors))

                if levelrtt_list:
                    count = 0
                    if len(level_monitors) >= len(levelrtt_list):
                        for level_rtt_monitor in  level_monitors:
                            if count < len(levelrtt_list):
                                level_rtt = levelrtt_list[count]
                                post_result = api.patch_levelrtt(token,level_rtt.id,rttalert,rttrecover,rttthreshold,rttbucket,level_rtt_monitor,True)
                            else:
                                post_result = api.post_levelrtt(token,cid,hid,rttalert,rttrecover,rttthreshold,rttbucket,level_rtt_monitor,True)
                            count+=1
                    else:
                        for level_rtt in sorted(levelrtt_list,key = id):
                            if count < len(level_monitors):
                                level_rtt_monitor = level_monitors[count]
                                log.logger.info('level_rtt_monitor:{}'.format(level_rtt_monitor))
                            else:
                                post_result = api.patch_levelrtt(token,level_rtt.id,None,None,None,None,None,True)
                            count+=1
                else:
                    for level_rtt_monitor in level_monitors:
                        post_result = api.post_levelrtt(token,cid,hid,rttalert,rttrecover,rttthreshold,rttbucket,level_rtt_monitor,True)
            elif int(alertrtt) == 0:
                if levelrtt_list:
                    for level_rtt in levelrtt_list:
                        post_result = api.patch_levelrtt(token,level_rtt.id,None,None,None,None,None,False)

            if post_result:
                response_data['message'] = 'update success'
                response_data['status_code'] = 200  
            else:
                response_data['message'] = 'update fail'
                response_data['status_code'] = 400
            return HttpResponse( json.dumps(response_data), content_type="application/json")

    except Exception as e:
        message =  "Exception : "+ str(e)
        response_data['message'] = message   
        response_data['status_code'] = 408
        return HttpResponse( json.dumps(response_data), content_type="application/json")

def Recipient_Vertify(request):
    try:
        response_data={}
        if request.method == 'POST':
            message_type = 'telegram'
            recipient_id =  request.POST['recipient_id']
            content = 'recipientid confirm message'
            messageapi = lg_message_api()
            response = messageapi.send_message(message_type,recipient_id,content)
            response_data['message'] = ""
            response_data['status_code'] = response.status_code
            return HttpResponse( json.dumps(response_data), content_type="application/json")
        else:
            response_data['message'] = "please use POST method"
            response_data['status_code'] = 400


    except Exception as e:
        message = "Exception : "+ str(e)
        log.logger.info('message:'+message)
        response_data['message'] = message   
        response_data['status_code'] = 408
        return HttpResponse( json.dumps(response_data), content_type="application/json")


#### function ### 
def get_config_list(token,customer_id):
    try:
        datalist =  list()
        api =  lg_operation_api(operapihost)
        configlist = api.get_HTConfigs(token,customer_id)

        protocollist = api.get_protocols(token)
        tmpconfiginstancelist = api.get_HTInstances(token)

        for config in configlist:
            #if config.enabled == True:
            protocol_name = next((protocol.name for protocol in protocollist if protocol.id == config.hb_protocol), None)
            configinstancelist = list([item for item in tmpconfiginstancelist if item.heartbeat == config.id])
            node,total,completed,fail,progress = parse_nodestatus(configinstancelist)
            summarystatus = 1
            if fail > 0 or progress >0:
                summarystatus = 0
            monitorsummary = Monitorsummary(config.id,
                                            config.hb_yml_name,
                                            protocol_name,
                                            config.schedule,
                                            summarystatus,
                                            total,
                                            config.created_by,
                                            config.created_time,
                                            config.updated_by,
                                            config.updated_time)
            datalist.append(monitorsummary)
        return datalist    
    except Exception as e:
        message =  "Exception : "+ str(e)
        log.logger.info(message)
   
def get_existed_url_count(configlist):
    count = 0
    for config in configlist:
        if config.url_heartbeat:
           for url in config.url_heartbeat:
               if url['enabled'] == True:
                   count = count +1
    return count

def get_interval_list(mininterval):
    maxinterval =  600
    intervallist = list()
    while mininterval <=600:
        intervallist.append(mininterval)
        mininterval = mininterval+60
    intervallist.append(900)
    intervallist.append(1200)
    return intervallist

def get_configdetail(token,config_id,enabled):
    api =  lg_operation_api(operapihost)
    config = api.get_HTConfig(token,config_id)
    configisntances = api.get_HTInstancebyconfig(token,config_id)
    urls = ','.join([url['full_url'] for url in sorted(config.url_heartbeat, key=lambda k: k.get('id', 0)) if url['enabled'] == True])
    details=''
    checkrequest=None
    checkreponse=None
    if enabled:
        urls = ','.join([url['full_url'] for url in sorted(config.url_heartbeat, key=lambda k: k.get('id', 0))  if url['enabled'] == True ])
    if config.detail_heartbeat:
        details =  ','.join([ detail['key']+":"+detail['value'] for detail in config.detail_heartbeat])
        checkrequest = next((detail['value'] for detail in config.detail_heartbeat if detail['key'] =='check.request'), None)
        checkreponse= next((detail['value'] for detail in config.detail_heartbeat if detail['key'] =='check.response'), None)
    nodes = ''
    node_ids=''
    for configinstance in configisntances:
        if configinstance.enabled == True:
            instance = api.get_instance(token,configinstance.instance)
            nodes = nodes +instance.ch_name+":"+get_status_name(configinstance.id,configinstance.status)+","
            node_ids = node_ids+str(instance.id)+","
    return JobInstanceDetail(urls,node_ids,nodes,checkrequest,checkreponse,details)

'''
def get_monitor_ur_summary():
    datalist = list()
    api = lg_operation_api(1)
    for item in api.get_HTConfJobByCID():
      config_id = item.config
      job = item.hosturls
      tmp_config = api.get_config(config_id)
      jobconfig = JobInstanceDetail(job,tmp_config['protocol_name'],1,tmp_config['interval'],None)
      jobconfig.node_status = api.get_HTConfinstanceByID(config_id)
      if jobconfig.node_status.failed > 0 or jobconfig.node_status.progress >0:
          jobconfig.status = 0
      datalist.append(jobconfig)
    return datalist
'''
def parse_nodestatus(data):
        total = 0 
        completed = 0
        fail = 0
        progress = 0
        node = ''
        for item in data:
            if item.enabled == True:
                status =  item.status
                instance_id = item.instance
                node = node + str(instance_id)+","
                total+=1
                if status == 1:
                    completed+=1
                if status ==2 or status == 3:
                    progress+=1
                if status == 4:
                    fail+=1 
        return node,total,completed,fail,progress

def generate_urls(existed_urls,jobs):
    tmp_joblist =  list([job.strip() for job in jobs.split(",")])
    existed_joblist = list(url["full_url"] for url in existed_urls)

    # delete part
    for url in existed_urls:
        if url["full_url"] in tmp_joblist:
            if url["enabled"] ==  False: # renew 
                url["enabled"] = True

        else: # delete
            url["enabled"] = False
         
    # new part
    for job in tmp_joblist:
        if job.strip() not in existed_joblist:
            log.logger.info('new url:'+job.strip())
            existed_urls.append({"id":0,"full_url":job.strip()})
    return existed_urls

def get_customer_monitor_list(token,customer_id):
    configinstancelist = list()
    api =  lg_operation_api(operapihost)
    configlist = api.get_HTConfigs(token,customer_id)
    if configlist:
        for config in configlist:
            configinstancelist.extend(api.get_HTInstancebyconfig(token,config.id))
    return configinstancelist

def get_customer_monitor_list_byinstanceid(token,customer_id,instance_id):
    configinstancelist = get_customer_monitor_list(token,customer_id)
    return list([ configinstance for configinstance in configinstancelist if configinstance.instance == instance_id])

def get_customer_monitor_nodes_id_list(token,customer_id):
    configinstancelist = get_customer_monitor_list(token,customer_id)
    if configinstancelist:
        return set(list([configinstance.instance for configinstance in configinstancelist if configinstance.enabled == True ]))
    else:
        return None

def get_status_name(configinstance_id,status_id):
    if status_id == 1:
        return 'ready'
    if status_id == 2:
        return 'pending'
    if status_id == 3:
        config_ins_id = str(configinstance_id)
        return "<span id ='deploystatus_"+config_ins_id+"'>deploying<a class='btn btn-default' onclick='deploy_refresh(\""+config_ins_id+"\")'><span class='fa fa-refresh'></span></a><span id='refresh_"+config_ins_id+"'></span></span>"

def alert_down_rtt_monitor_updatebyhid(token,username,action,hid):
    api =  lg_operation_api(operapihost)
    userpofile =  api.get_userprofile(token,username)
    levelrtt_list = list()
    leveldown_list = list()
    down_list = api.get_leveldownsbyhid(token,hid) 
    if down_list:
       leveldown_list = list(level for level in down_list if level.enabled == True)
    
    rtt_list = api.get_levelrttsbyhid(token,hid)
    if rtt_list:
       levelrtt_list = list(level for level in rtt_list if level.enabled == True)

    configinstancelist = api.get_HTInstancebyconfig(token,hid)
    level_monitors = get_level_monitors(configinstancelist)
    cid = int(userpofile.customer_id)
    if leveldown_list:
        if action == -1:
            for level_down in leveldown_list:
                post_result = api.patch_leveldown(token,level_down.id,None,None,None,None,False)
        else:
            count = 0
            if len(level_monitors) >= len(leveldown_list):
                for level_down_monitor in level_monitors:
                    if count < len(leveldown_list):
                        level_down = leveldown_list[count]
                        post_result = api.patch_leveldown(token,level_down.id,None,None,None,level_down_monitor,True)
                    else:
                        level = leveldown_list[-1]
                        post_result = api.post_leveldown(token,cid,hid,level.down_percentage_alert,level.down_percentage_recovery,
                                                        level.bucket,level_down_monitor,True)
                    count+=1
            else:
                for level_down in sorted(leveldown_list,key = id):
                    if count < len(level_monitors):
                        level_down_monitor = level_monitors[count]
                        post_result = api.patch_leveldown(token,level_down.id,None,None,None,level_down_monitor,True)
                    else:
                        post_result = api.patch_leveldown(token,level_down.id,None,None,None,None,False)
                    count+=1
    if levelrtt_list:
        if action == -1:
            for level_rtt in levelrtt_list:
                post_result = api.patch_levelrtt(token,level_rtt.id,None,None,None,None,None,True)
        else:
            count = 0
            if len(level_monitors) >= len(levelrtt_list):
                for level_rtt_monitor in  level_monitors:
                    if count < len(levelrtt_list):
                        level_rtt = levelrtt_list[count]
                        post_result = api.patch_levelrtt(token,level_rtt.id,None,None,None,None,level_rtt_monitor,True)
                    else:
                        level = levelrtt_list[-1]
                        post_result = api.post_levelrtt(token,cid,hid,level.rtt_percentage_alert,level.rtt_percentage_recovery,
                                                        level.rtt_threshold,level.bucket,level_rtt_monitor,True)
                    count+=1
            else:
                for level_rtt in sorted(levelrtt_list,key = id):
                    if count < len(level_monitors):
                        level_rtt_monitor = level_monitors[count]
                        post_result = api.patch_levelrtt(token,level_rtt.id,None,None,None,None,level_rtt_monitor,True)
                    else:
                        post_result = api.patch_levelrtt(token,level_rtt.id,None,None,None,None,None,True)
                    count+=1

def get_level_monitors(datalist):
    level_monitor_list = list()
    generate_list = list()
    level_monitors =''
    instancelist = sorted(list(data.instance for data in datalist if data.enabled == True))

    for instance in instancelist:
        if len(generate_list) == 5:
            level_monitors = ','.join(generate_list)
            level_monitor_list.append(level_monitors)
            level_monitors=''
            generate_list=list()
            generate_list.append(str(instance))
        else:
            generate_list.append(str(instance))
    level_monitors =''
    if len(generate_list)>0:
        level_monitors = ','.join(generate_list)
        level_monitor_list.append(level_monitors)
    return level_monitor_list




import random
import string
class HTConfigOperation(object):
    def __init__(self,operapihost,token,username):
         self.api =  lg_operation_api(operapihost)
         self.token = token
         self.userpofile =  self.api.get_userprofile(token,username)
         self.protocol = None
         self.existed_config_list = None
         self.new_config_list =list()
         self.delete_config_list =list()



    def New_Config(self,nodes,customer_id,protocol_id,hb_tag,interval,wsorigin,jobs,checkrequest,checkresponse):
        try:
            self.__set_protocol(protocol_id)

            self.__set_existed_config(customer_id)

            hb_yml_name =  self.__get_yml_file_name()
            

            enabled = True
            user_name =  self.userpofile.user_name

            log.logger.info('hb_yml_name:'+hb_yml_name)


            ##### instance id list ###
            instance_id_list =list([ int(node) for node in nodes.split(';')])

            #### heartbeat urls ####
            urls = list( {'full_url':job.strip()} for job in jobs.split(",") if job)

            #### heartbeat details ####
            details = list()
            if checkrequest:
                value = {'key':'check.request','value':checkrequest}
                details.append(value)
            if checkresponse:
                value = {'key':'check.response','value':checkresponse}
                details.append(value)

            config =  self.api.post_HTConfig(self.token,
                                        customer_id,
                                        protocol_id,
                                        hb_tag,
                                        hb_yml_name,
                                        interval,
                                        wsorigin,
                                        enabled,
                                        user_name,
                                        user_name,
                                        urls,
                                        details)
            if config:
                status_id = 2
                config_id =  config.id
                savelist = list()
                for instance_id in instance_id_list:
                    configinstances = self.api.post_HTConfigInstance(self.token,
                                                                config_id,
                                                                instance_id,
                                                                status_id,
                                                                enabled)
                    self.new_config_list.append(configinstances)
                                
                if len(instance_id_list) == len(self.new_config_list):
                    return config
                else:
                    return None
            else:
                return None
        except Exception as e:
            message = "Exception : "+ str(e)
            log.logger.info('message:'+message)
            error_class = e.__class__.__name__ #取得錯誤類型
            detail = e.args[0] #取得詳細內容
            cl, exc, tb = sys.exc_info() #取得Call Stack
            lastCallStack = traceback.extract_tb(tb)[-1] #取得Call Stack的最後一筆資料
            fileName = lastCallStack[0] #取得發生的檔案名稱
            lineNum = lastCallStack[1] #取得發生的行號
            funcName = lastCallStack[2] #取得發生的函數名稱
            errMsg = "File \"{}\", line {}, in {}: [{}] {}".format(fileName, lineNum, funcName, error_class, detail)
            log.logger.info('errMsg:'+errMsg)
            return None


    def Edit_Config(self,nodes,config_id,jobs,interval,wsorigin,checkrequest,checkreponse):
        try:
            username =  self.userpofile.user_name
            tmp_config = self.api.get_HTConfig(self.token,config_id)

            #### existed url list ####
            tmp_urls = self.__generate_urls(tmp_config.url_heartbeat,jobs)
            
            #### existed detail list ####
            tmp_details = list()
            requestflag = False
            reponseflag =False
            if tmp_config.detail_heartbeat:
                tmp_details = tmp_config.detail_heartbeat
                for detail in tmp_details:
                    if checkrequest:
                        if detail['key'] == 'check.request':
                            detail['value'] = checkrequest
                            detail['enabled'] =True
                            requestflag = True
                    else:
                        if detail['key'] == 'check.request':
                           detail['value'] = ""
                           detail['enabled']=False

                    if checkreponse:
                        if detail['key'] == 'check.response':
                            detail['value'] = checkreponse
                            detail['enabled'] =True
                            reponseflag = True
                    else:
                        if detail['key'] == 'check.response':
                            detail['value'] = ""
                            detail['enabled']=False

            if checkrequest:
                if requestflag == False:
                    value = {'key':'check.request','value':checkrequest}
                    tmp_details.append(value)
                    requestflag= True
            if checkreponse:
                if reponseflag == False:
                    value = {'key':'check.response','value':checkresponse}
                    tmp_details.append(value)
                    reponseflag = True

            
            log.logger.info('[Edit_Config]tmp_details:{}'.format(tmp_details))

            
            config = self.api.patch_HTConfig(self.token,
                                        config_id,
                                        None,
                                        interval,
                                        wsorigin,
                                        True,
                                        username,
                                        tmp_urls,
                                        tmp_details)
            if config:
                datalist = self.api.get_HTInstancebyconfig(self.token,config_id)
                all_id_list = list([item.instance for item in datalist])
                origin_id_list = set([item.instance for item in datalist if item.enabled == True])
                instance_id_list =set(list([ int(node) for node in nodes.split(';')]))
                existed_list = list(origin_id_list.intersection(instance_id_list))
                del_list = list(origin_id_list.difference(existed_list))
                new_list = list(instance_id_list.difference(existed_list))


                log.logger.info('existed list :{}'.format(existed_list))
                log.logger.info('deleted list :{}'.format(del_list))
                log.logger.info('new list :{}'.format(new_list))


                # delete
                if del_list:
                    for delid in del_list:
                        tmpconfignode = next((node for node in datalist if node.instance == delid),None)
                        if tmpconfignode:
                            status_id = 2
                            #status_id=1
                            enabled = False
                            configinstances = self.api.patch_HTConfigInstance(self.token,
                                                                         tmpconfignode.id,
                                                                         status_id,
                                                                         enabled)
                            self.delete_config_list.append(configinstances)
                # new                                                   
                if new_list:
                    status_id = 2
                    #status_id = 1
                    enabled = True
                    for newid in new_list:
                        if newid in all_id_list: # existed to renew 
                            tmpconfignode = next((node for node in datalist if node.instance == newid),None)
                            if tmpconfignode:
                                tmpconfignode.status = 2
                                configinstances = self.api.patch_HTConfigInstance(self.token,
                                                                            tmpconfignode.id,
                                                                            tmpconfignode.status,
                                                                            None)
                                self.new_config_list.append(configinstances)

                        else: # not existed to add 
                            configinstances =self.api.post_HTConfigInstance(self.token,
                                                                            config_id,
                                                                            newid,
                                                                            status_id,
                                                                            enabled)
                            self.new_config_list.append(configinstances)
               
                # update
                if existed_list:
                    for existed_id in existed_list:
                        tmpconfignode = next((node for node in datalist if node.instance == existed_id),None)
                        if tmpconfignode:
                            tmpconfignode.status =2
                            configinstances =self.api.patch_HTConfigInstance(self.token,
                                                                        tmpconfignode.id,
                                                                        tmpconfignode.status,
                                                                        None)
                            self.new_config_list.append(configinstances)

                log.logger.info('new :{}'.format(len(self.new_config_list)))
                log.logger.info('deleted :{}'.format(len(self.delete_config_list)))

                if len(instance_id_list) == len(self.new_config_list):
                    return config
                else:
                    return None
            else:
                return None
        except Exception as e:
            message = "[Edit_config]Exception : "+ str(e)
            log.logger.info('message:'+message)
            error_class = e.__class__.__name__ #取得錯誤類型
            detail = e.args[0] #取得詳細內容
            cl, exc, tb = sys.exc_info() #取得Call Stack
            lastCallStack = traceback.extract_tb(tb)[-1] #取得Call Stack的最後一筆資料
            fileName = lastCallStack[0] #取得發生的檔案名稱
            lineNum = lastCallStack[1] #取得發生的行號
            funcName = lastCallStack[2] #取得發生的函數名稱
            errMsg = "File \"{}\", line {}, in {}: [{}] {}".format(fileName, lineNum, funcName, error_class, detail)
            log.logger.info('errMsg:'+errMsg)
            return None


    def Delete_config(self,config_id):
        try:
            enabled = False
            savelist = list()
            username =  self.userpofile.user_name
            tmp_config = self.api.get_HTConfig(self.token,config_id)
            for url in tmp_config.url_heartbeat:
                url['enabled'] = True
            for detail in tmp_config.detail_heartbeat:
                detail['enabled'] = True
            config = self.api.patch_HTConfig(self.token,
                                        config_id,
                                        None,
                                        None,
                                        None,
                                        enabled,
                                        username,
                                        tmp_config.url_heartbeat,
                                        tmp_config.detail_heartbeat)
            if config:
                datalist = self.api.get_HTInstancebyconfig(self.token,config_id)
                if datalist and len(datalist)>0:
                    existeddatalist = list([item for item in datalist if item.enabled ==  True])
                    for data in existeddatalist:
                        status = 2
                        enabled = False
                        log.logger.info('data.id:'+str(data.id))
                        config_instance = self.api.patch_HTConfigInstance(self.token,
                                                                        data.id,
                                                                        status,
                                                                        enabled)
                        self.delete_config_list.append(config_instance)
                    if len(existeddatalist) == len(self.delete_config_list):
                        return config
                    else:
                        return None
                else:
                    return None
            else:
                return None
            
        except Exception as e:
            return None
        
    
    def __set_protocol(self,protocol_id):
        self.protocol = self.api.get_protocol(self.token,protocol_id)

    def __set_existed_config(self,customer_id):
        self.existed_config_list = self.api.get_HTConfigs(self.token,customer_id)

            
    def __get_yml_file_name(self):
        count = self.__get_existed_protocol_count()
        filecount = 10+count
        if self.existed_config_list:
            existedymlfilelist =  list([ config.hb_yml_name for config in self.existed_config_list])
            while count<filecount:
                if count == 1:
                    if self.protocol.name == "websocket":
                        hb_yml_name = "{}_ws_check.yml".format(self.userpofile.customer_name)
                    elif self.protocol.name == "http":
                        hb_yml_name = "{}_web_check.yml".format(self.userpofile.customer_name)
                    else:
                        hb_yml_name = "{}_{}_check.yml".format(self.userpofile.customer_name,self.protocol.name)
                else:
                    if self.protocol.name == "websocket":
                        hb_yml_name = "{}_ws_check_{}.yml".format(self.userpofile.customer_name,count)
                    elif self.protocol.name == "http":
                        hb_yml_name = "{}_web_check_{}.yml".format(self.userpofile.customer_name,count)
                    else:
                        hb_yml_name = "{}_{}_check_{}.yml".format(self.userpofile.customer_name,self.protocol.name,count)
                if hb_yml_name not in existedymlfilelist:
                    return hb_yml_name
                count +=1
        else:
            if count == 1:
                if self.protocol.name == "websocket":
                    return "{}_ws_check.yml".format( self.userpofile.customer_name,count)
                elif self.protocol.name == "http":
                    return "{}_web_check.yml".format( self.userpofile.customer_name,count)
                else:
                    return "{}_{}_check_{}.yml".format( self.userpofile.customer_name,self.protocol.name,count)
            else:
                if self.protocol.name == "websocket":
                    return "{}_ws_check_{}.yml".format( self.userpofile.customer_name,count)
                if self.protocol.name == "http":
                    return "{}_web_check_{}.yml".format( self.userpofile.customer_name,count)
                else:
                    return "{}_{}_check_{}.yml".format( self.userpofile.customer_name,self.protocol.name,count)

        serial_number = self.__random_generator()
        hb_yml_name = "{}_{}_{}.yml".format(customer_name,protocol_name,serial_number)
        return hb_yml_name


    def __get_existed_protocol_count(self):
        count = 1
        if self.existed_config_list:
            for config in  self.existed_config_list:
                if config.hb_protocol == int(self.protocol.id):
                    count = count +1
        return count
    
    def __random_generator(self,size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for x in range(size))

    def __generate_urls(self,existed_urls,jobs):
        tmp_joblist =  list([job.strip() for job in jobs.split(",") if job.strip()])
        existed_joblist = list(url["full_url"] for url in existed_urls)

        # delete part
        for url in existed_urls:
            if url["full_url"] in tmp_joblist:
                if url["enabled"] ==  False: # renew 
                    url["enabled"] = True

            else: # delete
                if url["enabled"] == True:
                    url["enabled"] = False
        
        for existeditem in existed_joblist:
            log.logger.info('existeditem:{}'.format(existeditem.strip()))    
        
        # new part
        for job in tmp_joblist:
            if job.strip() not in existed_joblist:
                log.logger.info('new url:'+job.strip())
                existed_urls.append({"id":0,"full_url":job.strip()})

        return existed_urls
