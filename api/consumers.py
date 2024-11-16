from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async  # Add this import
import json
from .models import Message,User,Group,MessageReadStatus
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.room_name = self.scope['url_route']['kwargs']['room_name']
            self.room_group_name = f'chat_{self.room_name}'
            print(f"Connecting to room: {self.room_name}")
            print(f"User: {self.scope.get('user', 'Anonymous')}")
            
            # Join room group
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