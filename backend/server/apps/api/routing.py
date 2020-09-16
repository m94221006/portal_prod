from django.conf.urls import url

from . import consumers

websocket_urlpatterns = [
    url(r'^ws/monitors/(?P<name>[^/]+)/$',consumers.MonitorConsumer),
    url(r'^ws/tools/(?P<name>[^/]+)/$',consumers.ToolsConsumer),
]
