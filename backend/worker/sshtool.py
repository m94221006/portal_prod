# -*- coding: UTF-8 -*-

import os
import sys
import subprocess
import timeit
import datetime
import shlex
import paramiko
import config as conf
import socket
import time
import re
from mlog import Log
import requests
from lgnodesapi import lg_nodes_api


log = Log("tool","upgradefilelog")

class sshtool(object):
    def __init__(self,host,port,username,passwd):
        self.output= None
        self.error= None
        self.client=None 
        self.remote_conn = None
        self.host= conf.HOST
        self.username = conf.USERNAME
        self.password = conf.PASSWORD
        self.timeout = float(conf.TIMEOUT)
        self.commands = conf.COMMANDS
        self.pkey = conf.PKEY
        self.port = conf.PORT
        self.uploadremotefilepath = conf.UPLOADREMOTEFILEPATH
        self.uploadlocalfilepath = conf.UPLOADLOCALFILEPATH
        self.downloadremotefilepath = conf.DOWNLOADREMOTEFILEPATH
        self.downloadlocalfilepath = conf.DOWNLOADLOCALFILEPATH

    def connect(self):
        try:
            print("Establishing ssh connection...")
            print("%s,%s,%s,%s"%(self.host,self.username, self.password, self.port))
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            #Connect to the server
            if (self.password == ''):
                private_key = paramiko.RSAKey.from_private_key_file(self.pkey)
                self.client.connect(hostname=self.host, port=self.port, username=self.username,pkey=private_key ,timeout=self.timeout, allow_agent=False, look_for_keys=False)
                print("Connected to the server",self.host)
                self.remote_conn = self.client.invoke_shell()

            else:
                self.client.connect(hostname=self.host, port=self.port,username=self.username,password=self.password,timeout=self.timeout, allow_agent=False, look_for_keys=False)    
                print("Connected to the server",self.host)
                self.remote_conn = self.client.invoke_shell()

        except paramiko.AuthenticationException:
            print("Authentication failed, please verify your credentials")
            return False
        except paramiko.SSHException as sshException:
            print("Could not establish SSH connection: %s" % sshException)
            return False
        except socket.timeout as e:
            print("Connection timed out")
            return False
        except Exception as e:
            print('\nException in connecting to the server')
            print('PYTHON SAYS:',e)
            self.client.close()
            return False
        return True

    def exec_command(self,command):
        self.output = None
        try:
            if self.client:
                print("Executing command --> {}".format(command))
                stdin, stdout, stderr = self.client.exec_command(command,get_pty=True)
                while True:
                    nextline = stdout.readline()
                    return nextline.strip().encode('utf-8')

                #stand_result = stdout.read().decode('utf-8')
                #error_result =  stderr.read().decode('utf-8')
                #self.output = stand_result
                #self.error = error_result
                #return stdin, stdout, stderr

            else:
                print("Could not establish SSH connection")
                return False   
        except socket.timeout as e:
            print("Command timed out.", command)
            self.client.close()
            return False                
        except paramiko.SSHException:
            print("Failed to execute the command!",command)
            self.client.close()
            return False               
        return True

    def exec_commands(self,commands):
        self.output = None
        try:
            if self.client:
                for command in commands:
                    print("Executing command --> {}".format(command))
                    stdin, stdout, stderr = self.client.exec_command(command,timeout=10)
                    self.output = stdout.read()
                    self.error = stderr.read()
                    if self.error:
                        print("Problem occurred while running command:"+ command + " The error is " + self.error)
                        return False
                    else:    
                        print("Command execution completed successfully",command)
                    self.client.close()
            else:
                print("Could not establish SSH connection")
                return False   
        except socket.timeout as e:
            print("Command timed out.", command)
            self.client.close()
            return False                
        except paramiko.SSHException:
            print("Failed to execute the command!",command)
            self.client.close()
            return False               
        return True

    
    def write_command(self, command,timeout):
        try:
            if(self.client):
                self.remote_conn.send("%s\n"%(command))
                time.sleep(timeout)
                self.output = str(self.remote_conn.recv(20000))
                return True
        except Exception as ex:
            print("[write_command]write command fail:%s "%(str(ex)))
            self.client.close()
            return False

    def write_command_match(self,command,timeout,result):
         try:
            if(self.client):
                self.remote_conn.send((command + "\n").encode('ascii'))
                time.sleep(timeout)
                self.output = str(self.remote_conn.recv(20000))
                print(self.output)
                match_result =self.__Patern_Match(result, self.output)
                return match_result
         except Exception as ex:
             print("[write_multip_command_match]write command fail:%s "%(str(ex)))
             return False

    def shell_message(self):
        message =""
        if(self.client):
            message =  str(self.remote_conn.recv(20000))
        return message

    def upload_file(self,uploadlocalfilepath,uploadremotefilepath):
        try:
            if self.connect():
                ftp_client= self.client.open_sftp()
                ftp_client.put(uploadlocalfilepath,uploadremotefilepath)
                ftp_client.close() 
                self.client.close()
            else:
                print("Could not establish SSH connection")
                return False  
        except Exception as e:
            print('\nUnable to upload the file to the remote server',uploadremotefilepath)
            print('PYTHON SAYS:',e)
            ftp_client.close()
            self.client.close()
            return False  
        return False  

    def download_file(self,downloadremotefilepath,downloadlocalfilepath):
        try:
            if self.connect():
                ftp_client= self.client.open_sftp()
                ftp_client.get(downloadremotefilepath,downloadlocalfilepath)
                ftp_client.close()  
                self.client.close()
            else:
                print("Could not establish SSH connection")
                result_flag = False  
        except Exception as e:
            print('\nUnable to download the file from the remote server',downloadremotefilepath)
            print('PYTHON SAYS:',e)
            result_flag = False
            ftp_client.close()
            self.client.close()
        
        return result_flag
    

    def __Patern_Match(self,pattern,text):
        if '&&' in pattern:
            patterns = pattern.split("&&")
            for pat in patterns:
                p = re.compile(pat)
                match = p.search(text)
                if (match == None):
                    return False
            return True
        else:
           p = re.compile(pattern)
           match = p.search(text)
           if (match == None):
               return False
           else:
               return True

