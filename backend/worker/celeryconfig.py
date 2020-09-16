from kombu.common import Broadcast
#broker_url =  'amqp://guest@104.199.213.33:5673/'
#broker_url ='redis://104.199.213.33:6378/0'
#broker_url ='redis://redis:6379/0'
#result_backend ='redis://redis:6379/0'

broker_url = 'amqp://guest@rabbitmq'
#result_backend = 'redis://:letronlgv2@redis:6379/1'

ignore_result=True
task_serializer = 'json'
task_acks_late = True
timezone = 'Asia/Taipei'
worker_concurrency = 10

#task_queues = (Broadcast('monitor_task'),)
#task_routes ={
#     'worker.worker.task_add': {
#     'queue': 'monitor_task',
#     'exchange': 'monitor_task'
#   }
#}