from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from .models import Friendship, User,Group, Challenge, ChallengeParticipant
from .serializers import FriendshipSerializer, UserSerializer, ChallengeSerializer, ChallengeParticipantSerializer, ChallengeDetailSerializer
from django.utils import timezone
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
                Q(sender=sender, receiver=receiver,status="accepted") |
                Q(sender=receiver, receiver=sender,status = "accepted")
            ).first()

            if existing_friendship:
                return Response({
                    'message': 'Friendship already exists',
                }, status=status.HTTP_200_OK)
            already_sent = Friendship.objects.filter(
                Q(sender=sender, receiver=receiver,status="pending") |
                Q(sender=receiver, receiver=sender,status = "pending")
            ).first()
            if already_sent:
                return Response({
                    "success":False,
                    "data": None,
                    "message":"Friend Request Already Sent"
                },status=status.HTTP_409_CONFLICT)
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
                    (Q(receiver=user)) & Q(status="accepted")
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
            

# This will be the api for getting all the friend requests which a user has received
class FriendRequestAPIView(APIView):
    def get(self,request):
        query_params = dict(request.query_params)
        userEmail = query_params.get('email', [None])[0]
        if not userEmail:
            return Response({"error": "User email parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(email=userEmail)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        friend_requests = Friendship.objects.filter(receiver=user, status="pending")
        serializer = FriendshipSerializer(friend_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self,request):
        try:
            action = request.data.get('action')
            receiver_email = request.data.get('receiverEmail')
            sender_email = request.data.get('senderEmail')

            if not all([action, receiver_email, sender_email]):
                return Response({
                    "error": "Missing required parameters"
                }, status=status.HTTP_400_BAD_REQUEST)
            try:
                receiver = User.objects.get(email=receiver_email)
                sender = User.objects.get(email=sender_email)
            except User.DoesNotExist:
                return Response({
                    "error": "User not found"
                }, status=status.HTTP_404_NOT_FOUND)
            friendship = Friendship.objects.filter(sender=sender,receiver=receiver,status='pending').first()
            if action == 'accept':
                friendship.status = 'accepted'
            elif action == 'reject':
                friendship.status = 'rejected'
            else:
                return Response({
                    "error": "Invalid action"
                }, status=status.HTTP_400_BAD_REQUEST)
            friendship.save()
            return Response({
                "message": f"Friend request {action}ed successfully"
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "error": "Unexpected error occurred",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class UserCreateAPIView(APIView):

    # This api will return the user deatils based on the username. It will be used in the search bar to search for new friends
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
                print("this will be returne")
                return Response([], status=status.HTTP_200_OK)
            
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

class ChallengeAPIView(APIView):
    def post(self, request):
        try:
            # Create new challenge
            data = {
                'title': request.data.get('title'),
                'problem_id': request.data.get('problem'),
                'duration': request.data.get('duration'),
                'created_by': User.objects.get(email=request.data.get('createdBy')),
                'status': 'pending',
            }
            print("I cam here with this data", data)
            challenge = Challenge.objects.create(**data)
            serializer = ChallengeSerializer(challenge)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': 'Failed to create challenge', 
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    def get(self, request, challenge_id=None):
        try:
            if challenge_id:
                # Fetch specific challenge with details
                print("I am here with this challenge id", challenge_id)
                challenge = Challenge.objects.select_related('created_by').get(id=challenge_id)
                print("I am here with this challenge", challenge)
                serializer = ChallengeDetailSerializer(challenge)
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                # Return all active challenges
                challenges = Challenge.objects.filter(status='active').select_related('created_by')
                serializer = ChallengeSerializer(challenges, many=True)
                return Response(serializer.data, status=status.HTTP_200_OK)

        except Challenge.DoesNotExist:
            print(f"Challenge not found with ID: {challenge_id}")
            return Response(
                {'error': f'Challenge with ID {challenge_id} not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"Error fetching challenge: {str(e)}")
            return Response({
                'error': 'Failed to fetch challenge',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ChallengeParticipationAPIView(APIView):
    def post(self, request):
        try:
            challenge_id = request.data.get('challengeId')
            user_email = request.data.get('userEmail')
            
            challenge = Challenge.objects.get(id=challenge_id)
            user = User.objects.get(email=user_email)
            
            # Check if user already joined
            if ChallengeParticipant.objects.filter(challenge=challenge, user=user).exists():
                return Response({'error': 'Already joined this challenge'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Join the challenge
            ChallengeParticipant.objects.create(
                challenge=challenge,
                user=user
            )
             
            return Response({'message': 'Successfully joined the challenge'}, status=status.HTTP_200_OK)
            
        except (Challenge.DoesNotExist, User.DoesNotExist):
            return Response({'error': 'Challenge or User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': 'Failed to join challenge',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ChallengeReadyAPIView(APIView):
    def post(self, request, challenge_id):
        try:
            print("I am here with this challenge id", challenge_id)
            challenge = Challenge.objects.get(id=challenge_id)
            user = User.objects.get(username=request.data.get('username'))
            if challenge and user:
                print("I am here with this user", user)
                participant = ChallengeParticipant.objects.get(
                    challenge=challenge,
                    user=user
                )
                print("I am here with this participant", participant)
                print("I am here with this is ready", request.data.get('isReady', False))
            participant.is_ready = request.data.get('isReady', False)
            participant.save()
            
            return Response({
                'message': 'Ready status updated successfully'
            }, status=status.HTTP_200_OK)
            
        except (Challenge.DoesNotExist, User.DoesNotExist, ChallengeParticipant.DoesNotExist):
            return Response({
                'error': 'Challenge or participant not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': 'Failed to update ready status',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class ChallengeStartAPIView(APIView):
    def post(self, request, challenge_id):
        try:
            challenge = Challenge.objects.get(id=challenge_id)
            
            # Update challenge status to 'active' and set start time
            challenge.status = 'active'
            challenge.start_time = timezone.now()
            challenge.save()
            
            # Get all participants and update their start times
            participants = ChallengeParticipant.objects.filter(challenge=challenge)
            for participant in participants:
                participant.start_time = challenge.start_time
                participant.save()
            
            return Response({
                "message": "Challenge started successfully",
                "start_time": challenge.start_time
            }, status=status.HTTP_200_OK)
            
        except Challenge.DoesNotExist:
            return Response({
                "error": "Challenge not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "error": "Failed to start challenge",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