def copy_file_from_remote(ssh_tool,monitor_name,monitor_ip,remote_ip,remote_folder,local_folder,file_name,file_size,file_md5):
    remote_file_path = "%s%s"%(remote_folder,file_name)
    local_file_path = "%s%s"%(local_folder,file_name)

    check = check_file(ssh_tool,local_folder,file_name)
    log.logger.info("[copy_file_from_remote]%s:%s check_file result : %s"%(monitor_name,monitor_ip,stringify(check)))
    if check == True:
        file_check = check_file_size(ssh_tool,local_file_path,file_size)
        log.logger.info("[copy_file_from_remote]%s:%s check_file_size result : %s"%(monitor_name,monitor_ip,stringify(file_check)))
        md5_check = check_file_md5(ssh_tool,local_file_path,file_md5)
        log.logger.info("[copy_file_from_remote]%s:%s check_file_md5 result : %s"%(monitor_name,monitor_ip,stringify(md5_check)))
        if file_check and md5_check:
            check = True
        else:
            check = False
    if check == False:
        log.logger.info("[copy_file_from_remote]%s:%s start to scp %s from remote server."%(monitor_name,monitor_ip,file_name))
        check =  scp_file(ssh_tool,remote_ip,remote_file_path,local_folder,file_name)
        if check == True:
            file_check = check_file_size(ssh_tool,local_file_path,file_size)
            log.logger.info("[upgrade_heartbeat]run %s:%s check_file_md5 result : %s"%(monitor_name,monitor_ip,stringify(file_check)))
            md5_check = check_file_md5(ssh_tool,local_file_path,file_md5)
            log.logger.info("[upgrade_heartbeat]run %s:%s check_file_size result : %s"%(monitor_name,monitor_ip,stringify(md5_check)))
            if file_check and md5_check:
                check = True
            else:
                check = False
    return check

def check_file(ssh_tool,filepath,filename):
     command = "ls -altr %s"%(filepath)
     result =  ssh_tool.write_command_match(command,5,filename)
     return result

