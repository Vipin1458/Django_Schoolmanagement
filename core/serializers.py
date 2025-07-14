from rest_framework import serializers

# from rest_framework.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from core.models import Exam, Question, ExamSubmission, Answer, Teacher,StudentExam, StudentAnswer
from .models import User, Teacher,Student

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.get('password')
        if not password:
            raise serializers.ValidationError({'password': 'This field is required.'})
        validated_data['password'] = make_password(password)
        return super().create(validated_data)


class TeacherSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Teacher
        fields = ['id', 'user', 'employee_id', 'phone_number', 'subject_specialization', 'date_of_joining', 'status']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        teacher = Teacher.objects.create(user=user, **validated_data)
        return teacher
    
class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    assigned_teacher = serializers.PrimaryKeyRelatedField(queryset=Teacher.objects.all())
    warn_assigned_teacher_change = False

    class Meta:
        model = Student
        fields = ['id', 'user', 'roll_number', 'phone_number', 'grade', 'date_of_birth', 'admission_date', 'status', 'assigned_teacher']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_serializer = UserSerializer(data=user_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        student = Student.objects.create(user=user, **validated_data)
        return student
    


    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        request_user = self.context['request'].user

        if getattr(request_user, "role", "") != "admin" and 'assigned_teacher' in validated_data:
            validated_data.pop('assigned_teacher')
            self.warn_assigned_teacher_change = True
        if user_data:
            user_serializer = UserSerializer(instance.user, data=user_data, partial=True)
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()

    
        return super().update(instance, validated_data)
    
class TeacherSelfUpdateSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Teacher
        fields = ['user','phone_number']  

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        user = instance.user

        # Update phone number
        if 'phone_number' in validated_data:
            instance.phone_number = validated_data['phone_number']
            instance.save()

        return instance

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            'id', 'question_text', 'option1', 'option2', 'option3', 'option4', 'correct_option'
        ]

class ExamSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, write_only=True)
    teacher = serializers.PrimaryKeyRelatedField(queryset=Teacher.objects.all(), required=False)

    class Meta:
        model = Exam
        fields = ['id', 'title', 'subject', 'teacher', 'questions']

    def create(self, validated_data):
        questions_data = validated_data.pop('questions')
        request_user = self.context['request'].user

        # If a teacher is creating, assign automatically
        if request_user.role == 'teacher':
            teacher = Teacher.objects.get(user=request_user)
            validated_data['teacher'] = teacher

        # Admin must explicitly provide a teacher
        validated_data['created_by'] = request_user
        exam = Exam.objects.create(**validated_data)

        for q in questions_data:
            Question.objects.create(exam=exam, **q)

        return exam
    

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['question', 'selected_option']

class ExamSubmissionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, write_only=True)
    score = serializers.IntegerField(read_only=True)

    class Meta:
        model = ExamSubmission
        fields = ['id', 'exam', 'answers', 'score']

    def create(self, validated_data):
        answers_data = validated_data.pop('answers')
        student = Student.objects.get(user=self.context['request'].user)
        submission = ExamSubmission.objects.create(student=student, **validated_data)

        score = 0
        for answer_data in answers_data:
            question = answer_data['question']
            selected_option = answer_data['selected_option']
            Answer.objects.create(submission=submission, question=question, selected_option=selected_option)

            if question.correct_option == selected_option:
                score += 1

        submission.score = score
        submission.save()
        return submission
