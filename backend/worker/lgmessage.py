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

log = Log("lg_message_api","lg_message_api_log")


class lg_message_api(object):
    def __init__(self):
        self.apihost = "http://18.162.81.56:8000/message"

    def send_message(self,message_type,receiverId,content):
        try:
            post_url =  "{}/send".format(self.apihost)
            headers = {'Content-Type': 'application/json'}
            if message_type:
                my_data={'type': message_type,
                        'receiverId': receiverId,
                        'content':content}
                res = requests.post(post_url, headers=headers, data = json.dumps(my_data))
                return res
                
        except Exception as e:
            message =  "Exception : "+ str(e)
            log.logger.info("send_message post :"+message)


if __name__ == '__main__':
    message_type='telegram'
    receiverId = -356754924
    content = "receiverId testing is okay"
    messageapi = lg_message_api()
    messageapi.send_message(message_type,receiverId,content)