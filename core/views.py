from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,viewsets
from .serializers import TeacherSerializer, StudentSerializer
from .models import Teacher, Student
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .permissions import IsAdmin, IsTeacher
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied


class RegisterTeacherView(APIView):
    permission_classes = [IsAdmin]

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
    permission_classes = [IsAdmin]

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


class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [IsAdmin]

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAdmin]

# class StudentByTeacherViewSet(viewsets.ReadOnlyModelViewSet):
class StudentByTeacherViewSet(viewsets.ModelViewSet):    
    serializer_class = StudentSerializer
    permission_classes = [IsTeacher]

    def get_queryset(self):
        return Student.objects.filter(assigned_teacher__user=self.request.user)
    
    def get_object(self):
        # Override to ensure teacher can access only their own student
        obj = super().get_object()
        if obj.assigned_teacher.user != self.request.user:
            raise PermissionDenied("You do not have permission to access this student.")
        return obj

    def perform_create(self, serializer):
        serializer.save(assigned_teacher=self.request.user.teacher)

class AdminTeacherViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Teacher.objects.all()
    serializer_class = TeacherSerializer
    permission_classes = [IsAdmin]

    @action(detail=True, methods=['get'], url_path='students')
    def get_students(self, request, pk=None):
        teacher = self.get_object()
        students = Student.objects.filter(assigned_teacher=teacher)
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)