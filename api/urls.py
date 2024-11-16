from django.urls import path
from .views import FriendshipAPIView, UserCreateAPIView,GroupChatAPIView
from django.views.generic import TemplateView

urlpatterns = [
    path('items-live/', TemplateView.as_view(template_name='myapp/items.html')),
    path('friendship/', FriendshipAPIView.as_view(), name='friendship-api'),
    path('users/', UserCreateAPIView.as_view(), name='user-create'),
    path('group', GroupChatAPIView.as_view(), name='group-chat'),
]