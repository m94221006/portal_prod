from django.conf.urls import url, include

from overview.views import index,download,login,UserInfo
urlpatterns = [
    url(r'index/', index),
    url(r'userinfo/',UserInfo),
    url(r'^login/',login),
    url(r'^download/', download),
]