from channels.generic.websocket import AsyncWebsocketConsumer,AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async  # Add this import
import json
from .models import Message,User,Group,MessageReadStatus
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            # Self.scope is like the request body of the http request. it contains the necessary information about the request
            print("scope is", self.scope)
            # whenever a socker is connection is established between the client and server a unique channel name is given to that web socket conncetion so therfore 
            # channel name is basically a unique idenetity given to each web socet connetion
            print("channel name is", self.channel_name)
            self.room_name = self.scope['url_route']['kwargs']['room_name']
            self.room_group_name = f'chat_{self.room_name}'
            print(f"Connecting to room: {self.room_name}")
            print(f"User: {self.scope.get('user', 'Anonymous')}")
            # Channel layer is the backend system managing all the connections . In this it is the reddis. It is creating a group and adding a client to the group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            await self.accept()
            print(f"Successfully connected to {self.room_group_name}")
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
        # Save the message to database
        #newmessage = await self.save_message(text_data)
        print("new message is", text_data)
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': text_data
            }
        )
    @database_sync_to_async
    # This function save the message to the database and make the message read status for all the members of the group and then return the message 
    def save_message(self, message_content):
        # Create the message
        message = Message.objects.create(
            content=message_content,
            sender=User.objects.get(username="charlie"),  # This should be dynamic
            group=Group.objects.get(name="DevOps Team")  # This should be dynamic
        )
        
        # Get all group members
        print("I came here")
        group = message.group
        group_members = group.members.all()
        
        # Create MessageReadStatus for each member
        for member in group_members:
            print("member is", member.username)
            MessageReadStatus.objects.create(
                message=message,
                user=member,
                is_read=member == message.sender  # True for sender, False for others
            )
        return message
    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
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
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        
        # Notify others that a new user has joined
        print("I came here to notify the others")
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_join_leave',
                'username': self.username,
                'action': 'joined'
            }
        )

    async def disconnect(self, close_code):
        # Notify others that a user has left
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
