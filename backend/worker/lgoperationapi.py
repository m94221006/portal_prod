# -*- coding: UTF-8 -*-

import os
import sys
import timeit
import datetime
import shlex
import json
import io
import requests
import json
from http_parser.util import b
from mlog import Log
import sys, traceback
log = Log("lgoperationapi","lookglasslog")

##### heartbeat config object #####
class UserProfile(object):
    def __init__(self,id,uid,u_name,cid,c_name,credential):
        self.id =  id
        self.user_id = uid
        self.user_name =u_name
        self.customer_id = cid
        self.customer_name = c_name
        self.credential =credential    

class CustomerInfo(object):
    def __init__(self,id,name,enabled,max_url_num,max_monitor_num,min_interval_num,instance):
        self.id = id
        self.name =name
        self.enabled = enabled
        self.max_url_num = max_url_num
        self.max_monitor_num =max_monitor_num  
        self.min_interval_num =min_interval_num 
        self.instance = instance

class CustomerContact(object):
    def __init__(self,id,cid,recipient_id,type_id,subject):
        self.id = id
        self.cid =cid
        self.recipient_id = recipient_id
        self.type_id = type_id
        self.subject =subject  


class Instance(object):
    def __init__(self,id,nid,host_name,region_name,isp_name,ch_name,host_ip,status_name):
        self.id = id
        self.nid = nid
        self.host_name = host_name
        self.region_name = region_name
        self.isp_name = isp_name
        self.ch_name =ch_name
        self.host_ip = host_ip
        self.status_name = status_name

class Region(object):
      def __init__(self,id,en_name,ch_name):
        self.id = id
        self.en_name = en_name
        self.ch_name = ch_name

class Isp(object):
      def __init__(self,id,name,deleted):
        self.id = id
        self.name = name
        self.deleted = deleted


class Protocol(object):
    def __init__(self,id,name):
        self.id = id
        self.name = name

class HTConfig(object):
    def __init__(self,configid,cid,hb_protocol,hb_tag,hb_yml_name,schedule,origin,enabled,created_by,created_time,updated_by,updated_time,url_heartbeat,detail_heartbeat):
        self.id = configid
        self.cid = cid
        self.hb_protocol =hb_protocol
        self.hb_tag =hb_tag
        self.hb_yml_name =hb_yml_name
        self.schedule = schedule
        self.origin = origin
        self.enabled = enabled
        self.created_by = created_by
        self.created_time = created_time
        self.updated_by = updated_by
        self.updated_time = updated_time
        self.url_heartbeat = url_heartbeat
        self.detail_heartbeat = detail_heartbeat

class HTConfigInstance(object):
    def __init__(self,id,heartbeat,instance,enabled,status):
     self.id = id
     self.heartbeat = heartbeat
     self.instance=instance
     self.status = status
     self.enabled= enabled


##### custom class ######
class Monitorsummary(object):
    def __init__(self,config_id,file_name,protocol_name,interval,status,total,creator,created_time,lastupdatedby,lastupdatedtime):
        self.config_id =  config_id
        self.file_name = file_name
        self.protocol_name =protocol_name
        self.interval =  interval
        self.status =status
        self.total = total
        self.creator = creator
        self.created_time = created_time
        self.lastupdatedby = lastupdatedby
        self.lastupdatedtime = lastupdatedtime


class node_status(object):
    def __init__(self,node,total_count,completed_count,failed_count,progress_count):
        self.node = node
        self.total = total_count
        self.completed = completed_count
        self.failed = failed_count
        self.progress =progress_count

class JobInstanceDetail(object):
    def __init__(self,urls,node_ids,nodes,checkrequest,checkresponse,others):
        self.urls= urls
        self.nodes=nodes
        self.node_ids = node_ids
        self.checkrequest = checkrequest
        self.checkresponse = checkresponse
        self.others =others


#### alert object####
class notifytype(object):
    def __init__(self,id,name):
        self.id= id
        self.name=name

class levelerror(object):
    def __init__(self,id,cid,threshold,total_bucket,error_bucket,alerting,interval,enabled):
        self.id= id
        self.cid=cid
        self.threshold = threshold
        self.total_bucket = total_bucket
        self.error_bucket = error_bucket
        self.alerting =alerting
        self.interval = interval
        self.enabled =  enabled

class levelnot20030x(object):
    def __init__(self,id,cid,alerting_time,recovery_time,bucket,alerting,interval,enabled,history_avg):
        self.id= id
        self.cid=cid
        self.alerting_time = alerting_time
        self.recovery_time = recovery_time
        self.bucket = bucket
        self.alerting =alerting
        self.interval = interval
        self.enabled =  enabled
        self.history_avg = history_avg

class leveldown(object):
    def __init__(self,id,cid,hid,down_percentage_alert,down_percentage_recovery,bucket,enabled,level_down_monitors):
        self.id= id
        self.cid=cid
        self.hid = hid
        self.down_percentage_alert = down_percentage_alert
        self.down_percentage_recovery = down_percentage_recovery
        self.bucket =bucket
        self.enabled = enabled
        self.level_down_monitors =  level_down_monitors

class levelrtt(object):
    def __init__(self,id,cid,hid,rtt_percentage_alert,rtt_percentage_recovery,rtt_threshold,bucket,enabled,level_rtt_monitors):
        self.id= id
        self.cid=cid
        self.hid = hid
        self.rtt_percentage_alert = rtt_percentage_alert
        self.rtt_percentage_recovery = rtt_percentage_recovery
        self.rtt_threshold = rtt_threshold
        self.bucket =bucket
        self.enabled = enabled
        self.level_rtt_monitors =  level_rtt_monitors


