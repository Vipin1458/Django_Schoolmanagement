from rest_framework import serializers
# from rest_framework.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from core.models import Exam, Question, Teacher
from .models import User, Teacher,Student,StudentExam, StudentAnswer

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

        if len(questions_data) != 5:
            raise serializers.ValidationError("Each exam must contain exactly 5 questions.")

        if request_user.role == 'teacher':
            teacher = Teacher.objects.get(user=request_user)
            validated_data['teacher'] = teacher

        validated_data['created_by'] = request_user
        exam = Exam.objects.create(**validated_data)

        for q in questions_data:
            Question.objects.create(exam=exam, **q)

        return exam



class ExamSubmissionAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    answer = serializers.CharField()



class StudentAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question_text', read_only=True)

    class Meta:
        model = StudentAnswer
        fields = ['id', 'question', 'question_text','answer', 'is_correct']

class StudentExamSerializer(serializers.ModelSerializer):
    exam_title = serializers.CharField(source='exam.title', read_only=True)
    answers = StudentAnswerSerializer(many=True, read_only=True) 
    student_name = serializers.CharField(source='student.user.username', read_only=True)
    class Meta:
        model = StudentExam
        fields = ['id', 'exam', 'exam_title', 'marks','student_name',  'submitted_at', 'answers']

class ExamSubmissionSerializer(serializers.Serializer):
    answers = ExamSubmissionAnswerSerializer(many=True)

    def validate_answers(self, value):
        if len(value) != 5:
            raise serializers.ValidationError("You must answer exactly 5 questions.")
        return value

    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        exam = self.context['exam']
        student = Student.objects.get(user=user)

        
        if StudentExam.objects.filter(student=student, exam=exam).exists():
            raise serializers.ValidationError("You have already submitted this exam.")

      
        student_exam = StudentExam.objects.create(student=student, exam=exam)
        score = 0

        for ans in validated_data['answers']:
            question_id = ans.get('question_id')
            answer = ans.get('answer')

            try:
                question = Question.objects.get(id=question_id, exam=exam)
            except Question.DoesNotExist:
                raise serializers.ValidationError(
                    f"Question ID {question_id} does not belong to this exam."
                )

            correct_answer = getattr(question, f"option{question.correct_option}")
            is_correct = question.correct_option == answer   

            if is_correct:
                score += 1

            StudentAnswer.objects.create(
                student_exam=student_exam,
                question=question,
                answer=answer,
                is_correct=is_correct
            )

        student_exam.marks = score
        student_exam.save()
        return student_exam
