from django.urls import path
from .views import FriendshipAPIView, UserCreateAPIView,GroupChatAPIView,TestAPIView,FriendRequestAPIView,ChallengeAPIView,ChallengeParticipationAPIView

urlpatterns = [
    path('friendship', FriendshipAPIView.as_view(), name='friendship-api'),
    path('users', UserCreateAPIView.as_view(), name='user-create'),
    path('group', GroupChatAPIView.as_view(), name='group-chat'),
    path('test/',TestAPIView.as_view(),name="test"),
    path('friendRequests',FriendRequestAPIView.as_view(),name="friend-requests"),
    path('challenges/create', ChallengeAPIView.as_view()),
    path('challenges/join', ChallengeParticipationAPIView.as_view()),
    path('challenges/<int:challenge_id>/', ChallengeAPIView.as_view(), name='challenge-detail'),
]
