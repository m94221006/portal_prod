# -*- coding: UTF-8 -*-

import os
import sys
import timeit
import datetime
import shlex
import json
import io
import requests
import datetime
import logging
import time
import os
import traceback
from worker.config import nodehtapihost,nodehtapiport

class Log:
    def __init__(self,log_file_name,log_name):
        self.logfilename = "%s%s.log"%(log_file_name,time.strftime("%Y%m%d%H%M", time.gmtime()))
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
        fh = logging.FileHandler(filepath,encoding='utf-8')
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        console.setFormatter(formatter)
        logger.addHandler(console)
        return logger

###### looking glass api in the node #######
class nodes_tool_api(object):
    def __init__(self,node_region_name,node_monitor_name,node_ip):
        self.apihost = "http://{}:5000/".format(node_ip)
        self.node_region_name = node_region_name
        self.node_monitor_name = node_monitor_name
    
    def get_nodes_api(self,lg_command,lg_host,lg_origin,curl_domain,curl_port,curl_ip,tcp_port,nslookup_type,nslookup_dns):
        getrurl  = ("{}{}".format(self.apihost,lg_command))
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
                res_data = requests.post(apihost, data = my_data, timeout=60)
            else:
                res_data = requests.get(apihost, params = my_data, timeout=60)
        except Exception as e:
            json_obj={}
            message =  "Exception : "+ str(e)
            json_obj["result"] = message
            json_obj["status_code"] = 408
            json_obj["total_time"] = 5
            res_data = json.dumps(json_obj)
        print(type(res_data)) 
        return res_data

###### heartbeat generate api in the node ####
class Node_HTConfig(object):
      def __init__(self,customer_id,customer_name,region_name,isp_name,monitor_name,schedule,urls,ht_yml_file,ht_type,origin):
        self.__data ={}
        self.__data["customer_number"] = customer_id
        self.__data["customer"] = customer_name
        self.__data["protocol"] = ht_type
        self.__data["isp"] = isp_name
        self.__data["region"] = region_name
        self.__data["monitor_name"] =monitor_name
        self.__data["schedule"] = schedule
        self.__data["yml_file"] = ht_yml_file
        self.__data["type"] = ht_type
        self.__data["max_redirects"] = 0

        if self.__data["type"] == 'websocket':
            self.__data["type"]  = 'http'
            self.__data["protocol"] = 'websocket'
            self.__data["origin"] = origin

        self.__data["urls"] = urls
        if self.__data["type"] !='http':
            self.__data["hosts"] = urls


      def set_check_request(self,checkout_request):
          self.__data["checkout_request"] = checkout_request
    
      def set_check_response(self,checkout_response):
         self.__data["checkout_response"] =checkout_response

      def set_monitor_ip(self,monitor_ip):
          self.__data["ip"] =  monitor_ip

      def set_asia(self):
           self.__data['is_asia'] =  True

      def get_ht_type(self):
          return self.__data["type"]

      def get_config_data(self):
          return self.__data 