class lg_operation_api(object):
    def __init__(self,hostip):
        #self.apihost = "http://192.168.1.135:8080/api"
        self.apihost ="http://{}:8080/".format(hostip)


    ########## get user and customer ##########
    def get_jwt_token(self,username,password):
        apihost = '{}api-token-auth/'.format(self.apihost)
        data = {"username": username, "password": password}
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        res = requests.post(apihost, data=data, headers=header)
        data = res.json()
        if data and 'token' in data:
            token = res.json()['token']
            return token
        else:
            return None

    def get_userprofile(self,token,username):
        try:
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/userprofile".format(self.apihost)
            res = requests.get(get_url, headers=header, timeout=20)
            data =  res.json()
            for item in data:
                if item['user_name']== username:
                    return UserProfile(item["id"] ,
                                       item["user"] ,
                                       item["user_name"], 
                                       item["customer"],
                                       item["customer_name"], 
                                       item["credential"])
            return None
        except Exception as e:
            message =  "(get_userprofile) Exception : "+ str(e)
            print(message)
            return None
    
    def get_customerinfo(self,token,cid):
        try:
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/customer/{}".format(self.apihost,cid)
            res = requests.get(get_url, headers=header, timeout=20)
            data =  res.json()
            if data :
                customerinfo = CustomerInfo(data["id"],data["name"],data["enabled"],data["max_url_num"],data["max_monitor_num"],data["min_interval_num"],data["instance"])
                return customerinfo
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            return None

    def get_customercontact(self,token,cid):
        try:
            datalist =  list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/customer-contact".format(self.apihost)
            res = requests.get(get_url, headers=header, timeout=20)
            data =  res.json()
            if data :
                for item in data:
                    customercontact = CustomerContact(item["id"],
                                                      item["cid"],
                                                      item["recipient_id"],
                                                      item["type_id"],
                                                      item["subject"])
                    datalist.append(customercontact)
                if cid:
                    datalist = list([item for item in datalist if cid == item.cid])
                return datalist
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            return None

    def get_customercontactbynotify(self,token,cid,type_id):
        try:
            datalist =  list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/customer-contact".format(self.apihost)
            res = requests.get(get_url, headers=header, timeout=20)
            data =  res.json()
            if data :
                for item in data:
                    if item["cid"] == cid and item["type_id"] == type_id:
                        return CustomerContact(item["id"],
                                               item["cid"],
                                               item["recipient_id"],
                                               item["type_id"],
                                               item["subject"])
                return None
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            return None

    ########## get instance and htconfig ##########
    def get_All_instances(self,token,instances_id):
        try:
            datalist = list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/instance/get_all_instances/".format(self.apihost)
            res = requests.get(get_url, headers=header, timeout=20)
            data =  res.json()
            if data:
                for item in data:
                    #log.logger.info("[get all instances]{} {}".format(item['id'],item['host_name'])) 
                    datalist.append(Instance(item['id'],item['nid'],item['host_name'],item['region_name'],item['isp_name'],item['ch_name'],item['host_ip'],item['status_name']))
                if instances_id:
                    datalist = [item for item in datalist if item.id in instances_id]
                #for item in datalist:
                    #log.logger.info("[get all instances]{} {}".format(item.id,item.host_name))
                return datalist
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            print(message)
            return None

    def get_instances(self,token,instances_id):
        try:
            datalist = list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/instance".format(self.apihost)
            res = requests.get(get_url, headers=header, timeout=20)
            data =  res.json()
            if data:
                for item in data:
                    datalist.append(Instance(item['id'],item['nid'],item['host_name'],item['region_name'],item['isp_name'],item['ch_name'],item['host_ip'],item['status_name']))
                if instances_id:
                    datalist = [item for item in datalist if item.id in instances_id]
                return datalist
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            print(message)
            return None

    def get_instance(self,token,instance_id):
        try:
            datalist = list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/instance/{}".format(self.apihost,instance_id)
            res = requests.get(get_url, headers=header, timeout=20)
            data =  res.json()

            if data:
                return Instance(data['id'],data['nid'],data['host_name'],data['region_name'],data['isp_name'],data['ch_name'],data['host_ip'],data['status_name'])
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            print(message)
            return None

    def get_regions(self,token):
        try:
            datalist = list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/region".format(self.apihost)
            res = requests.get(get_url, headers=header, timeout=20)
            data =  res.json()
            if data:
                for item in data:
                    datalist.append(Region(item['id'],
                                           item['en_name'],
                                           item['ch_name']))
                return datalist
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            print(message)
            return None

    def get_region(self,token,region_id):
        try:
            datalist = list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/region/{}".format(self.apihost,region_id)
            res = requests.get(get_url, headers=header, timeout=20)
            item =  res.json()
            if item:
                return Region(item['id'],
                              item['en_name'],
                              item['ch_name'])            
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            print(message)
            return None
    
    def get_isps(self,token):
        try:
            datalist = list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/isp".format(self.apihost)
            res = requests.get(get_url, headers=header, timeout=20)
            data =  res.json()
            if data:
                for item in data:
                    datalist.append(Isp(item['id'],
                                           item['name'],
                                           item['deleted']))
                return datalist
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            print(message)
            return None

    def get_isp(self,token,isp_id):
        try:
            datalist = list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/region/{}".format(self.apihost,isp_id)
            res = requests.get(get_url, headers=header, timeout=20)
            item =  res.json()
            if item:
                return Isp(item['id'],
                              item['name'],
                              item['deleted'])            
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            print(message)
            return None

    def get_protocols(self,token):
        try:
            datalist = list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/protocol".format(self.apihost)
            res = requests.get(get_url, headers=header, timeout=20)
            data =  res.json()
            if data:
                for item in data:
                    datalist.append(Protocol(item["id"],item["name"]))
                return datalist
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            return None

    def get_protocol(self,token,protocol_id):
        try:
            datalist = list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/protocol/{}/".format(self.apihost,protocol_id)
            res = requests.get(get_url, headers=header, timeout=20)
            item =  res.json()
            if item:
                return Protocol(item["id"],item["name"])
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            return None
    
    def get_HTConfigs(self,token,customer_id):
        try:
            datalist =  list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/heartbeat".format(self.apihost)
            res = requests.get(get_url, headers=header, timeout=20)
            data =  res.json()
            if data:
                for item in data:
                    config =  HTConfig(item['id'],
                                       item['cid'],
                                       item['hb_protocol'],
                                       item['hb_tag'],
                                       item['hb_yml_name'],
                                       item['schedule'],
                                       item['origin'],
                                       item['enabled'],
                                       item['created_by'],
                                       item['created_time'],
                                       item['updated_by'],
                                       item['updated_time'],
                                       item['url_heartbeat'],
                                       item['detail_heartbeat'])
                    datalist.append(config)
                if customer_id :
                    datalist = [item for item in datalist if item.cid == customer_id]
                return datalist
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            print(message)
            return None

    def get_HTConfig(self,token,config_id):
        try:
            datalist =  list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/heartbeat/{}".format(self.apihost,config_id)
            res = requests.get(get_url, headers=header, timeout=20)
            item =  res.json()
            if item:
                config =  HTConfig(item['id'],
                                   item['cid'],
                                   item['hb_protocol'],
                                   item['hb_tag'],
                                   item['hb_yml_name'],
                                   item['schedule'],
                                   item['origin'],
                                   item['enabled'],
                                   item['created_by'],
                                   item['created_time'],
                                   item['updated_by'],
                                   item['updated_time'],
                                   item['url_heartbeat'],
                                   item['detail_heartbeat'])
                return config
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            return None

    def get_HTInstances(self,token):
        try:
            datalist =  list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/heartbeat-instance".format(self.apihost)
            res = requests.get(get_url, headers =header , timeout=20)
            data =  res.json()
            if data:
                for item in data:
                    config = HTConfigInstance(item['id'],
                                              item['heartbeat'],
                                              item['instance'],
                                              item['enabled'],
                                              item['status'])
                    datalist.append(config)
                return datalist
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            print(message)
            return None

    def get_HTInstance(self,token,config_instance_id):
        try:
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/heartbeat-instance/{}".format(self.apihost,config_instance_id)
            res = requests.get(get_url, headers =header , timeout=20)
            item =  res.json()
            if item:
                config = HTConfigInstance(item['id'],
                                          item['heartbeat'],
                                          item['instance'],
                                          item['enabled'],
                                          item['status'])
                return config
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            return None

    def get_HTInstancebyconfig(self,token,config_id):
        try:
            datalist =  list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/heartbeat-instance".format(self.apihost)
            res = requests.get(get_url, headers =header , timeout=20)
            data =  res.json()
            if data:
                for item in data:
                    if item['heartbeat'] == config_id:
                        config = HTConfigInstance(item['id'],
                                                  item['heartbeat'],
                                                  item['instance'],
                                                  item['enabled'],
                                                  item['status'])
                        datalist.append(config)
                return datalist
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            print(message)
            return None
    
    
    ##########  get alert ##########
    def get_notifytypes(self,token):
        try:
            datalist = list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/alert/notify-type".format(self.apihost)
            res = requests.get(get_url, headers=header, timeout=20)
            data =  res.json()
            if data:
                for item in data:
                    datalist.append(notifytype(item["id"],item["name"]))
                return datalist
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            return None

    def get_notifytypebyname(self,token,notify_name):
        try:
            datalist = list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/alert/notify-type".format(self.apihost)
            res = requests.get(get_url, headers=header, timeout=20)
            data =  res.json()
            if data:
                for item in data:
                    if item["name"] == notify_name:
                        return notifytype(item["id"],item["name"])
                return none
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            return None

    def get_notifytype(self,token,notify_id):
        try:
            datalist = list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/alert/notify-type/{}/".format(self.apihost,notify_id)
            res = requests.get(get_url, headers=header, timeout=20)
            item =  res.json()
            if item:
                return notifytype(item["id"],item["name"])
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            return None

    def get_levelerrors(self,token,status_type):
        try:
            datalist =  list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/alert/{}".format(self.apihost,status_type)
            res = requests.get(get_url, headers =header , timeout=20)
            data =  res.json()
            if data:
                for item in data:
                    level = levelerror(item['id'],
                                       item['cid'],
                                       item['threshold'],
                                       item['total_bucket'],
                                       item['error_bucket'],
                                       item['alerting'],
                                       item['interval'],
                                       item['enabled'])
                    datalist.append(level)
                return datalist
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            print(message)
            return None

    def get_levelerrorbycid(self,token,cid,status_type):
        try:
            datalist =  list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/alert/{}".format(self.apihost,status_type)
            res = requests.get(get_url, headers =header , timeout=20)
            data =  res.json()
            if data:
                for item in data:
                    if cid == item["cid"]:
                       level = levelerror(item['id'],
                                          item['cid'],
                                          item['threshold'],
                                          item['total_bucket'],
                                          item['error_bucket'],
                                          item['alerting'],
                                          item['interval'],
                                          item['enabled'])
                       return level
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            log.logger.info(message)
            return None

    def get_levelnot20030x(self,token):
        try:
            datalist =  list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/alert/not20030x".format(self.apihost)
            res = requests.get(get_url, headers =header , timeout=20)
            data =  res.json()
            if data:
                for item in data:
                    level = levelnot20030x(item['id'],
                                            item['cid'],
                                            item['alerting_time'],
                                            item['recovery_time'],
                                            item['bucket'],
                                            item['alerting'],
                                            item['interval'],
                                            item['enabled'],
                                            item['history_avg'])
                    datalist.append(level) 
                return datalist
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            print(message)
            return None
    
    def get_levelnot20030xbycid(self,token,cid):
        try:
            datalist =  list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/alert/not20030x".format(self.apihost)
            res = requests.get(get_url, headers =header , timeout=20)
            data =  res.json()
            if data:
                for item in data:
                    if cid == item["cid"]:
                        level = levelnot20030x(item['id'],
                                               item['cid'],
                                               item['alerting_time'],
                                               item['recovery_time'],
                                               item['bucket'],
                                               item['alerting'],
                                               item['interval'],
                                               item['enabled'],
                                               item['history_avg'])
                        return level
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            print(message)
            return None

    def get_leveldownsbyhid(self,token,hid):
        try:
            datalist =  list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/alert/level-down".format(self.apihost)
            res = requests.get(get_url, headers =header , timeout=20)
            data =  res.json()
            if data:
                for item in data:
                    if item['hid'] == hid:
                        level = leveldown(item['id'],
                                            item['cid'],
                                            item['hid'],
                                            item['down_percentage_alert'],
                                            item['down_percentage_recovery'],
                                            item['bucket'],
                                            item['enabled'],
                                            item['level_down_monitors'])
                        datalist.append(level)
                return datalist
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            print(message)
            return None

    def get_leveldownsbycid(self,token,cid):
        try:
            datalist =  list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/alert/level-down".format(self.apihost)
            res = requests.get(get_url, headers =header , timeout=20)
            data =  res.json()
            if data:
                for item in data:
                    if item['cid'] == cid:
                        level = leveldown(item['id'],
                                            item['cid'],
                                            item['hid'],
                                            item['down_percentage_alert'],
                                            item['down_percentage_recovery'],
                                            item['bucket'],
                                            item['enabled'],
                                            item['level_down_monitors'])
                        datalist.append(level)
                return datalist
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            print(message)
            return None
    
    def get_leveldowns(self,token,cid):
        try:
            datalist =  list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/alert/level-down".format(self.apihost)
            res = requests.get(get_url, headers =header , timeout=20)
            data =  res.json()
            if data:
                for item in data:
                    if int(item['cid']) == cid:
                        level = leveldown(item['id'],
                                        item['cid'],
                                        item['hid'],
                                        item['down_percentage_alert'],
                                        item['down_percentage_recovery'],
                                        item['enabled'],
                                        item['level_down_monitors'])
                        datalist.append(level)
                return datalist
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            print(message)
            return None

    def get_levelrttsbyhid(self,token,hid):
        try:
            datalist =  list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/alert/level-rtt".format(self.apihost)
            res = requests.get(get_url, headers =header , timeout=20)
            log.logger.info(res)
            data =  res.json()
            log.logger.info(data)

            if data:
                for item in data:
                    if item['hid'] == hid:
                        level =  levelrtt(item['id'],
                                            item['cid'],
                                            item['hid'],
                                            item['rtt_percentage_alert'],
                                            item['rtt_percentage_recovery'],
                                            item['rtt_threshold'],
                                            item['bucket'],
                                            item['enabled'],
                                            item['level_rtt_monitors'])
                        datalist.append(level)
                return datalist
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            print(message)
            return None
            
    def get_levelrttsbycid(self,token,cid):
        try:
            datalist =  list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/alert/level-rtt".format(self.apihost)
            res = requests.get(get_url, headers =header , timeout=20)
            log.logger.info(res)
            data =  res.json()
            log.logger.info(data)

            if data:
                for item in data:
                    if item['cid'] == cid:
                        level =  levelrtt(item['id'],
                                            item['cid'],
                                            item['hid'],
                                            item['rtt_percentage_alert'],
                                            item['rtt_percentage_recovery'],
                                            item['rtt_threshold'],
                                            item['bucket'],
                                            item['enabled'],
                                            item['level_rtt_monitors'])
                        datalist.append(level)
                return datalist
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            print(message)
            return None
    
    def get_levelrtts(self,token,cid):
        try:
            datalist =  list()
            header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
            get_url = "{}api/alert/level-rtt".format(self.apihost)
            res = requests.get(get_url, headers =header , timeout=20)
            data =  res.json()
            if data:
                for item in data:
                    if int(item['cid']) == cid:
                        level = levelrtt(item['id'],
                                         item['cid'],
                                         item['hid'],
                                         item['rtt_percentage_alert'],
                                         item['rtt_percentage_recovery'],
                                         item['rtt_threshold'],
                                         item['bucket'],
                                         item['enabled'],
                                         item['level_rtt_monitors'])
                        datalist.append(level)
                return datalist
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            print(message)
            return None
    
    ########## post htconfig ##########
    def post_HTConfig(self,token,cid,hb_protocol,hb_tag,hb_yml_name,schedule,origin,enabled,created_by,updated_by,url_heartbeat,detail_heartbeat):
        try:
            post_data={"cid":cid,"hb_protocol":hb_protocol,"hb_tag":"","hb_yml_name":hb_yml_name,"schedule":schedule,"origin":origin
                        ,"enabled":enabled,"created_by":created_by,"updated_by":updated_by,"url_heartbeat":url_heartbeat,"detail_heartbeat":detail_heartbeat}
            get_url = "{}api/heartbeat/".format(self.apihost)
            header = {'Authorization':'JWT {}'.format(token),'Content-type': 'application/json'}
            log.logger.info(json.dumps(post_data))
            res = requests.post(get_url,headers=header, data=json.dumps(post_data),timeout=30)
            data =  res.json()
            log.logger.info(json.dumps(post_data))

            if data:
                config =  HTConfig(data['id'],
                                   data['cid'],
                                   data['hb_protocol'],
                                   data['hb_tag'],
                                   data['hb_yml_name'],
                                   data['schedule'],
                                   data['origin'],
                                   data['enabled'],
                                   data['created_by'],
                                   data['created_time'],
                                   data['updated_by'],
                                   data['updated_time'],
                                   data['url_heartbeat'],
                                   data['detail_heartbeat'])
                return config
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            log.logger.info(message)
            return None

    def post_HTConfigInstance(self,token,heartbeat,instance,status,enabled):
        try:
            post_data={"enabled":enabled,"heartbeat":heartbeat,"instance":instance,"status":status}
            get_url = "{}api/heartbeat-instance/".format(self.apihost)
            headers = {'Authorization':'JWT {}'.format(token),'Content-type': 'application/json'}
            res = requests.post(get_url, headers=headers, data=json.dumps(post_data),timeout=30)
            item =  res.json()
            if item:
                config =  HTConfigInstance(item['id'],
                                           item['heartbeat'],
                                           item['instance'],
                                           item['enabled'],
                                           item['status'])
                return config
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            log.logger.info(message)
            return None    

    def post_customercontact(self,token,cid,type_id,recipient_id,subject):
        try:
            post_data={"cid":cid,"recipient_id":recipient_id,"type_id":type_id,"subject":subject}
            get_url = "{}api/customer-contact/".format(self.apihost)
            header = {'Authorization':'JWT {}'.format(token),'Content-type': 'application/json'}
            res = requests.post(get_url,headers=header, data=json.dumps(post_data),timeout=30)
            data =  res.json()
            log.logger.info("data:{}".format(data))

            if data:
                customercontact = CustomerContact(data["id"],
                                                  data["cid"],
                                                  data["recipient_id"],
                                                  data["type_id"],
                                                  data["subject"])
                return customercontact
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            log.logger.info(message)
            return None
   
    ########## post alert ##########

    def post_levelerror(self,token,status_type,cid,threshold,total_bucket,error_bucket,alerting,interval,enabled):
        try:
            post_data={"cid":cid,"threshold":threshold,"total_bucket":total_bucket,"error_bucket":error_bucket,
                        "alerting":alerting,"interval":interval,"enabled":enabled}
            get_url = "{}api/alert/{}/".format(self.apihost,status_type)
            header = {'Authorization':'JWT {}'.format(token),'Content-type': 'application/json'}
            res = requests.post(get_url,headers=header, data=json.dumps(post_data),timeout=30)
            if res.status_code == 201:
                item =  res.json()
                if item:
                    level = levelerror(item['id'],
                                       item['cid'],
                                       item['threshold'],
                                       item['total_bucket'],
                                       item['error_bucket'],
                                       item['alerting'],
                                       item['interval'],
                                       item['enabled'])
                    return level
                else:
                    return None
            else:
                log.logger.info("[post_levelerror]Fail status code:{}".format(res.status_code))
                return None


        except Exception as e:
            message =  "Exception : "+ str(e)
            log.logger.info(message)
            return None

    def post_levelnot20030x(self,token,cid,alerting_time,recovery_time,bucket,history_avg,alerting,interval,enabled):
        try:
            post_data={"cid":cid,"alerting_time":alerting_time,"recovery_time":recovery_time,"bucket":bucket,
                       "history_avg":history_avg,"alerting":alerting,'interval':interval,"enabled":enabled}
            get_url = "{}api/alert/not20030x/".format(self.apihost)
            header = {'Authorization':'JWT {}'.format(token),'Content-type': 'application/json'}
            res = requests.post(get_url,headers=header, data=json.dumps(post_data),timeout=30)
            if res.status_code == 201:
                item =  res.json()
                if item:
                     level = levelnot20030x(item['id'],
                                            item['cid'],
                                            item['alerting_time'],
                                            item['recovery_time'],
                                            item['bucket'],
                                            item['history_avg'],
                                            item['alerting'],
                                            item['interval'],
                                            item['enabled'])
                     return level
                else:
                     return None
            else:
                log.logger.info("[post_levelnot20030x]Fail status code:{}".format(res.status_code))
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            log.logger.info(message)
            return None
    
    def post_leveldown(self,token,cid,hid,down_percentage_alert,down_percentage_recovery,bucket,level_down_monitors,enabled):
        try:
            post_data={"cid":cid,"hid":hid,"down_percentage_alert":down_percentage_alert,"down_percentage_recovery":down_percentage_recovery,
                       "enabled":enabled,"bucket":bucket,'level_down_monitors':level_down_monitors}
            get_url = "{}api/alert/level-down/".format(self.apihost)
            header = {'Authorization':'JWT {}'.format(token),'Content-type': 'application/json'}
            res = requests.post(get_url,headers=header, data=json.dumps(post_data),timeout=30)
            if res.status_code == 200 or res.status_code == 201 :
                item =  res.json()
                if item:
                    level = leveldown(item['id'],
                                    item['cid'],
                                    item['hid'],
                                    item['down_percentage_alert'],
                                    item['down_percentage_recovery'],
                                    item['bucket'], 
                                    item['enabled'],
                                    item['level_down_monitors'])
                    return level
                else:
                    return None
            else:
                log.logger.info("[post_leveldown]Fail status code:{}".format(res.status_code))
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            log.logger.info(message)
            return None

    def post_levelrtt(self,token,cid,hid,rtt_percentage_alert,rtt_percentage_recovery,rtt_threshold,bucket,level_rtt_monitors,enabled):
        try:
            post_data={"cid":cid,"hid":hid,"rtt_percentage_alert":rtt_percentage_alert,"rtt_percentage_recovery":rtt_percentage_recovery,
                       "rtt_threshold":rtt_threshold,"enabled":enabled,"bucket":bucket,'level_rtt_monitors':level_rtt_monitors}
            get_url = "{}api/alert/level-rtt/".format(self.apihost)
            header = {'Authorization':'JWT {}'.format(token),'Content-type': 'application/json'}
            res = requests.post(get_url,headers=header, data=json.dumps(post_data),timeout=30)
            if res.status_code == 200 or res.status_code == 201 :
                item =  res.json()
                if item:
                    level = levelrtt(item['id'],
                                        item['cid'],
                                        item['hid'],
                                        item['rtt_percentage_alert'],
                                        item['rtt_percentage_recovery'],
                                        item['rtt_threshold'],
                                        item['bucket'],
                                        item['enabled'],
                                        item['level_down_monitors'])
                    return level
                else:
                    return None
            else:
                log.logger.info("[post_levelrtt]Fail status code:{}".format(res.status_code))
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            log.logger.info(message)
            return None

    ########## patch htconfig ##########
    def patch_HTConfig(self,token,config_id,tag,schedule,origin,enable,updated_by,url_heartbeat,detail_heartbeat):
        try:
            post_data={"updated_by":updated_by}
            if tag:
                post_data['hb_tag'] = tag
            if schedule:
                post_data['schedule'] =  schedule
            if origin:
                post_data['origin'] = origin
            if enable is not None :
                post_data['enabled'] = enable
            if url_heartbeat:
                post_data['url_heartbeat'] = url_heartbeat
            if detail_heartbeat:
                post_data['detail_heartbeat'] = detail_heartbeat
            get_url = "{}api/heartbeat/{}/".format(self.apihost,config_id)
            header = {'Authorization':'JWT {}'.format(token),'Content-type': 'application/json'}
            res = requests.patch(get_url,  headers=header, data=json.dumps(post_data),timeout=20)
            log.logger.info("post_data:{}".format(json.dumps(post_data)))
            log.logger.info("response data:{}".format(res))
            data =  res.json()

            if data:
                config =  HTConfig(data['id'],
                                   data['cid'],
                                   data['hb_protocol'],
                                   data['hb_tag'],
                                   data['hb_yml_name'],
                                   data['schedule'],
                                   data['origin'],
                                   data['enabled'],
                                   data['created_by'],
                                   data['created_time'],
                                   data['updated_by'],
                                   data['updated_time'],
                                   data['url_heartbeat'],
                                   data['detail_heartbeat'])
                return config
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            log.logger.info(message)
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

    def patch_HTConfigInstance(self,token,config_id,status_id,enabled):
        try:

            post_data={}
            if status_id:
                post_data['status'] = status_id
            if enabled is not None:
                post_data['enabled'] = enabled

            header = {'Authorization':'JWT {}'.format(token),'Content-type': 'application/json'}
            get_url = "{}api/heartbeat-instance/{}/".format(self.apihost,config_id)
            log.logger.info(get_url)

            res = requests.patch(get_url,headers=header, data=json.dumps(post_data),timeout=30)
            log.logger.info(json.dumps(post_data))
            log.logger.info(get_url)
            log.logger.info(res)
            item =  res.json()   
            log.logger.info(item)   
            if item:
                config =  HTConfigInstance(item['id'],
                                           item['heartbeat'],
                                           item['instance'],
                                           item['enabled'],
                                           item['status'])
                return config
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            log.logger.info(message)
            return None
   
    def patch_CustomerInstances(self,token,customer_id,instances):
        try:
            post_data={"instance":instances}
            get_url = "{}api/customer/{}/".format(self.apihost,customer_id)
            header = {'Authorization':'JWT {}'.format(token),'Content-type': 'application/json'}
            res = requests.patch(get_url,  headers=header, data=json.dumps(post_data),timeout=20)
            data =  res.json()
            if data:
                customerinfo = CustomerInfo(data["id"],
                                            data["name"],
                                            data["enabled"],
                                            data["max_url_num"],
                                            data["max_monitor_num"],
                                            data["min_interval_num"],
                                            data["instance"])
                return customerinfo
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            print(message)
            return None
    
    ########## patch alert ##########

    def patch_customercontact(self,token,contact_id,type_id,recipient_id,subject):
        try:
            post_data={"recipient_id":recipient_id}
            if type_id :
                post_data['type_id'] = type_id
            if subject:
                post_data['subject'] = subject
            get_url = "{}api/customer-contact/{}/".format(self.apihost,contact_id)
            header = {'Authorization':'JWT {}'.format(token),'Content-type': 'application/json'}
            res = requests.patch(get_url,  headers=header, data=json.dumps(post_data),timeout=20)
            data =  res.json()
            if data:
                customercontact = CustomerContact(data["id"],
                                                  data["cid"],
                                                  data["recipient_id"],
                                                  data["type_id"],
                                                  data["subject"])
                return customercontact
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            print(message)
            return None  

    def patch_levelerror(self,token,status_type,level_id,threshold,total_bucket,error_bucket,interval,enabled):
        try:
            post_data={}
            if threshold:
                post_data['threshold'] = threshold
            if total_bucket:
                post_data['total_bucket'] = total_bucket
            if error_bucket:
                post_data['error_bucket'] = error_bucket
            if interval:
                post_data['interval'] = interval
            if enabled is not None :
                post_data['enabled'] = enabled
            get_url = "{}api/alert/{}/{}/".format(self.apihost,status_type,level_id)
            header = {'Authorization':'JWT {}'.format(token),'Content-type': 'application/json'}
            res = requests.patch(get_url,  headers=header, data=json.dumps(post_data),timeout=20)
            item =  res.json()
            if item:
                level = levelerror(item['id'],
                                   item['cid'],
                                   item['threshold'],
                                   item['total_bucket'],
                                   item['error_bucket'],
                                   item['alerting'],
                                   item['interval'],
                                   item['enabled'])
                return level
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            log.logger.info(message)
            return None

    def patch_levelnot20030x(self,token,level_id,alerting_time,recovery_time,bucket,interval,enabled):
        try:
            post_data={}
            if alerting_time:
                post_data['alerting_time'] = alerting_time
            if recovery_time:
                post_data['recovery_time'] = recovery_time
            if bucket:
                post_data['bucket'] = bucket
            if interval:
                post_data['interval'] = interval
            if enabled is not  None :
                post_data['enabled'] = enabled
            get_url = "{}api/alert/not20030x/{}/".format(self.apihost,level_id)
            header = {'Authorization':'JWT {}'.format(token),'Content-type': 'application/json'}
            res = requests.patch(get_url,  headers=header, data=json.dumps(post_data),timeout=20)
            item =  res.json()
            if item:
                level = levelnot20030x(item['id'],
                                       item['cid'],
                                       item['alerting_time'],
                                       item['recovery_time'],
                                       item['bucket'],
                                       item['alerting'],
                                       item['interval'],
                                       item['enabled'],
                                       item['history_avg'])
                return level
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            log.logger.info(message)
            return None

    def patch_leveldown(self,token,level_id,down_percentage_alert,down_percentage_recovery,bucket,level_down_monitors,enabled):
        try:
            post_data={}
            if down_percentage_alert:
                post_data['down_percentage_alert'] = down_percentage_alert
            if down_percentage_recovery:
                post_data['down_percentage_recovery'] = down_percentage_recovery
            if bucket:
                post_data['bucket'] = bucket
            if enabled is not None:
                post_data["enabled"]=enabled
            if level_down_monitors:
                post_data["level_down_monitors"] = level_down_monitors

            get_url = "{}api/alert/level-down/{}/".format(self.apihost,level_id)
            header = {'Authorization':'JWT {}'.format(token),'Content-type': 'application/json'}
            log.logger.info("[patch_leveldown]post_data:{}".format(post_data))
            res = requests.patch(get_url,  headers=header, data=json.dumps(post_data),timeout=20)
            if res.status_code== 200:
                item =  res.json()
                log.logger.info("[patch_leveldown]item:{}".format(item))
                if item:
                    level = leveldown(item['id'],
                                    item['cid'],
                                    item['hid'],
                                    item['down_percentage_alert'],
                                    item['down_percentage_recovery'],
                                    item['bucket'], 
                                    item['enabled'],
                                    item['level_down_monitors'])
                    return level
                else:
                    None
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            log.logger.info(message)
            return None

    def patch_levelrtt(self,token,level_id,rtt_percentage_alert,rtt_percentage_recovery,rtt_threshold,bucket,level_rtt_monitors,enabled):
        try:
            post_data={}
            if rtt_percentage_alert:
                post_data['rtt_percentage_alert']= rtt_percentage_alert
            if rtt_percentage_recovery:
                post_data['rtt_percentage_recovery'] = rtt_percentage_recovery
            if rtt_threshold:
                post_data['rtt_threshold'] = rtt_threshold
            if bucket:
                post_data['bucket'] = bucket
            if enabled is not None:
                post_data["enabled"]=enabled
            if level_rtt_monitors:
                post_data["level_rtt_monitors"] = level_rtt_monitors

            get_url = "{}api/alert/level-rtt/{}/".format(self.apihost,level_id)
            log.logger.info("[patch_levelrtt]post_data:{}".format(post_data))
            header = {'Authorization':'JWT {}'.format(token),'Content-type': 'application/json'}
            res = requests.patch(get_url,  headers=header, data=json.dumps(post_data),timeout=20)

            if res.status_code== 200:
                item =  res.json()
                if item:
                    level = levelrtt(item['id'],
                                        item['cid'],
                                        item['hid'],
                                        item['rtt_percentage_alert'],
                                        item['rtt_percentage_recovery'],
                                        item['rtt_threshold'],
                                        item['bucket'],
                                        item['enabled'],
                                        item['level_rtt_monitors'])
                    return level
                else:
                    None
            else:
                return None
        except Exception as e:
            message =  "Exception : "+ str(e)
            log.logger.info(message)
            return None

    
