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
from worker.config import historyapihost,historyapiport

log = Log("lg_history_api","lg_history_api_log")


class lg_history_api(object):
    def __init__(self,customer,user_id,query_count):
        self.customer = customer
        self.user_id = user_id
        self.query_count = query_count
        self.apihost = "http://{}:{}/lg".format(historyapihost,historyapiport)

    def create_lg_history(self,history_task_id,monitor_name,command,host,status_code,total_time,down_link,header,body,res_data):
        try:
            post_url =  self.apihost
            headers = {'Content-Type': 'application/json'}
            if command == 'har':
                body = down_link
            if res_data:
                result =  res_data.json()
            else:
                result =''
            my_data={'customer':self.customer,
                     'uid': self.user_id,
                     'monitor':monitor_name,
                     'type':command,
                     'domain':host,
                     'status_code':str(status_code),
                     "total_time":str(total_time),
                     "header":header,
                     'body':body,
                     'task_id':str(history_task_id),
                     'result':result}
            log.logger.info("create_lg_history my_data :{}".format(my_data))
            res = requests.post(post_url, headers=headers, data = json.dumps(my_data))
            log.logger.info("create_lg_history post :{}".format(res.json()))
            return res
        except Exception as e:
            message =  "Exception : "+ str(e)
            log.logger.info("create_lg_history post :"+message)

    def get_lg_history(self,id):
        try:
            get_url = "{}/{}?count={}".format(self.apihost,self.user_id,self.query_count)
            if id:
                get_url =get_url+"&id={}".format(id)
            res = requests.get(get_url, timeout=20)
            return res
        except Exception as e:
            message =  "Exception : "+ str(e)
            log.logger.info("get_lg_history get :"+message)

    def search_lg_history(self,command,monitor):
        try:
            get_url = "{}/{}?count={}&customer={}".format(self.apihost,self.user_id,self.query_count,self.customer)
            if command and monitor:
                get_url =get_url+"&lg_type={}&monitor={}".format(command,monitor)
            else:
                if command :
                    get_url = get_url+"&lg_type={}".format(command)
                if monitor:
                    get_url =get_url+"&monitor={}".format(monitor)
            res = requests.get(get_url, timeout=20)
            log.logger.info("search_lg_history get :{}".format(res.json()))

            return res
        except Exception as e:
            message =  "Exception : "+ str(e)
            log.logger.info("search_lg_history get :"+message)

    def search_lg_history_bytask(self,task_id):
        try:
            get_url = "{}/{}?task_id={}".format(self.apihost,self.user_id,task_id)
            res = requests.get(get_url, timeout=20)
            log.logger.info("search_lg_history_bytask get :{}".format(res.json()))
            return res
        except Exception as e:
            message =  "Exception : "+ str(e)
            log.logger.info("search_lg_history_bytask get :"+message)

if __name__ == '__main__':
    CUSTOMER='Letron'
    user_id = 5
    history =lg_history_api(CUSTOMER,user_id,20)
    monitor_name='辽宁抚顺网通'
    command ='ping'
    status_code = "200"
    total_time ="200"
    down_link=''
    header ='testing'
    body ='testing'
    res_data = ''
    host = '8.8.8.8'
    res = history.search_lg_history("","")
    print(res.json())
