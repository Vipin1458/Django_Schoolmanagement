from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

from .models import Conversation, Message
from .serializers import ConversationSerializer, ConversationCreateSerializer, MessageSerializer


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
       
        data = request.data.copy()
        user = request.user

        if hasattr(user, "student") and not data.get("student_id"):
            data["student_id"] = user.student.id
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

        qs = conv.messages.all().order_by("-created_at")
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = MessageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = MessageSerializer(qs, many=True)
        return Response(serializer.data)
    


    