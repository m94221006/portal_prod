from django.conf.urls import url, include

from api.views import runmonitor,runtool,getmonitorlist


urlpatterns = [
    url(r'runmonitor/',runmonitor),
    url(r'runtool/',runtool),
]
