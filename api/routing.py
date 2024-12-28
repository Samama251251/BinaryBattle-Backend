from django.urls import re_path
from . import consumers
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [

    re_path(r'ws/chat/online/(?P<username>[\w.]+)/$', consumers.onlineConsumer.as_asgi()),  # 
    re_path(r'ws/chat/(?P<room_id>\d+)/$', consumers.ChatConsumer.as_asgi()),
    # re_path(r'ws/challenge/lobby/(?P<challenge_id>\d+)/$', consumers.ChallengeLobbyConsumer.as_asgi()),
    re_path(r'ws/challenge/lobby/(?P<challenge_id>\d+)/(?P<username>[\w.]+)/$', consumers.ChallengeLobbyConsumer.as_asgi()),
]