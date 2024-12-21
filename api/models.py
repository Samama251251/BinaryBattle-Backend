from django.db import models
from django.utils import timezone

class User(models.Model):
    username = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    score = models.SmallIntegerField(default=0)
    rank = models.TextField()
    isOnline = models.BooleanField(default=False,null=True)

    def __str__(self):
        return f"{self.username}"

    class Meta:
        ordering = ['created_at']

class Friendship(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('blocked', 'Blocked')
    ]

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='friendship_requests_sent'
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='friendship_requests_received'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['sender', 'receiver']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender} -> {self.receiver} ({self.status})"

    def accept(self):
        if self.status == 'pending':
            self.status = 'accepted'
            self.save()

    def reject(self):
        if self.status == 'pending':
            self.status = 'rejected'
            self.save()

class Group(models.Model):
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(User, related_name='groups')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages', null=True,)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        if self.group:
            return f"From {self.sender} to group {self.group.name} at {self.timestamp}"
        return f"From {self.sender} to {self.receiver} at {self.timestamp}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.group and self.receiver:
            raise ValidationError("A message cannot have both a receiver and a group.")
        if not self.group and not self.receiver:
            raise ValidationError("A message must have either a receiver or a group.")
class MessageReadStatus(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='read_status'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='message_read_status'
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['message', 'user']),
        ]

class Challenge(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed')
    ]

    title = models.CharField(max_length=200)
    problem_id = models.CharField(max_length=100)
    duration = models.IntegerField()  # in minutes  
    created_by = models.ForeignKey('User', on_delete=models.CASCADE, related_name='created_challenges')
    created_at = models.DateTimeField(default=timezone.now)
    start_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    participants = models.ManyToManyField('User', through='ChallengeParticipant', related_name='participated_challenges')
   
class ChallengeParticipant(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(default=timezone.now)
    submission = models.TextField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_ready = models.BooleanField(default=False)