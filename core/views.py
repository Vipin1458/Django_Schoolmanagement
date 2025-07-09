from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics, permissions
from .serializers import TeacherSerializer, StudentSerializer
from .models import Teacher, Student
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate

class RegisterTeacherView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TeacherSerializer(data=request.data)
        if serializer.is_valid():
            teacher = serializer.save()
            return Response({
                "message": "Teacher registered successfully.",
                "teacher_id": teacher.id,
                "user_id": teacher.user.id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterStudentView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = StudentSerializer(data=request.data)
        if serializer.is_valid():
            student = serializer.save()
            return Response({
                "message": "Student registered successfully.",
                "student_id": student.id,
                "user_id": student.user.id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherListView(generics.ListAPIView):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [permissions.AllowAny]


class StudentListView(generics.ListAPIView):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [permissions.AllowAny]


class StudentsByTeacherView(generics.ListAPIView):
    serializer_class = StudentSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        teacher_id = self.kwargs['teacher_id']
        return Student.objects.filter(assigned_teacher__id=teacher_id)
    
class CustomLoginView(APIView):
    permission_classes = []  

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"error": "Please provide both username and password."},
                            status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if not user:
            return Response({"error": "Invalid credentials."},
                            status=status.HTTP_401_UNAUTHORIZED)

        token, created = Token.objects.get_or_create(user=user)

        return Response({
            "token": token.key,
            "user_id": user.id,
            "username": user.username,
            "role": user.role
        }, status=status.HTTP_200_OK)
