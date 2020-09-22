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
 Looking Glass provides following tools for real-time testing from 100+ locations.
  1. curl domain
  1. Tcping ip
  1. ping ip
  1. nslookup dns
  1. dig dns
  1. MTR ip
  1. HAR domain
  1. websocket domain
  
 Introduction:
 https://www.letrontech.com/looking-glass-testing-tool
 
 could see the demo video.
 
 Testing Site:
 Url: http://demo.letronlab.com:8089/
 Username: demouser
 Password: d@m02020!
 
 example:
 curl/har http://www.baidu.com/ to test

## Run and Testing?
step 1.build images
  docker-compose build
  
step 2.run service:
  docker-compose up -d

