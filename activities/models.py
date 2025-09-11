from django.db import models
from django.contrib.auth.models import User

class Lesson(models.Model):
    title = models.CharField(max_length=200, null=True, blank=True)
    topic = models.JSONField(null=True, blank=True)   # will hold ["chunk1 explained", "chunk2 explained", ...]
    quiz = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lessons")

    def __str__(self):
        return self.title
