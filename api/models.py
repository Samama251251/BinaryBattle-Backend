from django.db import models

class User(models.Model):
    username = models.CharField(max_length=50, primary_key=True)
    name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    score = models.SmallIntegerField(default=0)
    rank = models.TextField()

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
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages', null=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages', null=True,)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

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