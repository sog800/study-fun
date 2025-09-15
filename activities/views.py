from rest_framework import generics, permissions
from .models import Lesson
from .serializers import LessonSerializer
from rest_framework.response import Response
from rest_framework import status
from .utils import chunk_text
from .ai_service import call_ai
import os
import PyPDF2
from pptx import Presentation
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import json

class LessonCreateView(generics.CreateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # allow file uploads

    def extract_text_from_pdf(self, file_obj):
        reader = PyPDF2.PdfReader(file_obj)
        text = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
        return " ".join(text)

    def extract_text_from_pptx(self, file_obj):
        prs = Presentation(file_obj)
        text = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if hasattr(shape, "text"):
                    text.append(shape.text)
        return " ".join(text)

    def create(self, request, *args, **kwargs):
        title = request.data.get("title")
        raw_topic = request.data.get("topic")
        uploaded_file = request.FILES.get("file")

        # Case 1: Text provided
        if raw_topic:
            content = raw_topic

        # Case 2: File uploaded
        elif uploaded_file:
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext == ".pdf":
                content = self.extract_text_from_pdf(uploaded_file)
            elif ext in [".pptx", ".ppt"]:
                content = self.extract_text_from_pptx(uploaded_file)
            else:
                return Response({"error": "Unsupported file type"}, status=status.HTTP_400_BAD_REQUEST)

        else:
            return Response({"error": "Provide either text or file"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Chunk the content into slides
        chunks = chunk_text(content, max_length=400)  # smaller for slides

        explained_chunks = []
        for chunk in chunks:
            prompt = f"""
            Explain the following text in clear, simple English for students. 
            - Break it into small paragraphs. 
            - Retain key scientific terms but explain them in parentheses, e.g. "Homeostasis (keeping balance in the body)". 

            Text:
            {chunk}
            """
            explained_chunks.append(call_ai(prompt))

        # 2. Combine for quiz generation
        combined_text = " ".join(explained_chunks)
        quiz_prompt = f"""
        Create a multiple-choice quiz based on the following lesson.  
        - Each question should have 4 options (A, B, C, D). 
        - Clearly mark the correct answer.

        Lesson:
        {combined_text}
        """
        quiz = call_ai(quiz_prompt)

        # 3. Save lesson
        lesson = Lesson.objects.create(
            title=title,
            topic=explained_chunks,  # list of slides
            quiz=quiz,
            created_by=request.user,
        )

        serializer = LessonSerializer(lesson)
        return Response(serializer.data, status=status.HTTP_201_CREATED)





# Retrieve + Update + Delete a lesson
class LessonDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]


# List all lessons
class LessonsListView(generics.ListAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def grade_quiz(request, pk):
    try:
        lesson = Lesson.objects.get(pk=pk)
    except Lesson.DoesNotExist:
        return Response({"error": "Lesson not found"}, status=status.HTTP_404_NOT_FOUND)
    
    quiz_data = request.data
    questions = quiz_data.get('questions', [])
    
    if not questions:
        return Response({"error": "No questions provided"}, status=status.HTTP_400_BAD_REQUEST)
    
    # Calculate basic score
    correct_count = 0
    question_results = []
    
    for question_data in questions:
        user_answer = (question_data.get('userAnswer') or '').strip().upper().replace(')', '')
        correct_answer = (question_data.get('correctAnswer') or '').strip().upper().replace(')', '')
        is_correct = user_answer == correct_answer
        
        if is_correct:
            correct_count += 1
            
        question_results.append({
            'question': question_data.get('question', ''),
            'userAnswer': user_answer,
            'correctAnswer': correct_answer,
            'isCorrect': is_correct,
            'explanation': ''  # Will be filled by AI
        })
    
    total_questions = len(questions)
    percentage = (correct_count / total_questions) * 100 if total_questions > 0 else 0
    
    # Generate AI feedback
    quiz_summary = f"""
    Student Quiz Results:
    - Score: {correct_count}/{total_questions} ({percentage:.1f}%)
    - Questions and Answers:
    """
    
    for i, q in enumerate(question_results):
        quiz_summary += f"""
    {i+1}. {q['question']}
       Student answered: {q['userAnswer']}
       Correct answer: {q['correctAnswer']}
       Result: {'Correct' if q['isCorrect'] else 'Incorrect'}
    """
    
    feedback_prompt = f"""
    Based on the quiz results below, provide:
    1. Encouraging feedback (2-3 sentences)
    2. Areas for improvement if score < 70%
    3. Congratulations if score >= 70%
    
    Keep it positive and educational.
    
    {quiz_summary}
    """
    
    try:
        ai_feedback = call_ai(feedback_prompt)
        
        # Generate explanations for incorrect answers
        for question_result in question_results:
            if not question_result['isCorrect']:
                explanation_prompt = f"""
                Question: {question_result['question']}
                Correct Answer: {question_result['correctAnswer']}
                Student Answer: {question_result['userAnswer']}
                
                Provide a brief explanation (1-2 sentences) of why the correct answer is right.
                """
                explanation = call_ai(explanation_prompt)
                question_result['explanation'] = explanation.strip()
        
    except Exception as e:
        ai_feedback = f"Great job completing the quiz! You scored {correct_count} out of {total_questions} questions correctly."
    
    result = {
        'score': correct_count,
        'totalQuestions': total_questions,
        'percentage': round(percentage, 1),
        'feedback': ai_feedback,
        'questionResults': question_results
    }
    
    return Response(result, status=status.HTTP_200_OK)
