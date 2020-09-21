#  Django celery and channel for letron tool

Topics:
- Environment
- Introduction
- run and testing

## Environment
### package
1. python:3.5
1. django==2.1.2
1. django-celery-beat==1.4.0
1. channels==2.3.1
### Database.
1. postgres.

### MQ
1. rabbitmq
1. redis

## Introduction

### Looking glass ###
This api is to use the JWT Token to make the authentication:
python jwt authentication example: 

```python
apihost = 'https://127.0.0.1:8080/api-token-auth/'
data = {"username": username, "password": password}
header = {"Content-Type": "application/x-www-form-urlencoded"}
res = requests.post(apihost, data=data, headers=header)
token = res.json()['token']
```

### Monitor deploy to node  ###
Once you get the jwt token that you could use to access operation data api.
api get data with jwt token example :
```python
header = {'Authorization':'JWT {}'.format(token),'Content-type':'application/json'}
get_url = "{}api/customer/{}".format(self.apihost,cid)
res = requests.get(get_url, headers=header, timeout=20)
data =  res.json()
```

## Run and Testing?
step 1.build images
  docker-compose build
  
step 2.run service:
  docker-compose up -d