class nodes_heartbeat_api(object):
    def __init__(self,hostip,is_asia):
        #self.apihost = "http://192.168.1.135:8080/api"
        self.hostip = hostip
        self.is_asia = is_asia
        self.apihost = "http://{}:{}/".format(nodehtapihost,nodehtapiport)
        self.token = ''
        self.get_node_jwt_token('admin','srsdeploy') 

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

    def New_HTConfig(self,node_config,check_request,check_response):
        log = Log("lg_operation_api","lg_operation_api_log")
        try:
            #if self.hostip not in  self.node_testing_list:
            node_config.set_monitor_ip(self.hostip)
            
            ### other option
            
            ## set if asia
            if self.is_asia:
                node_config.set_asia()

            ht_type = node_config.get_ht_type()
            if ht_type == 'http' or ht_type== 'websocket':
                if check_request:
                    parse_check_request = self.parse_check('request',check_request)
                    log.logger.info("parse_check_request:{}".format(parse_check_request))
                    if parse_check_request:
                        node_config.set_check_request(parse_check_request)

                if check_response:
                    parse_check_reponse = self.parse_check('response',check_response)
                    log.logger.info("parse_check_reponse:{}".format(parse_check_reponse))

                    if parse_check_reponse:
                        node_config.set_check_response(parse_check_reponse)
                
            apiurl = "{}heartbeat/{}".format(self.apihost,ht_type)
            post_data = node_config.get_config_data()
            log.logger.info("apiurl:{}".format(apiurl))
            log.logger.info("post_data:{}".format(post_data))
            header = {'Authorization':'Bearer {}'.format(self.token),'Content-type': 'application/x-www-form-urlencoded'}
            res = requests.post(apiurl, data=post_data, headers=header,timeout=30)
            result = False
            if res:
               if res.status_code == 200:
                   data = res.json() 
                   log.logger.info(data)
                   if data:
                       if data['status_code'] == 200:
                           result =  True
                       else:
                           result =  False
                   else:
                        result = False
               else:
                    result =  False
            else:
                result =  False
            return res.status_code, result
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
            return 408,None

    def Get_HTConfig(self,ht_yml_file):
        try:
            log = Log("lg_operation_api","lg_operation_api_log")
            apiurl = "{}/heartbeat/?ip={}&filename={}".format(self.apihost,self.hostip,ht_yml_file)
            if self.is_asia:
                apiurl = "{}&is_asia=True".format(apiurl)

            header = {'Authorization':'Bearer {}'.format(self.token),'Content-type': 'application/x-www-form-urlencoded'}
            res = requests.get(apiurl, headers=header,timeout=30)
            if res:
                if res.status_code ==200:
                    data = res.json()
                    return  res.status_code, data
            else:
                return res.status_code, None
        except Exception as e:
            message =  "Exception : "+ str(e)
            return None

    def Delete_HTConfig(self,ht_yml_file):
        try:
            log = Log("lg_operation_api","lg_operation_api_log")
            postdata = {'yml_file':ht_yml_file}
            #if self.hostip not in self.node_testing_list:
            postdata['ip'] = self.hostip
            if self.is_asia:
                postdata["is_asia"] = True
            apiurl = "{}heartbeat".format(self.apihost)
            header = {'Authorization':'Bearer {}'.format(self.token),'Content-type': 'application/x-www-form-urlencoded'}
            res = requests.delete(apiurl, data=postdata, headers=header,timeout=30)
            data = res.json()
            if data:
                if data['status_code'] == 200:
                    return True
                else:
                    return False
            else:
                return False
        except Exception as e:
            message =  "Exception : "+ str(e)
            return False

    def parse_check(self,checktype,checktext):
        log = Log("lg_operation_api","lg_operation_api_log")
        checkitem = json.loads(checktext)
        if checktype == 'request':
            ## header
            checkheadervalue = checkitem['headers']
            if checkheadervalue:
                headerlist = checkheadervalue.split('\n')
                headervalue = {}
                for item in headerlist:
                    if item:
                        log.logger.info("item:{}".format(item))
                        key = item.split(':')[0].replace("'","").strip()
                        value = item.split(':')[1].replace("'","").strip()
                        headervalue[key] =value
                if headervalue:
                    checkitem['headers'] =headervalue

            ## body
            #checkbodyvalue = checkitem['body']
            #if checkbodyvalue:
            #    checkitem['body'] =checkbodyvalue.replace("\"","").replace("'","")

    
        elif checktype == 'response':
            checkvalue = checkitem['body']
            if checkvalue and '-' in checkvalue:
                checkvalue =  checkvalue.replace("\n","").replace('-',",")
                checkvalue = ','.join(list(value.strip() for value in checkvalue.split(',') if value)) 
            checkitem['body'] = checkvalue
        return json.dumps(checkitem)

if __name__ == '__main__':
    test_ip = '18.162.81.56'
    monitor_ip = '121.14.16.30' 
    username ='admin'
    password ='srsdeploy'
    node_ht = nodes_heartbeat_api(monitor_ip)
    print("token :{}".format(node_ht.token))
    if node_ht.token:
        customer_id = 0
        customer_name = 'staging'
        region = '東北'
        isp = '网通'
        monitor='辽宁抚顺网通'
        schedule = 300
        ht_type = 'http'
        ht_yml_file = 'ricky_http_testing1.yml'
        origin = None
        url ='\"http://www.google.com\",\"http://www.youtube.com\"'
        
        checkout_request = "method: POST \r\n headers:\r\n Content-Type: application/x-www-form-urlencoded \r\n body:\r\n  name=first" 
        checkout_response=''
        node_config = Node_HTConfig(customer_id,customer_name,region,isp,monitor,300,url,ht_yml_file,ht_type,origin)
        #data = json.dumps(node_config.get_config_data())

        #result = node_ht.New_HTConfig(node_config,checkout_request,checkout_response)
        #print("new config result:{}".format(result))

        #result = node_ht.Delete_HTConfig(ht_yml_file)
        #print("delete config result:{}".format(result))



    