def check_file_md5(ssh_tool,filepath,md5):
    command = "md5sum %s"%(filepath)
    result =  ssh_tool.write_command_match(command,5,md5)
    return result

def check_file_size(ssh_tool,filepath,filesize):
    command = "ls -l %s | cut -d ' ' -f5"%(filepath)
    result =  ssh_tool.write_command_match(command,5,filesize)
    return result

def check_software_version(ssh_tool,command,version_name):
     result =  ssh_tool.write_command_match(command,5,version_name)
     return result

def check_container(ssh_tool,container_name):
     command = 'docker ps'
     result =  ssh_tool.write_command_match(command,5,container_name)
     return result

def check_image(ssh_tool,image_name,tag):
    command= 'docker images %s'%(image_name)
    result =  ssh_tool.write_command_match(command,5,tag)
    return result

def run_container(ssh_tool,run_command,container_name):
    result =  ssh_tool.write_command(run_command,5)
    if result:
        result = check_container(ssh_tool,container_name)
    return result 

def start_container(ssh_tool,container_name):
    command = 'docker start %s'%(container_name)
    result =  ssh_tool.write_command(command,5)
    if result:
        result = check_container(ssh_tool,container_name)
    return result 

def stop_container(ssh_tool,container_name):
    command = 'docker stop %s'%(container_name)
    result =  ssh_tool.write_command(command,5)
    if result:
        result = check_container(ssh_tool,container_name)
        if result == False:
            result = True
        else:
            result =False
    return result 

def update_heartbeat(ssh_tool,verion):
    upgrade_command = 'docker stop letron_heartbeat && cp -rf /home/ubuntu/heartbeat /opt/heartbeat/ && docker start letron_heartbeat'
    if ssh_tool.write_command(upgrade_command,20):
        check_command ="docker logs --tail 100 letron_heartbeat | grep 'heartbeat; Version:'"
        check =  ssh_tool.write_command_match(check_command,5,verion)
        return check

def git_pull_code(ssh_tool,folder_path,folder_name,code_version,pull_message,check_file_path,check_md5):
    command = "md5sum %s"%(check_file_path)
    result =  ssh_tool.write_command_match(command,5,check_md5)
    if result ==  False:
        command = 'cd %s'%(folder_path)
        result =  ssh_tool.write_command_match(command,5,folder_name)
        if result == True:
            if code_version :
                command ='git pull %'%(code_version)
            else:
                command = 'git pull'
        result =  ssh_tool.write_command_match(command,5,pull_message)
        if result ==  True:
            command = "md5sum %s"%(check_file_path)
            result =  ssh_tool.write_command_match(command,5,check_md5)
    return result         

def curl_check_service(ssh_tool):
    log.logger.info("[deploy lg]container already running, start to check site")
    command ='curl http://127.0.0.1:5000/'
    check =  ssh_tool.write_command_match(command,5,"body")
    if check == True:
        log.logger.info("[deploy lg]finish deploy")
    return check

def scp_file(ssh_tool,remote_ip,remoter_path,localfloder,filename):
    command ='scp -P 20022 root@%s:%s %s'%(remote_ip,remoter_path,localfloder)
    check =  ssh_tool.write_command(command,3)
    message =ssh_tool.output
    if 'yes' in message:
        command = 'yes'
        check =  ssh_tool.write_command_match(command,3,"password")
        command = 'Ryan_mlytics@2019'
        check =  ssh_tool.write_command(command,3)
    elif 'password' in message:
        command = 'Ryan_mlytics@2019'
        check =  ssh_tool.write_command(command,3)
    else:
        check = False

    message = ssh_tool.output
    timer_num = 0
    if 'ETA' in message:
        while timer_num <=100:
            if '100%' in message:
                log.logger.info("[deploy lg]copy %s completed"%(filename))
                check= True
                break
            elif 'ETA' in message and '100%' not in message:
                log.logger.info("[deploy lg]%s"%(message))
                time.sleep(5)
                timer_num +=1
                message = ssh_tool.shell_message()
                check= False
    else:
        check = False
    return check

