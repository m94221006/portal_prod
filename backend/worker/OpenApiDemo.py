#!/usr/bin/python
import datetime
from hashlib import sha256
#from urllib import parse
import urllib




import hmac
import base64
import requests

class OpenApiDemo:
    def getDate(self):
        GMT_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'
        date_gmt = datetime.datetime.utcnow().strftime(GMT_FORMAT)
        return date_gmt

    def getAuth(self, userName, apikey, date):
        signed_apikey = hmac.new(apikey.encode('utf-8'), date.encode('utf-8'), sha256).digest()
        signed_apikey = base64.b64encode(signed_apikey)
        signed_apikey = userName + ":" + signed_apikey.decode()
        signed_apikey = base64.b64encode(signed_apikey.encode('utf-8'))
        return signed_apikey

    def createHeader(self, accept, authStr, date):
        headers = {
            'Date': date,
            'Accept': accept,
            'Content-type': accept,
            'Authorization': 'Basic ' + authStr.decode()
        }
        return headers

    def sendRequest(self, httpUrl, method, httpBodyParams, headers):
        if method.upper() == 'POST':
            resp = requests.post(httpUrl, data=httpBodyParams, headers=headers)
        elif method.upper() == 'GET':
            resp = requests.get(httpUrl, headers=headers)
        self.printResp(resp)
        return resp.json()

    def printResp(self, resp):
        headers_post = dict(resp.headers);
        tmp_str = "statusCode:{}\nDate:{}\nContent-Length:{}\nConnection:{}\nx-cnc-request-id:{}\n\n{}".format(
            resp.status_code,
            headers_post.get('Date'),
            headers_post.get('Content-Length'),
            headers_post.get('Connection'),
            headers_post.get('x-cnc-request-id'),
            resp.text.encode('utf-8'))
        print(tmp_str)


if __name__ == '__main__':
    userName = 'Ryan_mlytics'
    apikey = 'a@exp0lk2019' 
    method = 'GET'
    accept = 'application/json'
    httpHost = "https://open.chinanetcenter.com/vmp"
    httpUri = "/nodes"
    httpGetParams = {
     'regionName':'huanan'
    }
    httpBodyParamsXML=''
    openApiDemo = OpenApiDemo()
    date = openApiDemo.getDate() 
    authStr = openApiDemo.getAuth(userName, apikey, date) 
    headers = openApiDemo.createHeader(accept, authStr, date) 
    httpUrl = httpHost + httpUri + "?" + urllib.parse.urlencode(httpGetParams)
    openApiDemo.sendRequest(httpUrl, method, httpBodyParamsXML, headers)
