
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from .models import Friendship, User,Group
from .serializers import FriendshipSerializer
# Create your views here.
from .models import Friendship
from .serializers import UserSerializer 
class FriendshipAPIView(APIView):
    def post(self,request):
        try:
            sender_username = request.data["sender"]
            receiver_username = request.data["receiver"]
            # This will verify whether the body conatins the sender username and receiver username
            if not sender_username or not receiver_username:
                Response({
                    'errorMessage':'Both sender and receiver username are required'
                },status=status.HTTP_400_BAD_REQUEST)
            # Verifying both users exist in database before making Friendship
            try:
                sender = User.objects.get(username = sender_username)
            except User.DoesNotExist:
                return Response({
                    "errorMessage":f"Sender user {sender_username} does not exist"
                },status=status.HTTP_404_NOT_FOUND)
            try:
                receiver = User.objects.get(username = receiver_username)
            except User.DoesNotExist:
                return Response({
                    "errorMessage":f"Receiver user {receiver_username} does not exist"
                })
            # Making sure that sender and receiver both are not same
            if sender == receiver:
                return Response({
                    'error': 'Cannot create friendship with yourself'
                }, status=status.HTTP_400_BAD_REQUEST)
            #Making sure that Request is not send already
            existing_friendship = Friendship.objects.filter(
                Q(sender=sender, receiver=receiver) |
                Q(sender=receiver, receiver=sender)
            ).first()

            if existing_friendship:
                return Response({
                    'error': 'Friendship already exists',
                    'status': existing_friendship.status,
                    'friendship_id': existing_friendship.id
                }, status=status.HTTP_400_BAD_REQUEST)
           # Now after all the checkings we will create friendship 
            try:
                friendship = Friendship.objects.create(sender = sender,receiver = receiver,status="pending")
                serializer = FriendshipSerializer(friendship)
                return Response(serializer.data)
            except Exception as e:
                return Response({
                    'error': 'Failed to create friendship',
                    'detail': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({
                'error': 'Unexpected error occurred',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class UserCreateAPIView(APIView):
    def post(self, request):
        # try:
        #     serializer = UserSerializer(data=request.data)
        #     if serializer.is_valid():
        #         serializer.save()
        #         return Response(serializer.data, status=status.HTTP_201_CREATED)
        #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        # except Exception as e:
        #     return Response({
        #         'error': 'Unexpected error occurred',
        #         'detail': str(e)
        #     }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        print("user created")
        return Response({"message":"User created successfully"},status=status.HTTP_201_CREATED)
        
class GroupChatAPIView(APIView):
    def post(self,request):
        group_name = request.data["group_name"]
        print("group name is", group_name)
        return Response({"message":"Group created successfully"},status=status.HTTP_201_CREATED)


            