def deploy_remote_file(host_ip):
    port = '20022'
    ssh_tool = sshtool("","","","")
    ssh_tool.host = host_ip
    ssh_tool.port = port
    timer_num = 0
    check =  False
    log.logger.info("[deploy lg]start to connect.")

    if ssh_tool.connect():
        log.logger.info("[deploy lg]start to check.")
        command ='docker ps'
        check =  ssh_tool.write_command_match(command,10,"looking_glass_agent")
        if check == True:
            log.logger.info("[deploy lg]container already running, start to check site")
            command ='curl http://127.0.0.1:5000/'
            check =  ssh_tool.write_command_match(command,10,"body")
            if check == True:
                log.logger.info("[deploy lg]aleady deploy")
        if check == False:
            


            command = 'git clone https://oauth2:7afYNZc5G8-55sd6okcg@gitlab.com/letronsrs/looking-glass-agent.git /opt/looking-glass-agent/'
            check =  ssh_tool.write_command_match(command,30,"Checking connectivity... done")
            if 'already exists' in ssh_tool.output:
                result = True

            if check== True:
                command= 'docker pull letronsrs/looking_glass_agent:1.0.7'
                check =  ssh_tool.write_command_match(command,30,"Pulling from")
                if 'Image is up to date' in ssh_tool.output:
                    check =True
                    log.logger.info("[deploy lg]image had been existed")
                else:
                    pull_message = ssh_tool.shell_message()
                    while timer_num <=20:
                        if 'Downloaded newer image' in pull_message:
                            log.logger.info("[deploy lg]looking_glass_agent:1.0.7 image pull completed")
                            check= True
                            break
                        else:
                            time.sleep(5)
                            timer_num +=1
                            pull_message = ssh_tool.shell_message()
                            check= False

            if check== True:
                command = "ls -altr /opt/looking-glass-agent/"
                result =  ssh_tool.write_command_match(command,20,"api")
            if check== True:
                command ='docker images'
                result =  ssh_tool.write_command_match(command,5,"letronsrs/looking_glass_agent")

            if check == True:
                log.logger.info("[deploy lg]start to run")
                command = 'docker run -idt --name looking_glass_agent -v /opt/looking-glass-agent/api:/usr/app/api -p 5000:5000 letronsrs/looking_glass_agent:1.0.7'
                check =  ssh_tool.write_command(command,10)
                if result == True:
                    log.logger.info("[deploy lg]start to check")
                    command ='docker ps'
                    check =  ssh_tool.write_command_match(command,10,"looking_glass_agent")
                    if check == True:
                        log.logger.info("[deploy lg]container already running, start to check site")
                        command ='curl http://127.0.0.1:5000/'
                        check =  ssh_tool.write_command_match(command,10,"body")
                        if check == True:
                           log.logger.info("[deploy lg]finish deploy")
        else:
            ssh_tool.client.close()

        ssh_tool.client.close()
        return check

