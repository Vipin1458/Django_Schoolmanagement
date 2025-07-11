from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import Teacher, Student
from core.serializers import StudentSerializer

from datetime import date

User = get_user_model()

class StudentSerializerTest(TestCase):
    def setUp(self):
        self.teacher_user = User.objects.create_user(
            username='teacher1',
            email='teacher1@example.com',
            password='testpass123',
            role='teacher'
        )
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            employee_id='EMP001',
            phone_number='9999999999',
            subject_specialization='CS',
            date_of_joining=date(2022, 10, 10)
        )

        
        self.student_data = {
            'user': {
                'username': 'student1',
                'email': 'student1@example.com',
                'password': 'pass1234',
                'role': 'student'
            },
            'roll_number': 'ROLL001',
            'phone_number': '1111111111',
            'grade': '10',
            'date_of_birth': '2007-01-11',
            'admission_date': '2024-05-03',
            'status': 0,
            'assigned_teacher': self.teacher.id
        }

    def test_valid_student_serializer(self):
        serializer = StudentSerializer(data=self.student_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_student_creation(self):
        serializer = StudentSerializer(data=self.student_data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        student = serializer.save()

        self.assertEqual(student.roll_number, 'ROLL001')
        self.assertEqual(student.assigned_teacher, self.teacher)
        self.assertEqual(student.user.username, 'student1')

    def test_missing_required_fields(self):
        invalid_data = self.student_data.copy()
        invalid_data.pop('roll_number')

        serializer = StudentSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('roll_number', serializer.errors)
