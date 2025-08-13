# chat/serializers.py
from rest_framework import serializers
from django.db import transaction

from .models import Conversation, Message
from django.conf import settings

User = settings.AUTH_USER_MODEL

class MessageSerializer(serializers.ModelSerializer):
    sender_id = serializers.SerializerMethodField()
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "conversation", "sender_id", "sender_name", "text", "metadata", "is_read", "created_at"]

    def get_sender_id(self, obj):
        user = obj.sender
        if not user:
            return None
        if hasattr(user, "teacher"):
            return user.teacher.id  
        elif hasattr(user, "student"):
            return user.student.id
        return user.id

    def get_sender_name(self, obj):
        user = obj.sender
        if not user:
            return None
        return getattr(user, "first_name", None) or getattr(user, "email", None) or str(user)



class ConversationSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    teacher_id = serializers.IntegerField(source="teacher.id", read_only=True)
    student_id = serializers.IntegerField(source="student.id", read_only=True)
    teacher_name = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "teacher_id",
            "teacher_name",
            "student_id",
            "student_name",
            "created_by",
            "created_at",
            "updated_at",
            "last_message"
        ]

    def get_teacher_name(self, obj):
        if obj.teacher and obj.teacher.user:
            return (
                f"{obj.teacher.user.first_name} {obj.teacher.user.last_name}".strip()
                or obj.teacher.user.email
            )
        return None

    def get_student_name(self, obj):
        if obj.student and obj.student.user:
            return (
                f"{obj.student.user.first_name} {obj.student.user.last_name}".strip()
                or obj.student.user.email
            )
        return None

    def get_last_message(self, obj):
        last = obj.messages.order_by("-created_at").first()
        return MessageSerializer(last).data if last else None



class ConversationCreateSerializer(serializers.Serializer):
    teacher_id = serializers.IntegerField(required=False)
    student_id = serializers.IntegerField(required=False)

    def validate(self, data):
        user = self.context["request"].user
        teacher_id = data.get("teacher_id")
        student_id = data.get("student_id")

        if not teacher_id and not student_id:
            raise serializers.ValidationError("Provide teacher_id or student_id (one may be inferred from your account).")

        from django.apps import apps
        Teacher = apps.get_model("core", "Teacher")
        Student = apps.get_model("core", "Student")

        if hasattr(user, "student") and not student_id:
            student_obj = getattr(user, "student")
            student_id = getattr(student_obj, "id")
            data["student_id"] = student_id

        if hasattr(user, "teacher") and not teacher_id:
            teacher_obj = getattr(user, "teacher")
            teacher_id = getattr(teacher_obj, "id")
            data["teacher_id"] = teacher_id

        try:
            teacher = Teacher.objects.get(id=teacher_id)
        except Teacher.DoesNotExist:
            raise serializers.ValidationError({"teacher_id": "Invalid teacher_id."})

        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            raise serializers.ValidationError({"student_id": "Invalid student_id."})

  
        if not user.is_staff:
            if hasattr(user, "student"):
                my_student = getattr(user, "student")
                assigned_teacher = getattr(my_student, "teacher", None)
                if not assigned_teacher or assigned_teacher.id != teacher.id:
                    raise serializers.ValidationError("You may only start a conversation with your assigned teacher.")
            elif hasattr(user, "teacher"):
                my_teacher = getattr(user, "teacher")
                if not Student.objects.filter(id=student.id, teacher=my_teacher).exists():
                    raise serializers.ValidationError("You may only start conversations with students assigned to you.")
            else:
                raise serializers.ValidationError("Only teachers or students may create conversations.")
        data["_teacher_obj"] = teacher
        data["_student_obj"] = student
        return data

    def create(self, validated_data):
        teacher = validated_data["_teacher_obj"]
        student = validated_data["_student_obj"]
        user = self.context["request"].user

        conv, created = Conversation.objects.get_or_create(teacher=teacher, student=student, defaults={"created_by": user})
        return conv