if __name__ == '__main__':
  dev_api_ip = '192.168.1.135'
  username = 'letron'
  password = 'l@tr0n2019'
  api = lg_operation_api(dev_api_ip)
  token  = api.get_jwt_token(username,password)

  if token:
      data={}

      #### post testing ####
      userpofile =  api.get_userprofile(token,username)
      data['user']= userpofile.__dict__

      print("{} : {} : {}".format(userpofile.id,userpofile.user_name,userpofile.customer_id))
      cid = userpofile.customer_id
      hb_protocol = 1
      hb_tag = ''
      hb_yml_name = 'letron_http_rickytesting1.yml'
      schedule =300
      enabled =False
      #htconfigs = api.get_HTConfigs(token,userpofile.customer_id)
      

      #url_heartbeat = [{ "full_url":"http://www.testing6.tw"},{ "full_url":"http://www.test7.com"}]
      #detail_heartbeat =  [{"key":"check.request:testing","value": "status: 200\r\n    body:\r\n      - Saved\r\n      - saved"}]
      #config =  api.patch_HTConfigInstance(token,13,None,enabled)
      ##### post heartbeat config testing #####
      #config = api.post_HTConfig(token,cid,hb_protocol,hb_tag,hb_yml_name,schedule,enabled,username,username,url_heartbeat,detail_heartbeat)
      #if config:
      #    print("{} : {}".format(config.id,config.hb_yml_name))


      ##### patch heartbeat config testing ####
      #config_id = 11
      #tag =""
      #enabled = True
      #schedule= None
      #url_heartbeat = [{ "id": 10, "full_url":"http://www.testing1.tw"},{ "id": 11, "full_url":"http://www.test2.com"}]
      #detail_heartbeat =  [{"id": 6 ,"key":"check.request:rickytesting","value": "status: 200\r\n    body:\r\n      - Saved\r\n      - saved"}]

      #config = api.patch_HTConfig(token,config_id,hb_tag,schedule,enabled,username,url_heartbeat,detail_heartbeat)
      #print("{} : {}".format(config.id,config.hb_yml_name))
      

      ## post heartbeat config instance testing ###

      #config_id = 11
      #status_id = 1
      #eanble = True
      #instance_list = [13,14,15,16,17]
      #for instance_id in instance_list:
      #    config =  api.post_HTConfigInstance(token,config_id,instance_id,status_id,eanble)

      ### patch heartbeat config instance testing ###
      #status_id=None
      #eanble = False
      #config_instance_list = [13,14,15]
      #for config_instance_id in config_instance_list:
      #    config =  api.patch_HTConfigInstance(token,config_instance_id,status_id,eanble)
      #    print("{} : {}".format(config.id,config.instance))

      #status_id =2
      #eanble = None
      #config_instance_list = [16,17]
      #for config_instance_id in config_instance_list:
      #    config =  api.patch_HTConfigInstance(token,config_instance_id,status_id,eanble)
      #    print("{} : {}".format(config.id,config.instance))


    ### update heartbeat config instance testing ###


      #### get api testing####
      #protocals = api.get_protocols(token)
      #for protocal in protocals:
        #print("{} : {} ".format(protocal.id,protocal.name))
        #single_protocal = api.get_protocol(token,protocal.id)
        #print("{} : {} ".format(single_protocal.id,single_protocal.name))

      #userpofile =  api.get_userprofile(token,username)
      #print("{} : {} : {}".format(userpofile.id,userpofile.user_name,userpofile.customer_id))
      #if UserProfile:
          #customer =  api.get_customerinfo(token,userpofile.customer_id)
          #print("{} : {} ".format(customer.id,customer.name))

          #instances =  api.get_instances(token,None)
          #for instance in instances:
          #    print("{} : {}".format(instance.id,instance.ch_name))

          #    single_instance = api.get_instance(token,instance.id)
          #    print("{} : {}".format(single_instance.id,single_instance.ch_name))

          #htconfigs = api.get_HTConfigs(token,userpofile.customer_id)
          #for config in htconfigs:
          #    print("{} : {}".format(config.id,config.hb_yml_name))

          #    single_config = api.get_HTConfig(token,config.id)
          #    print("{} : {}".format(single_config.id,single_config.hb_yml_name))

          #    config_instances = api.get_HTConfigInstances(token,config.id)
          #    for config_instance in config_instances:
          #        print("{} : {} : {}".format(config_instance.id,config_instance.heartbeat, config_instance.instance))

          #        single_config_instance = api.get_HTConfigInstance(token,config_instance.id)
          #        print("{} : {} : {}".format(single_config_instance.id,single_config_instance.heartbeat, single_config_instance.instance))
        
  #api.get_config_bycustomer()
  #api.get_instance_list()
  #configdetail = api.get_HTJobInstanceDetail(5)
  #print(configdetail.urls)
  #print(configdetail.nodes)
  #print(configdetail.others)

  #for item in api.get_HTConfJobByCID():
  #    config_id = item.config
  #    job = item.hosturls
  #    tmp_config = api.get_config(config_id)
  #    jobconfig = JobInstanceDetail(job,tmp_config['protocol_name'],1,tmp_config['interval'],None)
  #    jobconfig.node_status = api.get_HTConfinstanceByID(config_id)
  #    if jobconfig.node_status.failed > 0 or jobconfig.node_status.progress >0:
  #        jobconfig.status = 0
  #    datalist.append(jobconfig)
  #monitorlist = api.get_instance_list()
  #regionlist= list(set([instance.region for instance in monitorlist]))
  #isplist= list(set([instance.isp for instance in monitorlist]))


      



