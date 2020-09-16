from django.conf.urls import url, include

from lookglass.views import (index,index_v2,looking_glass,looking_glass_v2,looking_glass_down,lg_history,
                            lg_history_detail,lg_history_content,lg_task,task_config,lg_task_history,lg_task_instances)

urlpatterns = [
    url(r'index/', index , name='index'),
    url(r'index_v2/', index_v2 , name='index_v2'),
    url(r'looking_glass/',looking_glass),
    url(r'looking_glass_v2/',looking_glass_v2),
    url(r'lg_down/',looking_glass_down),
    url(r'lg_history/',lg_history),
    url(r'lg_history_detail/',lg_history_detail),
    url(r'lg_history_content/',lg_history_content),
    url(r'lg_task/',lg_task),
    url(r'task_config/',task_config),
    url(r'lg_task_history/',lg_task_history),
    url(r'lg_task_instances/',lg_task_instances),

]
