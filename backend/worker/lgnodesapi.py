# -*- coding: UTF-8 -*-

import os
import sys
import timeit
import datetime
import shlex
import json
import io
import requests
from mlog import Log

log = Log("lg_api_log","lg_api_log")

class Instance(object):
    def __init__(self,id,nid,region,isp,ch_name,host_ip,status_name):
        self.id = id
        self.nid = nid
        self.region = region
        self.isp = isp
        self.ch_name =ch_name
        self.host_ip = host_ip
        self.status_name = status_name

class Region(object):
    def __init__(self,id,en_name,ch_name):
        self.id = id
        self.en_name =  en_name
        self.ch_name = ch_name
  

class lg_nodes_api(object):
    def __init__(self,node_region_name,node_monitor_name,node_ip):
        self.node_ip = node_ip
        self.node_region_name = node_region_name
        self.node_monitor_name = node_monitor_name

    def get_postdata(self,lg_command,lg_host,lg_origin,curl_domain,curl_port,curl_ip,tcp_port,nslookup_type,nslookup_dns):
        my_data = {}
        if lg_command == "curl":
            lg_host = '-i %s'%(lg_host)
            my_data={'host':lg_host,'domain':curl_domain,'port':curl_port,'ip':curl_ip}
        elif lg_command == "websocket":
            lg_host = '-i %s'%(lg_host)
            my_data={'host':lg_host,'origin':lg_origin,'domain':curl_domain,'port':curl_port,'ip':curl_ip}
        elif lg_command == "ping":
                my_data={'host':lg_host}
        elif lg_command == "tcping":
                my_data={'host':lg_host,'port':tcp_port}
        elif lg_command == "nslookup" or lg_command == "dig": 
                my_data={'host':lg_host,'type':nslookup_type,'dns':nslookup_dns}
        elif lg_command == "mtr":
                my_data={'host':lg_host}
        elif lg_command == "har":
                my_data={'domain':lg_host}
        
        return my_data
    
    def get_nodes_api(self,lg_command,lg_host,lg_origin,curl_domain,curl_port,curl_ip,tcp_port,nslookup_type,nslookup_dns):
        apihost = ("https://{}:5433/{}".format(self.node_ip,lg_command))
        session = requests.Session()
        session.verify = False
        if lg_command == "curl":
            lg_host = '-i %s'%(lg_host)
            my_data={'host':lg_host,'domain':curl_domain,'port':curl_port,'ip':curl_ip}
        elif lg_command == "websocket":
            lg_host = '-i %s'%(lg_host)
            my_data={'host':lg_host,'origin':lg_origin,'domain':curl_domain,'port':curl_port,'ip':curl_ip}
        elif lg_command == "ping":
                my_data={'host':lg_host}
        elif lg_command == "tcping":
                my_data={'host':lg_host,'port':tcp_port}
        elif lg_command == "nslookup" or lg_command == "dig": 
                my_data={'host':lg_host,'type':nslookup_type,'dns':nslookup_dns}
        elif lg_command == "mtr":
                my_data={'host':lg_host}
        elif lg_command == "har":
                my_data={'domain':lg_host}
        try:
            if lg_command == 'har':
                res_data = session.post(apihost, data = my_data, timeout=60)
            else:
                res_data = session.get(apihost, params = my_data, timeout=60)
        except Exception as e:
            json_obj={}
            message =  "Exception : "+ str(e)
            json_obj["result"] = message
            json_obj["status_code"] = 408
            json_obj["total_time"] = 5
            res_data = json.dumps(json_obj)
        print(type(res_data)) 
        return res_data


    def get_nodes_yml_api(self,jwttoken,httype):
        header = "Authorization: JWT {}".format(jwttoken)
        apihost = "http://{}:5001/heartbeat/{}".format(self.node_ip,httype)
        res_data = requests.post(apihost, data = my_data, headers=header, timeout=60)
   

    def __get_node_jwt_token(self,username,password):
        apihost = "http://{}:5001/login".format(self.node_ip)
        data = json.dumps({"username": username, "password": password})
        header = {"Content-Type": "application/json"}
        res = requests.post(apihost, data=data, headers=header)
        token = res.json()['access_token']
        print('token:'+token)
        return token

    def get_local_api(self):
        apihost = "http://127.0.0.1:8089/api/instance/"
        res_data = requests.get(apihost, timeout=60)
        return res_data

   
    def get_ssh_result(node_ssh_port,command):
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

