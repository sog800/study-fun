from rest_framework import serializers
from .models import Lesson

class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ["id", "title", "topic", "quiz", "created_at", "created_by"]
        read_only_fields = ["id", "created_at", "created_by"]
