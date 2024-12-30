from channels.generic.websocket import AsyncWebsocketConsumer,AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async  # Add this import
import json
from .models import Message,User,Group,MessageReadStatus,ChallengeParticipant
# Self.scope is like the request body of the http request. it contains the necessary information about the request
# whenever a socker is connection is established between the client and server a unique channel name is given to that web socket conncetion so therfore 
# channel name is basically a unique idenetity given to each web socet connetion
# Channel layer is the backend system managing all the connections . In this it is the reddis. It is creating a group and adding a client to the group
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            # Get both users' usernames from the URL
            print("I came here to connect")
            self.room_id = self.scope['url_route']['kwargs']['room_id']
            
        
            self.room_name = f"chat_{self.room_id}"
            self.room_group_name = self.room_name
            
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            print(f"Successfully connected to chat between {self.room_id}")
        except Exception as e:
            print(f"Connection error: {str(e)}")
            raise

    async def disconnect(self, close_code):
        print(f"Disconnecting with code: {close_code}")
        try:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            print("Successfully disconnected from group")
        except Exception as e:
            print(f"Disconnect error: {str(e)}")
    async def receive(self, text_data):
        try:
            print("I came here to receive")
            data = json.loads(text_data)
            print("data is",data)
            message_content = data['text']
            print("printign the message content",message_content)
            # Save message to database
            message = await self.save_message(data)
            
            # Check if other user is online
            is_online = await self.check_user_online(data["to"])
            
            if not is_online or is_online:
                print("I am sending the message to the group")
                # Send message to room group if user is online
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message_content,
                        'sender': data["source"],
                        'timestamp': str(message.timestamp)
                    }
                )
            # If user is offline, message is already saved in DB with unread status
            
        except Exception as e:
            print(f"Error in receive: {str(e)}")

    @database_sync_to_async
    def save_message(self, data):
        print("I came here to save the message")
        print("data is",data)
        sender = User.objects.get(username=data["source"])
        receiver = User.objects.get(username=data["to"])
        
        # Create the message
        message = Message.objects.create(
            content=data['text'],
            sender=sender,
            receiver=receiver  # Add receiver field to Message model
        )
        
        # Create MessageReadStatus for receiver
        MessageReadStatus.objects.create(
            message=message,
            user=receiver,
            is_read=False
        )
        
        return message

    @database_sync_to_async
    def check_user_online(self, username):
        try:
            user = User.objects.get(username=username)
            return user.isOnline
        except User.DoesNotExist:
            return False

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'timestamp': event['timestamp']
        }))

class onlineConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            # Accept the WebSocket connection
            username = self.scope['url_route']['kwargs']['username']
            print("I came inside the onlineConsumer")
            await self.changeOnlineStatus(username,"connect")
            await self.accept()

        except Exception as e:
            print(f"Error in connect: {str(e)}")
            await self.close()
                 
    async def disconnect(self,close_code):
        try:
            username = self.scope['url_route']['kwargs']['username']       
            await self.changeOnlineStatus(username,"disconnect")
        except Exception as e:
            print(f"Error in disconnect: {str(e)}")
    @database_sync_to_async
    def changeOnlineStatus(self, username,mode):
        try:
            user = User.objects.get(username=username)
            if(mode=="connect"):
                user.isOnline = True
            else:
                user.isOnline = False
            user.save()
        except User.DoesNotExist:
            print(f"User {username} not found")
            return None
        except Exception as e:
            print(f"Error changing online status: {str(e)}")
            return None

class ChallengeLobbyConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        print("I came here to connect")
        self.challenge_id = self.scope['url_route']['kwargs']['challenge_id']
        self.room_group_name = f'challenge_lobby_{self.challenge_id}'
        self.username = self.scope['url_route']['kwargs']['username']
        print("username is",self.username)
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        
        # Update challenge participants and notify others
        await self.update_challenge_participants('joined')
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_join_leave',
                'username': self.username,
                'action': 'joined'
            }
        )

    async def disconnect(self, close_code):
        # Update challenge participants and notify others
        await self.update_challenge_participants('left')
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_join_leave',
                'username': self.username,
                'action': 'left'
            }
        )
        
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive_json(self, content):
        message_type = content.get('type')
        if message_type == 'ready_status':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'ready_status_update',
                    'username': content['username'],
                    'isReady': content['isReady']
                }
            )
        elif message_type == 'challenge_start':
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'challenge_started',
                    'startTime': content['startTime']
                }
            )

    async def ready_status_update(self, event):
        await self.send_json({
            'type': 'ready_status_update',
            'username': event['username'],
            'isReady': event['isReady']
        })

    async def challenge_started(self, event):
        # Skip sending to the channel that initiated the challenge start
        if event.get('skip_channel') != self.channel_name:
            await self.send_json({
                'type': 'challenge_started', 
                'startTime': event['startTime']
            })

    async def user_join_leave(self, event):
        await self.send_json({
            'type': 'user_join_leave',
            'username': event['username'],
            'action': event['action']
        })

    @database_sync_to_async
    def update_challenge_participants(self, action):
        try:
            print("I came here to update the challenge participants")
            if action == 'joined':
                ChallengeParticipant.objects.get_or_create(
                    challenge_id=self.challenge_id,
                    user=User.objects.get(username=self.username)
                )
            elif action == 'left':
                ChallengeParticipant.objects.filter(
                    challenge_id=self.challenge_id,
                    user__username=self.username
                ).delete()
        except Exception as e:
            print(f"Error updating challenge participants: {str(e)}")

class ChallengeArenaConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        try:
            # Get challenge ID and user email from the connection
            self.challenge_id = self.scope['url_route']['kwargs']['challenge_id']
            self.username = self.scope['url_route']['kwargs']['username']
            self.room_group_name = f'challenge_arena_{self.challenge_id}'

            # Add to challenge group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            
            print(f"User {self.username} connected to challenge {self.challenge_id} arena")
        except Exception as e:
            print(f"Connection error: {str(e)}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            # Remove from challenge group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            print(f"User {self.username} disconnected from challenge {self.challenge_id} arena")
        except Exception as e:
            print(f"Disconnect error: {str(e)}")

    async def receive_json(self, content):
        try:
            message_type = content.get('type')
            data = content.get('data', {})
            print("i came here")
            if message_type == 'new_submission':
                # Broadcast submission status to all participants
                print("I am here for the new submission")

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'submission_update',
                        'username': data['username'],
                        'challengeId': data['challengeId'],
                        'skip_channel': self.channel_name
                    }
                )
                print("I have succesfull sent the data")
            
            elif message_type == 'submission_completed':
                # Broadcast completion status and score
                print("I am here for the submission completed")
                print("data is",data)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'challenge_winner',
                        'username': data['username'],
                        'challengeId': data['challengeId'],
                        'status': "submitted",
                        'skip_channel': self.channel_name
                    }
                )
                print("I have succesfull sent the data")
                # Check if this submission makes the user a winner
                if data['status'] == 'completed':
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'challenge_winner',
                            'username': data['username'],
                            'challengeId': data['challengeId']
                        }
                    )

        except Exception as e:
            print(f"Error processing message: {str(e)}")

    async def submission_update(self, event):
        # Skip sending to the channel that initiated the submission
        if event.get('skip_channel') != self.channel_name:
            await self.send_json({
                'type': 'submission_update',
                'challengeId': event['challengeId'],
                'username': event['username'],
                'status': "submitted",
            })
        print("Succesfuuly Done the websoccket")

    async def challenge_winner(self, event):
        # Send winner notification to WebSocket
        if event.get('skip_channel') != self.channel_name:
            await self.send_json({
                'type': 'challenge_winner',
                'challengeId': event['challengeId'],
                'username': event['username']
            })
