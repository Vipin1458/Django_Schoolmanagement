# chat/views.py
from rest_framework import viewsets, status, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from .models import Conversation, Message
from .serializers import ConversationSerializer, ConversationCreateSerializer, MessageSerializer

from django.shortcuts import get_object_or_404


class ConversationViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ConversationSerializer
    queryset = Conversation.objects.all()

    def get_queryset(self):
        user = self.request.user
        from django.apps import apps
        Teacher = apps.get_model("core", "Teacher")
        Student = apps.get_model("core", "Student")

        qs = Conversation.objects.none()
        if hasattr(user, "teacher"):
            teacher_obj = getattr(user, "teacher")
            qs = qs | Conversation.objects.filter(teacher=teacher_obj)
        if hasattr(user, "student"):
            student_obj = getattr(user, "student")
            qs = qs | Conversation.objects.filter(student=student_obj)
        if user.is_staff:
            qs = Conversation.objects.all()

        return qs.distinct().order_by("-updated_at")

    def list(self, request):
        qs = self.get_queryset()
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = ConversationSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)
        serializer = ConversationSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)

    def create(self, request):
        from django.apps import apps
        Teacher = apps.get_model("core", "Teacher")
        Student = apps.get_model("core", "Student")

        user = request.user
        data = request.data.copy()

        if hasattr(user, "student"):
            student_obj = user.student
            assigned_teacher = student_obj.assigned_teacher
            if not assigned_teacher:
                return Response(
                    {"detail": "You do not have an assigned teacher."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            data["student_id"] = student_obj.id
            data["teacher_id"] = assigned_teacher.id  

        elif hasattr(user, "teacher"):
            teacher_obj = user.teacher
            data["teacher_id"] = teacher_obj.id
            if not data.get("student_id"):
                return Response(
                    {"detail": "Student ID is required when creating a conversation as a teacher."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        elif user.is_staff:
            if not data.get("teacher_id") or not data.get("student_id"):
                return Response(
                    {"detail": "Both teacher_id and student_id are required for admin."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        else:
            return Response({"detail": "You are not allowed to create a conversation."}, status=403)

        serializer = ConversationCreateSerializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        conv = serializer.save()
        read_ser = ConversationSerializer(conv, context={"request": request})
        return Response(read_ser.data, status=status.HTTP_201_CREATED)



    @action(detail=True, methods=["get"], url_path="messages")
    def messages(self, request, pk=None):
        conv = get_object_or_404(Conversation, pk=pk)

        user = request.user
        if not user.is_staff:
            is_participant = False
            if hasattr(user, "teacher") and conv.teacher == getattr(user, "teacher"):
                is_participant = True
            if hasattr(user, "student") and conv.student == getattr(user, "student"):
                is_participant = True
            if not is_participant:
                return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        qs = conv.messages.all().order_by("created_at")
        serializer = MessageSerializer(qs, many=True, context={"request": request})
        return Response({"results": serializer.data})