def deploy_from_local_file(host_ip):
    try:
        container_name = 'looking_glass_agent'
        image_name = 'letronsrs/looking_glass_agent'
        image_tag = '1.0.7'
        code_file_path = '/opt/looking-glass-agent/api/'
        code_file_name = 'api_tools.py'
        remote_ip = '121.32.236.50'
        remote_folder = '/home/ubuntu/'
        local_folder = '/home/ubuntu/'
        port = '20022'
        ssh_tool = sshtool("","","","")
        ssh_tool.host = host_ip
        ssh_tool.port = port
        timer_num = 0
        check =  False
        log.logger.info("[deploy lg]start to connect.")
        if ssh_tool.connect():
            if check_container(ssh_tool,container_name):
                log.logger.info("[deploy lg]api service had been ready.")
                check = curl_check_service(ssh_tool)
            else:
                image_check = check_image(ssh_tool,image_name,image_tag)
                file_check = check_file(ssh_tool,code_file_path,code_file_name)
                if image_check and file_check:
                    run_command = 'docker run -idt --name looking_glass_agent -v /opt/looking-glass-agent/api:/usr/app/api -p 5000:5000 letronsrs/looking_glass_agent:1.0.7'
                    check = run_container(ssh_tool,run_command,container_name)
                    log.logger.info("[deploy lg]run %s:%s finish result : %s"%(image_name,image_tag,stringify(check)))
                    check = curl_check_service(ssh_tool)
                else:
                    if file_check == False:
                        file_name = "looking-glass-agent.tar.gz"
                        tarfile_path ='/home/ubuntu/%s'%(filename)
                        dest_path = '/opt/'
                        if copy_file_from_remote(ssh_tool,remote_ip,remote_folder,local_folder,file_name):
                            file_check = tar_file_to_folder(ssh_tool,tarfile_path,dest_path,code_file_path,code_file_name)
                    if image_check == False:
                        file_name = "looking_glass_agent_107.tar"
                        dockertar_file = '/home/ubuntu/%s'%(filename)
                        if copy_file_from_remote(ssh_tool,remote_ip,remote_folder,local_folder,file_name):
                            image_check = deploy_docker_image_from_file(ssh_tool,dockertar_file,image_name,image_tag)
                    if image_check and file_check:
                        run_command = 'docker run -idt --name looking_glass_agent -v /opt/looking-glass-agent/api:/usr/app/api -p 5000:5000 letronsrs/looking_glass_agent:1.0.7'
                        check = run_container(ssh_tool,run_command,container_name)
                        log.logger.info("[deploy lg]run %s:%s finish result : %s"%(image_name,image_tag,stringify(check)))
                        check = curl_check_service(ssh_tool)
                    else:
                        log.logger.info("[deploy lg]run %s:%s finish result : %s"%(image_name,image_tag,stringify(False)))
        ssh_tool.client.close()
        return check
    except Exception as e:
        log.logger.error("[deploy lg]error : %s"%(str(e)))
        ssh_tool.client.close()

def tar_file_to_folder(ssh_tool,tarfile_path,dest,check_filepath,check_filename):
    command ='tar zxvf %s -C %s'%(tarfile_path,dest)
    check =  ssh_tool.write_command_match(command,10,check_filename)
    log.logger.info("[deploy lg]tar %s to %s finish result : %s"%(tarfile_path,dest,stringify(check)))
    if check == True:
        check = check_file(ssh_tool,check_filepath,check_filename)
        log.logger.info("[deploy lg]check %s to %s finish result : %s"%(dest,check_filename,stringify(check)))
    return check

def deploy_docker_image_from_file(ssh_tool,docker_tar_file,image_name,tag):
    command = 'docker images %s'%(image_name)
    check =  ssh_tool.write_command_match(command,3,tag)
    if check ==  False:
        loading_start_message ='Loading layer'
        loading_done_message ='Loaded image'
        command = 'docker load < %s'%(docker_tar_file)
        check =  ssh_tool.write_command(command,10)
        message = ssh_tool.output
        timer_num = 0
        if loading_start_message in message:
            while timer_num <=30:
                if loading_done_message in message:
                    log.logger.info("[deploy lg]load %s done"%(docker_tar_file))
                    check= True
                    break
                elif loading_start_message in message and loading_done_message not in message:
                    log.logger.info("[deploy lg]%s"%(message))
                    time.sleep(5)
                    timer_num +=1
                    message = ssh_tool.shell_message()
                    check= False
        else:
            check = False
        
        command = 'docker images %s'%(image_name)
        check =  ssh_tool.write_command_match(command,3,tag)
        log.logger.info("[deploy lg]load %s:%s finish result : %s"%(image_name,tag,stringify(check)))
    return check

def stringify(value):
    return ('Nothing' if value is None else
            'pass' if value is True else
            'fail' if value is False else
            str(value))

