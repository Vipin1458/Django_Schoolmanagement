# chat/models.py
from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL

class Conversation(models.Model):
    """
    1:1 conversation between a student and a teacher.
    Unique constraint prevents duplicates.
    """
    teacher = models.ForeignKey("core.Teacher", on_delete=models.CASCADE, related_name="conversations")
    student = models.ForeignKey("core.Student", on_delete=models.CASCADE, related_name="conversations")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("teacher", "student")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Conversation: teacher={self.teacher_id} student={self.student_id}"


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="sent_messages")
    text = models.TextField()
    metadata = models.JSONField(null=True, blank=True)  # for attachments or future use
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Msg {self.pk} conv={self.conversation_id} by={self.sender_id}"
from django.db import models

# Create your models here.
