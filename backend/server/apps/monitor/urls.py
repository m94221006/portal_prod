from django.conf.urls import url, include

from monitor.views import (index, Config_Detail,Config_Deploy,Heartbeat_Config,instance,allinstance,instance_config,
                          Heartbeat_Instance_Config,Heartbeat_Config_status,Alert_Deploy,Alert_Confg,Recipient_Vertify)


urlpatterns = [
    url(r'index/', index),
    url(r'instance/',instance),
    url(r'allnodes/',allinstance),
    url(r'instance_config/', instance_config),
    url(r'Config_Detail/', Config_Detail),
    url(r'Config_Deploy/', Config_Deploy),
    url(r'^Heartbeat_Config/',Heartbeat_Config),
    url(r'^Heartbeat_Instance_Config/',Heartbeat_Instance_Config),
    url(r'Heartbeat_Config_status/',Heartbeat_Config_status),
    url(r'alert_deploy/', Alert_Deploy),
    url(r'alert_config/', Alert_Confg),
    url(r'recipient_vertify/',Recipient_Vertify),
]
 