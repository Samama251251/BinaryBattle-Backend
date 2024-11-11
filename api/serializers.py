from rest_framework import serializers
from .models import Friendship, User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'name', 'email']

class FriendshipSerializer(serializers.ModelSerializer):
    sender_details = UserSerializer(source='sender', read_only=True)
    receiver_details = UserSerializer(source='receiver', read_only=True)
    
    class Meta:
        model = Friendship
        fields = ['id', 'sender', 'receiver', 'sender_details', 
                 'receiver_details', 'status', 'created_at']