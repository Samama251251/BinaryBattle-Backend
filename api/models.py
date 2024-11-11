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
    """
    Model to handle friendship relationships between users
    """
    
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