def scp_file_from_remote():
    log.logger.info("[deploy lg]Start to get nodes info")
    letron_api = OpenAPI()
    node_dict = letron_api.sendRequest('GET', "")
    for k, v in node_dict.items():
        server=v[0]
        ip = v[1]
        monitor_name = v[2]
        region = v[3]
        isp = v[4]
        log.logger.info("[deploy lg]%s - %s scp_file_from_remote"%(server,ip))
        remote_ip = '121.32.236.50'
        remote_folder = '/opt/mlytics/'
        local_folder = '/home/ubuntu/'
        file1_name = 'dockercompose-prod-waver-dev.tgz'
        file2_name = 'looking-glass-agent-source-108.tar.gz'

        file1_md5='5dbb9ad0b59b1ee55adaa9f2dfd8ea83'
        file2_md5='bdc764071fe671b44ba77fc9b6989e33'
        file1_size = '9493089'
        file2_size='50560759'
        image_name = 'letronsrs/looking_glass_agent'
        image_tag=' 1.0.8'
        port = '20022'
        ssh_tool = sshtool("","","","")
        ssh_tool.host = ip
        ssh_tool.port = port
        timer_num = 0
        check =  False
        log.logger.info("[deploy lg]start to connect.")
        log.logger.info("[scp_file_from_remote]%s - %s "%(monitor_name,ip))
        if region =='华南':
            if ssh_tool.connect():
                log.logger.info("[scp_file_from_remote]%s - %s upgrade heartbeat"%(monitor_name,ip))
                copy_file_from_remote(ssh_tool,monitor_name,ip,remote_ip,remote_folder,local_folder,file1_name,file1_size,file1_md5)
                #docker_tar_file = local_folder + file1_name
                #deploy_docker_image_from_file(ssh_tool,docker_tar_file,image_name,image_tag)
                #copy_file_from_remote(ssh_tool,monitor_name,ip,remote_ip,remote_folder,local_folder,file2_name,file2_size,file2_md5)
                ssh_tool.client.close()

def check_letron_lg():
    log = Log("tool","checklog")

    log.logger.info("[deploy lg]Start to get nodes info")
    letron_api = OpenAPI()
    node_dict = letron_api.sendRequest('GET', "")
    for k, v in node_dict.items():
        server=v[0]
        ip = v[1]
        monitor_name = v[2]
        region = v[3]
        isp = v[4]
        url = "http://%s:5000/curl"%(ip)
        #my_data={'domain':'https://www.baidu.com/'}

        my_data={'host':'-ivk https://www.tma78.com/','domain':'','port':'','ip':''}
        try:
            
            r =  requests.get(url, params = my_data,timeout=20)
            print()
            #r = requests.post(url, data = my_data, timeout=None)
            if r.status_code == 200:
                log.logger.info("[deploy lg]%s - %s finish to site check result : %s"%(server,ip,'Pass'))
            else:
                log.logger.info("[deploy lg]%s - %s finish to site check result : %s"%(server,ip,'Fail'))
        except Exception as e:
            log.logger.info("[deploy lg]%s - %s finish to site check result : %s"%(server,ip,'Fail'))

def deploy_letron_lg():
    log = Log("tool","deploylog")
    log.logger.info("[deploy lg]Start to get nodes info")
    letron_api = OpenAPI()
    node_dict = letron_api.sendRequest('GET', "")
    filelist = ["looking-glass-agent.tar.gz","looking_glass_agent_107.tar"]
    for k, v in node_dict.items():
        server=v[0]
        ip = v[1]
        monitor_name = v[2]
        region = v[3]
        isp = v[4]
        log.logger.info("[deploy lg]%s - %s deploy_from_local_file"%(server,ip))
        result = deploy_from_local_file(ip)
        log.logger.info("[deploy lg]%s - %s finish to deploy_from_local_file result : %s"%(server,ip,result))
           
