from django.urls import re_path
from . import consumers
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
    re_path(r'ws/chat/online/(?P<username>[\w.]+)/$', consumers.onlineConsumer.as_asgi()),  # Changed pattern to include dots
]