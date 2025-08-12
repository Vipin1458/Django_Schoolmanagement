# chat/serializers.py
from rest_framework import serializers
from django.db import transaction

from .models import Conversation, Message
from django.conf import settings

User = settings.AUTH_USER_MODEL

class MessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.IntegerField(source="sender.id", read_only=True)
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "conversation", "sender_id", "sender_name", "text", "metadata", "is_read", "created_at"]

    def get_sender_name(self, obj):
        # Adjust depending on your User model fields
        user = getattr(obj, "sender", None)
        if not user:
            return None
        return getattr(user, "first_name", None) or getattr(user, "email", None) or str(user)


class ConversationSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    teacher_id = serializers.IntegerField(source="teacher.id", read_only=True)
    student_id = serializers.IntegerField(source="student.id", read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "teacher_id", "student_id", "created_by", "created_at", "updated_at", "last_message"]

    def get_last_message(self, obj):
        last = obj.messages.order_by("-created_at").first()
        if not last:
            return None
        return MessageSerializer(last).data


class ConversationCreateSerializer(serializers.Serializer):
    teacher_id = serializers.IntegerField(required=False)
    student_id = serializers.IntegerField(required=False)

    def validate(self, data):
        user = self.context["request"].user
        teacher_id = data.get("teacher_id")
        student_id = data.get("student_id")

        # Basic validation: must provide both party ids or infer from user
        if not teacher_id and not student_id:
            raise serializers.ValidationError("Provide teacher_id or student_id (one may be inferred from your account).")

        # We will import the models lazily to avoid import issues:
        from django.apps import apps
        Teacher = apps.get_model("core", "Teacher")
        Student = apps.get_model("core", "Student")

        # If user is a student and didn't pass student_id, infer it
        if hasattr(user, "student") and not student_id:
            student_obj = getattr(user, "student")
            student_id = getattr(student_obj, "id")
            data["student_id"] = student_id

        # If user is a teacher and didn't pass teacher_id, infer it
        if hasattr(user, "teacher") and not teacher_id:
            teacher_obj = getattr(user, "teacher")
            teacher_id = getattr(teacher_obj, "id")
            data["teacher_id"] = teacher_id

        # Validate existence of teacher and student
        try:
            teacher = Teacher.objects.get(id=teacher_id)
        except Teacher.DoesNotExist:
            raise serializers.ValidationError({"teacher_id": "Invalid teacher_id."})

        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            raise serializers.ValidationError({"student_id": "Invalid student_id."})

        # Permission rules:
        # If requester is student -> teacher must be assigned to that student.
        # If requester is teacher -> student must be in their student list.
        # Admins (is_staff) bypass checks.
        if not user.is_staff:
            if hasattr(user, "student"):
                # requester is student
                my_student = getattr(user, "student")
                # expecting Student model has a FK to teacher named 'teacher'
                assigned_teacher = getattr(my_student, "teacher", None)
                if not assigned_teacher or assigned_teacher.id != teacher.id:
                    raise serializers.ValidationError("You may only start a conversation with your assigned teacher.")
            elif hasattr(user, "teacher"):
                my_teacher = getattr(user, "teacher")
                # check that the student is assigned to this teacher
                # This expects Student model to have a FK 'teacher' pointing to Teacher
                if not Student.objects.filter(id=student.id, teacher=my_teacher).exists():
                    raise serializers.ValidationError("You may only start conversations with students assigned to you.")
            else:
                # some other user types (fallback)
                raise serializers.ValidationError("Only teachers or students may create conversations.")
        # save found objects for use later
        data["_teacher_obj"] = teacher
        data["_student_obj"] = student
        return data

    def create(self, validated_data):
        teacher = validated_data["_teacher_obj"]
        student = validated_data["_student_obj"]
        user = self.context["request"].user

        # get_or_create to prevent duplicates
        conv, created = Conversation.objects.get_or_create(teacher=teacher, student=student, defaults={"created_by": user})
        return conv
