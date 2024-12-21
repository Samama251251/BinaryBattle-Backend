from rest_framework import serializers
from .models import Friendship, User,Message, Challenge, ChallengeParticipant

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'name', 'email','score','rank']

class FriendshipSerializer(serializers.ModelSerializer):
    sender_details = UserSerializer(source='sender', read_only=True)
    receiver_details = UserSerializer(source='receiver', read_only=True)
    
    class Meta:
        model = Friendship
        fields = ['id', 'sender', 'receiver', 'sender_details', 
                 'receiver_details', 'status', 'created_at']

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'content', 'timestamp', 'is_read']
        read_only_fields = ['sender', 'timestamp']

class ChallengeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Challenge
        fields = ['id', 'title', 'problem_id', 'duration', 'created_by', 'created_at', 'start_time', 'status']

class ChallengeParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengeParticipant
        fields = ['user', 'challenge', 'joined_at', 'submission', 'completed_at']

class ChallengeDetailSerializer(serializers.ModelSerializer):
    participants = serializers.SerializerMethodField()

    class Meta:
        model = Challenge
        fields = ['id', 'title', 'problem_id', 'duration', 'created_by', 
                 'start_time', 'status', 'participants']

    def get_participants(self, obj):
        participants = []
        for participant in obj.participants.all():
            challenge_participant = ChallengeParticipant.objects.get(
                challenge=obj, 
                user=participant
            )
            participants.append({
                'email': participant.email,
                'username': participant.username,
                'isReady': challenge_participant.is_ready,
                'joinedAt': challenge_participant.joined_at
            })
        return participants