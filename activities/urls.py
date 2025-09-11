from django.urls import path
from .views import LessonsListView, LessonDetailView, LessonCreateView, grade_quiz

urlpatterns = [
    path("lessons/create/", LessonCreateView.as_view(), name="lesson-create"),
    path("lessons/", LessonsListView.as_view(), name="lesson-list"),
    path("lessons/<int:pk>/", LessonDetailView.as_view(), name="lesson-detail"),
    path("lessons/<int:pk>/grade-quiz/", grade_quiz, name="grade-quiz"),
]
