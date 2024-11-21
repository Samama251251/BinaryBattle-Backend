
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
    #This will be the api for getting all the friends of a specific user
    def get(self,request):
            try:
                query_params = dict(request.query_params)
                username = query_params.get('username', [None])[0]
                if not username:
                    return Response({"error": "Username parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
                # Get the user object first
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
                # Fix the filter syntax and get accepted friendships
                friendships = Friendship.objects.filter(
                    # Get friendships where user is the sender and status is accepted
                    (Q(sender=user)) & Q(status="accepted")
                )  # Efficiently load the receiver user details
                # Create a list to store friend details
                friend_details = []
                for friendship in friendships:

                    friend_details.append({
                        
                            'username': friendship.receiver.username,
                            'isOnline': friendship.receiver.isOnline,

                            'email': friendship.receiver.email,
                            'score': friendship.receiver.score,
                            'rank': friendship.receiver.rank
                        
                    })
                friendships_receiver = Friendship.objects.filter(
                    # Get friendships where user is the sender and status is accepted
                    (Q(receiver=user))
                )  # Efficiently load the receiver user details
                # Create a list to store friend details
                for friendship in friendships_receiver:
                    friend_details.append({
                        
                            'username': friendship.sender.username,
                            'isOnline': True,
                            'email': friendship.sender.email,
                            'score': friendship.sender.score,
                            'rank': friendship.sender.rank,
                        
                    })
                
                return Response(friend_details, status=status.HTTP_200_OK)
            except Exception as e:
                print(e)
                return Response({
                    "error": "Unexpected error occurred",
                    "detail": str(e)
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
    def get(self,request):
        try:
            print("I was here")
            query_params = dict(request.query_params)
            # Convert QueryDict to dictionary
            username = query_params.get('username', [None])[0]  # Handle case when username param is missing
            if not username:
                return Response({"error": "Username parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
            
            print(username)
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
            
            print("I came here")
            serializer = UserSerializer(user)
            return Response([serializer.data], status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return Response({
                "error": "Unexpected error occurred",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GroupChatAPIView(APIView):
    def post(self,request):
        group_name = request.data["group_name"]
        print("group name is", group_name)
        return Response({"message":"Group created successfully"},status=status.HTTP_201_CREATED)
class TestAPIView(APIView):
    def post(self,request):
        data = request.data
        print(data)
        print("I am inside the testing")
        return Response({"message": "Received"}, status=status.HTTP_200_OK)