def upgrade_heartbeat(ssh_tool):
    try:
        remote_ip = '121.32.236.50'
        remote_path = '/home/ubuntu/'
        local_path = '/home/ubuntu/'
        file_name = 'heartbeat'
        md5 = '4d2126430e64a95a12b1b98f46fd4810'
        file_size = '66733619'
        upgrade_path = '/opt/heartbeat/'
        heartbeat_version ='7.2.1'
        check =  False
        check = copy_file_from_remote(ssh_tool,monitor_name,ip,remote_ip,remote_path,local_path,file_name,file_size,md5)
        if check:
            check_version_command ='/opt/heartbeat/heartbeat version'
            check = check_software_version(ssh_tool,check_version_command,heartbeat_version)
            log.logger.info("[upgrade_heartbeat]check_software_version(%s)result :%s(%s)"%(heartbeat_version,ssh_tool.output,stringify(check)))
            if check ==False:
                log.logger.info("[upgrade_heartbeat]need to upgrade from %s to %s."%(ssh_tool.output,heartbeat_version))
                check = update_heartbeat(ssh_tool,heartbeat_version)
                log.logger.info("[upgrade_heartbeat]upgrade result:%s."%(stringify(check)))
                check = check_software_version(ssh_tool,check_version_command,heartbeat_version)
                log.logger.info("[upgrade_heartbeat]check_software_version(%s)result :%s(%s)"%(heartbeat_version,ssh_tool.output,stringify(check)))
    except Exception as e:
        log.logger.info("[upgrade_heartbeat]exception : %s"%(str(e)))


def restart_waver_service(host_ip):
    try:
        container_name = 'waver:v2.5.22'
        file_name = 'docker-compose.yaml'
        file_folder = '/opt/mlytics/waver_2019_11_27/'
        port = '20022'
        ssh_tool = sshtool("","","","")
        ssh_tool.host = host_ip
        ssh_tool.port = port
        timer_num = 0
        check =  False
        log.logger.info("[restart_waver_service]start to connect.")
        if ssh_tool.connect():
            container_check = check_container(ssh_tool,container_name)
            file_check = check_file(ssh_tool,file_folder,file_name)
            log.logger.info("[restart_waver_service]%s container_check result : %s"%(host_ip,stringify(container_check)))
            log.logger.info("[restart_waver_service]%s file_check result : %s"%(host_ip,stringify(file_check)))
            if container_check and file_check:
                command = 'docker-compose -f /opt/mlytics/waver_2019_11_27/docker-compose.yaml down && docker-compose -f /opt/mlytics/waver_2019_11_27/docker-compose.yaml up -d'
                check =  ssh_tool.write_command_match(command,20,'Creating waver-prod')
                log.logger.info("[restart_waver_service]%s result : %s"%(host_ip,stringify(check)))
            else:
                log.logger.info("[restart_waver_service]%s file check  and container_check result : fail"%(host_ip))
            ssh_tool.client.close()
        return check
    except Exception as e:
        log.logger.error("[deploy lg]error : %s"%(str(e)))
        ssh_tool.client.close()

if __name__ == '__main__':
   log.logger.info("[deploy lg]Start to get nodes info")
   nodes_api = lg_nodes_api('','','')
   node_list = nodes_api.get_local_api().json()

   for node in node_list:
        region_name=node['region_name']
        chinese_name=node['chinese_name']
        host_ip = node['host_ip']
        print(region_name+":"+chinese_name+":"+host_ip)
        port = '20022'
        ssh_tool = sshtool("","","","")
        ssh_tool.host = host_ip
        ssh_tool.port = port
        if ssh_tool.connect():
            log.logger.info("[%s]could connect"%(host_ip))

            #result =  ssh_tool.write_command_match("df -P | awk '0+$5 >= 50 {print}'",10,'ubuntu--vg-root')
            #if result == True:
            #    log.logger.info("[%s]check disk result then 50 : %s"%(host_ip,ssh_tool.output))


#ssh_tool = sshtool("","","","")
#ssh_tool.host = '163.171.211.192'
#ssh_tool.port = '20022'

 # customer_name = 'SSM'
 #hostname = '163.171.211.192'
 #port = 20022
 #username= conf.USERNAME
 #password = conf.PASSWORD
 #command ='ping 8.8.8.8'
 #ssh = paramiko.SSHClient()
 #ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
 #ssh.connect(hostname=hostname, username=username, password=password,port=port)
                # 務必要加上get_pty=True,否則執行命令會沒有權限
