# -*- coding: UTF-8 -*-

import os
import sys
import subprocess
import timeit
import datetime
import shlex
import json
import yaml
import io
import requests
#from pyparser import HttpParser
#from io import StringIO
import socket
from http_parser.parser import HttpParser
from http_parser.util import b
import re

from worker.mlog import Log

log = Log("lg_parse_log","lg_parse_log")


class lg_parse(object):
    def __init__(self,host,port,lg_command,content):
        self.host = host
        self.port = port
        self.lg_command = lg_command
        self.content=""
        self.result=""
        self.status_code = 408

        if content:
            if type(content) == str: self.content = json.loads(content)
            else: self.content = content.json()
            self.result =  self.content["result"]
            self.status_code = self.content["status_code"]

    def parsing_content(self):
        down_link = ''
        if self.content:
            if self.status_code != 408:
                if self.lg_command == 'curl' or self.lg_command == 'websocket':
                    if 'Try' in self.result or 'HTTP/1.1' in self.result:
                        status_code,header,body = self.parse_html()
                    else:
                        status_code = self.status_code 
                        header = self.result
                        body = self.result
                        

                    total_time = str(self.content["total_time"])

                elif self.lg_command == 'nslookup':
                    status_code,total_time,header,body = self.parse_nslookup()
                    header = status_code

                elif self.lg_command == 'dig':
                    status_code,total_time,header,body = self.parse_dig()
                    header = status_code
            
                elif self.lg_command == 'tcping':
                    status_code,total_time,header,body = self.parse_tcping()

                elif self.lg_command == 'ping' :
                    status_code,total_time,header,body = self.parse_ping()

                elif self.lg_command == 'mtr':
                    status_code,total_time,header,body = self.parse_mtr()

                elif self.lg_command == 'har':
                    status_code,total_time,down_link,header,body= self.parse_har()
            else:
                status_code = self.status_code 
                total_time = 5
                header = self.result
                body = self.result
            return status_code,total_time,down_link,header,body 

    def parse_html(self):
        try:
            resolve_ip =''
            data = []  
            fitler_list = ['*','> ','< ','{']
            for item in self.result.split("\n"):  
                if 'Trying' in item:
                    resolve_ip =  item.replace('*',"").replace("Trying","").replace("...","").strip()  
                    log.logger.info('resolve_ip: %s '%(resolve_ip))
     
                matching = [s for s in fitler_list if s in item[:2]]
                if len(matching)==0:
                    data.append(item.encode('utf-8'))
            parsing_string = b("\r\n").join(data)
            p = HttpParser()
            p.execute(parsing_string, len(parsing_string))
            status_code = str(p.get_status_code())
            header_obj = p.get_headers()
            #body = str(p.recv_body())
            
            header_list =[]
            if resolve_ip:
                header_list.append('%s:%s'%("resolve ip",resolve_ip.strip()))
            for key, value in header_obj.items():
                header_list.append('%s:%s'%(key,value))
            header = ("<br/>").join(header_list)

            body = self.content["result"]
            
            log.logger.info('resolve_ip :%s '%(resolve_ip))
            log.logger.info('status_code :%s '%(status_code))
            log.logger.info('header :%s '%(header))
            log.logger.info('body :%s '%(body))

            return status_code,header,body
        except Exception as e:
            log.logger.info('Exception： %s '%(str(e)))
            return None,None,str(e)

    def parse_dig(self):
        try:
            itemlist =  self.result.split("<br/>")
            body = self.result
            status_code = ''
            total_time = ''
            header =''
            if itemlist:
                #fitler_list = ['*','> ','< ','{']
                for index ,value in enumerate(itemlist):
                    if 'ANSWER SECTION' in value:
                        index+=1
                        while itemlist[index]!='':
                            status_code = status_code+itemlist[index]+"<br/>"
                            index+=1
                    if 'Query time' in value:
                        total_time = value.split(':')[1].strip()
            header=status_code
            return status_code,total_time,header,body
        except Exception as e:
            print('Exception:%s '%str(e))
            return None,None,None,str(e)

    def parse_nslookup(self):
        try:
            itemlist =  self.result.split("<br/>")
            body =  self.result
            status_code = ''
            total_time = ''
            header=''
            if itemlist:
                #fitler_list = ['*','> ','< ','{']
                for index ,value in enumerate(itemlist):
                    if 'Non-authoritative answer' in value:
                        index+=1
                        while itemlist[index]!='':
                            status_code = status_code+itemlist[index]+"<br/>"
                            index+=1
                    if 'real' in value or 'user' in value or 'sys' in value:
                        total_time = total_time+"<br/>"+value
            header=status_code
            return status_code,total_time,header,body
        except Exception as e:
            print('Exception:%s '%str(e))
            return None,None,None,str(e)

    def parse_ping(self):
        try:
            itemlist =  self.result.split("<br/>")
            body =  self.result
            status_code = ''
            total_time = ''
            header =''
            if itemlist:
                #fitler_list = ['*','> ','< ','{']
                for index ,value in enumerate(itemlist):
                    if 'statistics' in value:
                        index+=1
                        status_code = itemlist[index]
                        if 'packet' in status_code:
                            lost_rate = float(status_code.split(',')[2].strip().replace("% packet loss",""))
                            if lost_rate > 0:
                                status_code="<span style='color:red'>"+status_code+"</span>"
                        index+=1
                        total_time = itemlist[index]
                        header= status_code+'<br/>'+total_time
                        break;
            return status_code,total_time,header,body
        except Exception as e:
            print('Exception:%s '%str(e))
            return None,None,str(e)
    
    def parse_tcping(self):
        try:
            itemlist = self.result.split("<br/>")
            body =  self.result
            status_code = ''
            total_time = ''
            header =''
            totalcount = 0
            failcount = 0;
            failrate = 0
            passcount = 0
            minvalue = 0
            maxvalue =0 
            avg=0
            loading_time_list = list()
            if itemlist:
                #fitler_list = ['*','> ','< ','{']
                for index ,value in enumerate(itemlist):
                    if 'seq' in value:
                        if 'open' in value:
                            passcount+=1
                            timevalue = float(value.split(']')[1].strip().replace("ms",""))
                            loading_time_list.append(timevalue)
                        else:
                            failcount+=1
                        totalcount+=1

            if totalcount == failcount:
                failrate = 100
            else:
                failrate = round(failcount/totalcount,2)*100

            if passcount >0 and len(loading_time_list)>0:
                minvalue = min(loading_time_list)
                maxvalue = max(loading_time_list)
                avg = round((sum(loading_time_list)/len(loading_time_list)),2)

            if failrate == 100 :       
                status_code = "<span style='color:red'>Ping statistics for {}:{}<br/> {} probes sent.<br/> {} successful, {} failed.  ({} % fail)</span>".format(self.host,self.port,totalcount,passcount,failcount,failrate)
            else:
                status_code = "Ping statistics for {}:{}<br/> {} probes sent.<br/> {} successful, {} failed.  ({} % fail)".format(self.host,self.port,totalcount,passcount,failcount,failrate)

            total_time = "Approximate trip times in milli-seconds:<br/>Minimum = {}ms, Maximum = {}ms, Average = {}ms".format(minvalue,maxvalue,avg)
            header = status_code+"<br>"+total_time
            body = self.result+"<br>"+header
            return status_code,total_time,header,body
        except Exception as e:
            log.logger.info('Exception:%s '%str(e))
            return None,None,None,str(e)

    def parse_mtr(self):
        try:
            body =  '<br/>'.join(self.result)
            header = '<br/>'.join(self.result)
            status_code ="{} count path".format(len(self.result))
            total_time = "{} count path".format(len(self.result))
            return status_code,total_time,header,body
        except Exception as e:
            log.logger.info('Exception:%s '%str(e))
            return None,None,None,str(e)

    def parse_har(self):
        try:
            body = self.result
            status_code =self.content["status_code"]
            total_time= 0
            total_size = 0
            down_link = ""
            if status_code== 200:
                if self.content["load_time"]:
                    total_time = str(round(int(self.content["load_time"]) / 1000,2))
                if self.content["total_size"]:
                    total_size = round(int(self.content["total_size"]) / (1024*1024),2)
                if self.content["url"]:
                    down_link = self.content["url"]
                header = "request: {} ,total size:{} MB,total loading:{}s".format(self.content["requests"],total_size,total_time)
            else:
                header = "status_code: {} ,testing fail, please refresh this node.".format(status_code)
            
            return status_code,total_time,down_link,header,body
        except Exception as e:
            log.logger.info('Exception:%s '%str(e))
            return None,None,None,None,str(e)
