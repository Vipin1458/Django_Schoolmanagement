from rest_framework import serializers

# from rest_framework.exceptions import ValidationError
from django.contrib.auth.hashers import make_password

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