#stdin, stdout, stderr = ssh.exec_command(command, get_pty=True)
#while True:
    #nextline = stdout.readline()
    #print(nextline.strip().encode('utf-8')) # 發送消息到客戶端
                    # 判斷消息爲空時,退出循環
    #if nextline == "" and nextline != None:
    #    break

 #     if result:
 #         output = ssh_tool.output
 #         itemlist = output.strip().split("\n")
 #         print(len(itemlist))
 #         for item in itemlist:
 #             command = 'cat /opt/heartbeat/monitors.d/%s'%(item)
 #             print(command)
 #             result =  ssh_tool.exec_command(command)
 #             output = ssh_tool.output.strip()
 #             print(output)

'''
    log.logger.info("[deploy lg]Start to get nodes info")
    letron_api = OpenAPI()
    node_dict = letron_api.sendRequest('GET', "")
    for k, v in node_dict.items():
        server=v[0]
        ip = v[1]
        monitor_name = v[2]
        region = v[3]
        isp = v[4]
        command = "echo 'sshd:210.61.181.67,121.14.16.28' >> /etc/hosts.allow"
        if ip!='121.14.16.28' or ip!='210.61.181.67':
                port = '20022'
                ssh_tool = sshtool("","","","")
                ssh_tool.host = ip
                ssh_tool.port = port
                if ssh_tool.connect():
                    result =  ssh_tool.write_command_match("cat /etc/hosts.allow | grep '210.61.181.67'",10,'sshd')
                    log.logger.info("[deploy lg]check ssh %s:%s finish result : %s"%(monitor_name,ip,stringify(result)))
                    if result == False:
                        result =  ssh_tool.write_command(command,5)
                        log.logger.info("[deploy lg]enable ssh %s:%s finish result : %s"%(monitor_name,ip,stringify(result)))
                        result =  ssh_tool.write_command_match("cat /etc/hosts.allow | grep '210.61.181.67'",10,'sshd')
                        log.logger.info("[deploy lg]check ssh %s:%s finish result : %s"%(monitor_name,ip,stringify(result)))
                        ssh_tool.client.close()
    log.logger.info("[deploy lg]Start to get nodes info")
    letron_api = OpenAPI()
    node_dict = letron_api.sendRequest('GET', "")
    for k, v in node_dict.items():
        server=v[0]
        ip = v[1]
        monitor_name = v[2]
        region = v[3]
        isp = v[4]
        folder_path = '/opt/looking-glass-agent/'
        folder_name = 'looking-glass-agent'
        code_version=''
        pull_message =''
        check_file_path = '/opt/looking-glass-agent/api/api_tools.py'
        check_md5 = '7d3d9ce31da04d9c5e066f7bf120e4ad'
        port = '20022'
        ssh_tool = sshtool("","","","")
        ssh_tool.host = ip
        ssh_tool.port = port
        timer_num = 0
        check =  False
        if region != '亞太':
            log.logger.info("[upgrade_lg]%s - %s upgrade lg"%(monitor_name,monitor_name))
            if ssh_tool.connect():
                result = git_pull_code(ssh_tool,folder_path,folder_name,code_version,pull_message,check_file_path,check_md5)
                log.logger.info("[deploy lg]upgrade %s:%s pull code result : %s"%(monitor_name,ip,stringify(result)))
                if result == True:
                    container_vesion = 'looking_glass_agent:1.0.8'
                    result = check_container(ssh_tool,container_vesion)
                    log.logger.info("[deploy lg]  %s:%s check container result : %s"%(monitor_name,ip,stringify(result)))
                    if result == False:
                        command = 'docker stop looking_glass_agent && docker rm looking_glass_agent && docker-compose -f /opt/looking-glass-agent/docker-compose.yml up -d'
                        result =  ssh_tool.write_command_match(command,20,'done')
                        log.logger.info("[deploy lg]  %s:%s upgrade container result : %s"%(monitor_name,ip,stringify(result)))
                        if result == True:
                            result = check_container(ssh_tool,container_vesion)
                            if result == True:
                                result = curl_check_service(ssh_tool)
                    else:
                         result = curl_check_service(ssh_tool)       
                log.logger.info("[deploy lg]upgrade %s:%s finish result : %s"%(monitor_name,ip,stringify(result)))
                ssh_tool.client.close()
'''