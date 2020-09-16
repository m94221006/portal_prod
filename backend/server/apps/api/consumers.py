from channels.generic.websocket import AsyncWebsocketConsumer,WebsocketConsumer
import json
import logging
from asgiref.sync import async_to_sync

logger = logging.getLogger('djangows')


class ToolsConsumer(WebsocketConsumer):
  
    def connect(self):
        self.name = self.scope['url_route']['kwargs']['name']
        self.group_name = 'lg_%s' %  self.name
        logger.info('%s connect'%(self.group_name))

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name ,
            self.channel_name
        )
        logger.info('%s disconnect'%(self.group_name))
    def receive(self, text_data):
          pass

    def server_result_message(self, event):
        self.send(json.dumps(event))


    def play_result_message(self, event):
        self.send(json.dumps(event))

    def server_close(self, close_code):
       logger.info('%s close'%(self.group_name))
       self.close()
   
class MonitorConsumer(WebsocketConsumer):

    def connect(self):
        # One group name for all clients: 'tasks'
        self.name = self.scope['url_route']['kwargs']['name']
        self.group_name = 'mt_%s' %  self.name
        logger.info('%s connect'%(self.group_name))
        
        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

        self.accept()


    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name ,
            self.channel_name
        )

    def receive(self, text_data):
        pass

  
    def monitor_query_message(self, event):
        # Send message to channel
        logger.info('groupname: %s send:%s'%(self.group_name,event))

        self.send(json.dumps(event))