class lg_instance_api(object):
    def __init__(self):
        self.api_host = '18.162.81.56'
        self.api_host_port = '8080'
        self.username ='letron'
        self.password ='l@tr0n2019'

    def __get_operation_jwt_token(self):
        header = {"Content-Type": "application/json"}
        url = "http://{}:{}/api-token-auth/".format(self.api_host, self.api_host_port)
        data = json.dumps({"username": self.username, "password": self.password})
        res = requests.post(url, data=data, headers=header)
        token = res.json()['token']
        return token

    def get_regions(self):
        jwttoken = self.__get_operation_jwt_token()
        datalist = list()
        header = {"Authorization": "JWT {}".format(jwttoken)}
        url = "http://{}:{}/api/region/".format(self.api_host,self.api_host_port)
        res = requests.get(url,headers=header,timeout=20)
        data = res.json()
        for item in data:
            datalist.append(Region(item["id"],item["en_name"],item["ch_name"]))
        return datalist


    def get_instances(self):
        jwttoken = self.__get_operation_jwt_token()
        datalist = list()
        header = {"Authorization": "JWT {}".format(jwttoken)}
        url = "http://{}:{}/api/instance/".format(self.api_host,self.api_host_port)
        res = requests.get(url,headers=header,timeout=20)
        data = res.json()
        for item in data:
            datalist.append(Instance(item["id"],item["nid"],item["region_name"],item["isp_name"],item["ch_name"],item["host_ip"],item["status_name"]))
        return datalist
   
    def get_instance(self,instance_id):
        jwttoken = self.__get_operation_jwt_token()
        header = {"Authorization": "JWT {}".format(jwttoken)}
        url = "http://{}:{}/api/instance/{}".format(self.api_host,self.api_host_port,instance_id)
        res = requests.get(url,headers=header, timeout=20)
        item = res.json()
        if item :
            return Instance(item["id"],item["nid"],item["region_name"],item["isp_name"],item["ch_name"],item["host_ip"],item["status_name"])
        else:
            return None



###### heartbeat generate api in the node ####

class node_heartbeat(object):
    def __init__(self,hostip):
        #self.apihost = "http://192.168.1.135:8080/api"
        self.apihost = "http://{}:5001/".format(hostip)
        self.token = '' 

        ########## GET ##########
    def get_node_jwt_token(self,username,password):
        try:
            apiurl = "{}login".format(self.apihost)
            data = json.dumps({"username": username, "password": password})
            header = {"Content-Type": "application/json"}
            res = requests.post(apiurl, data=data, headers=header)
            self.token = res.json()['access_token']

        except Exception as e:
            message =  "Exception : "+ str(e)
            return None

    def New_HTConfig(self,ip,ht_yml_file,ht_type,max_redirects,customer_name,customer_id,isp_name,region_name,monitor_name,schedule,origin,jobs,check_request,check_response):
        try:
            postdata = {}
            protocol = ht_type
            if ht_type == 'websocket':
                ht_type = 'http'
            postdata['ip'] = ip
            postdata['yml_file'] = ht_yml_file
            postdata['type'] = ht_type
            postdata['protocol']=  protocol
            postdata['customer'] = customer_name
            postdata['customer_number']= customer_id
            postdata['isp'] =isp_name
            postdata['region'] =region_name
            postdata['monitor_name'] = monitor_name
            postdata['schedule'] = schedule
            if ht_type == 'http':
                postdata['origin']=''
                if protocol == 'websocket':
                    postdata['origin'] = origin
                postdata['max_redirects'] = max_redirects
                postdata['urls'] = jobs
                
                ### other option
                if check_request:
                    postdata['checkout_request'] = check_request
                if check_response:
                    postdata['checkout_response'] = check_response
            else:
                postdata['hosts'] = jobs
            apiurl = "{}heartbeat/{}".format(self.apihost,ht_type)
            print(apiurl)
            print(postdata)
            header = {'Authorization':'Bearer {}'.format(self.token),'Content-type': 'application/x-www-form-urlencoded'}
            res = requests.post(apiurl, data=postdata, headers=header)
            data = res.json()                
            print(data)
            if data['status_code'] == 200:
                return True
            else:
                return False
        except Exception as e:
            message =  "Exception : "+ str(e)
            print(message)
            return None
    def Get_HTConfig(self,ht_yml_file):
        try:
            apiurl = "{}heartbeat/{}".format(self.apihost,ht_yml_file)
            header = {'Authorization':'Bearer {}'.format(self.token),'Content-type': 'application/x-www-form-urlencoded'}

            res = requests.get(apiurl, data=postdata, headers=header)
            data = res.json()
            return data
        except Exception as e:
            message =  "Exception : "+ str(e)
            return None

    def Delete_HTConfig(self,ip,ht_yml_file):
        try:
            postdata = {'ip':ip,'yml_file':ht_yml_file}
            apiurl = "{}heartbeat".format(self.apihost)
            header = {'Authorization':'Bearer {}'.format(self.token),'Content-type': 'application/x-www-form-urlencoded'}
            res = requests.delete(apiurl, data=postdata, headers=header)
            data = res.json()
            return data
        except Exception as e:
            message =  "Exception : "+ str(e)
            return None


if __name__ == '__main__':
    test_ip = '18.162.81.56'
    monitor_ip = '116.138.176.68' 
    username ='admin'
    password ='srsdeploy'
    node_ht = node_heartbeat(test_ip)
    node_ht.get_node_jwt_token(username,password)
    print("token :{}".format(node_ht.token))
    if node_ht.token:
        url ='\"http://www.google.com\",\"http://www.youtube.com\"'
    
        result = node_ht.New_HTConfig(monitor_ip,"ricky_http_testing1.yml","http",0,'staging',100,'网通','東北','辽宁抚顺网通',300,None,url,None,None)
        print("new config result:{}".format(result))

        result = node_ht.Delete_HTConfig(monitor_ip,"ricky_http_testing1.yml")
        print("delete config result:{}".format(result))



    
