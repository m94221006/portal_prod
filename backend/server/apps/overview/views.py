from django.shortcuts import render
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.http import HttpResponse
from worker.lgoperationapi import lg_operation_api
from mlog import Log
from worker.config import operapihost
import json
from config import expire
log = Log("over","lookglasslog")

# Create your views here.
def index(request):
    return render(request, 'index.html',locals())

def login(request):
    response_data = {}
    try:
        if request.method == "POST":
            api =  lg_operation_api(operapihost)
            username = request.POST['username']
            password = request.POST['password']
            token =  api.get_jwt_token(username,password)

            if token :
                response_data['expire'] = expire
                response_data['token'] = token
                response_data['message'] = "login success" 
                response_data['status_code'] = 200
            else:
                response_data['expire'] = 0
                response_data['token'] = ''
                response_data['message'] = "please login with correct username and password" 
                response_data['status_code'] = 400 
        elif request.method == "GET":
            return render_to_response('registration/Login.html')
        else:
            response_data['token'] = ''
            response_data['message'] = "not support this url path"
            response_data['status_code'] = 403
        return HttpResponse(json.dumps(response_data), content_type="application/json")
    except Exception as e:
        message = "Exception : "+ str(e)
        response_data['message'] = message
        response_data['status_code'] = 408
        return HttpResponse( json.dumps(response_data), content_type="application/json")


def UserInfo(reuqest):
    try:
        username = reuqest.GET['username']
        context_dict ={'username': username}
    except Exception as e:
        message = "Exception : "+ str(e)
        context_dict ={'username': None}
    return render_to_response('registration/UserInfo.html',context_dict)

def download(request):
    file=open('/app/backend/server/django_static/files/User_Guide.pdf','rb')
    response =FileResponse(file)
    response['Content-Type']='application/octet-stream'
    response['Content-Disposition']='attachment;filename="Letron_User_Guide.pdf"'
    return response