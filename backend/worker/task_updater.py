''' This class updates the task'''
import os
import sys
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SERVER_DIR = os.path.join(BACKEND_DIR, 'server')
sys.path.insert(0, SERVER_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
import django
django.setup()

from server.asgi import *
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


class TaskUpdater:
    @staticmethod
    def update_ws(room_group_name,msg):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(room_group_name, msg)