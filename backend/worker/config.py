import os


#BROKER_URL = 'redis://104.199.213.33:6378/0'
#REDIS_URL = '104.199.213.33' #websocket redis result
#REDIS_PORT = '6378'

#DATABASE_URL =  '104.199.213.33'
#DATABASE_NAME =  'simple_tasks'
#DATABASE_USER = 'postgres'
#DATABASE_PASS =  '1234'
#DATABASE_PORT =  '5433'
#DJANGO_DEBUG =False
#DJANGO_DEBUG = os.environ.get('DJANGO_DEBUG', True)
#HOST_CONFIG = {'5243':0,'lbdzw':1,'nxsk8':2,'7cxbx':3}

#BROKER_URL = 'redis://104.199.213.33:6378/0'

REDIS_URL = 'redis' #websocket redis result
REDIS_PORT = '6379'
REDIS_AUTH ='letronlgv2'
WS_IP = '220.242.161.13'
WS_PORT ='9000'
CUSTOMER='Letron'
USERID = 1


DATABASE_URL =  'postgres'
DATABASE_NAME =  'letron_tasks'
DATABASE_USER = 'letron'
DATABASE_PASS =  'l@tr0n2019'
DATABASE_PORT =  '5432'
DJANGO_DEBUG =False
#DJANGO_DEBUG = os.environ.get('DJANGO_DEBUG', True)


#Server credential details needed for ssh 
HOST='Enter your host details here'
USERNAME='root'
PASSWORD='Ryan_mlytics@2019'
PORT = 20022
TIMEOUT = 10

#.pem file details
PKEY = 'Enter your key filename here'

#Sample commands to execute(Add your commands here)
COMMANDS = ['ls;mkdir sample']

#Sample file locations to upload and download
UPLOADREMOTEFILEPATH = '/etc/example/filename.txt'
UPLOADLOCALFILEPATH = 'home/filename.txt'
DOWNLOADREMOTEFILEPATH = '/etc/sample/data.txt'
DOWNLOADLOCALFILEPATH = 'home/data.txt'

node_api_token ='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJhM2E0MzkxNy1hZWY0LTRmMjctODM1Yy0xNjE3OTdjNjBmZGMiLCJpZGVudGl0eSI6ImFkbWluIiwibmJmIjoxNTczNDU4ODQ1LCJpYXQiOjE1NzM0NTg4NDUsImZyZXNoIjpmYWxzZSwidHlwZSI6ImFjY2VzcyJ9.5r1_2GsEjgUiNdTIq2C6191WfwNVOPi1LqbgcdWrn2k'


### lg operaiton api ##
env = 'dev'
operapihost ='220.242.161.13'
historyapihost = '54.169.156.33'
historyapiport='5555'

nodehtapihost = '54.169.156.33'
nodehtapiport = '5001'
#operapihost = '192.168.1.135'
operapiport = 8090
admin='letron'
adminpw ='l@tr0n2019'
#operapiport = 8080
if env == 'prod':
    operapihost = '18.162.81.56'


## user login ##
expire = 1800000  ## 30 minutes
