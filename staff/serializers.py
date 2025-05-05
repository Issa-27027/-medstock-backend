from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Department, Staff, StaffActivity, Training, Achievement, Schedule

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'description', 'created_at']
        read_only_fields = ['created_at']

class TrainingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Training
        fields = ['id', 'title', 'description', 'completion_date',
                 'certificate_number', 'provider', 'created_at']
        read_only_fields = ['created_at']

class AchievementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achievement
        fields = ['id', 'title', 'description', 'date_awarded',
                 'award_type', 'created_at']
        read_only_fields = ['created_at']

class StaffActivitySerializer(serializers.ModelSerializer):
    performed_by = UserSerializer(read_only=True)

    class Meta:
        model = StaffActivity
        fields = ['id', 'action', 'details', 'performed_by', 'timestamp']
        read_only_fields = ['timestamp']

class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = ['id', 'date', 'start_time', 'end_time',
                 'is_available', 'notes', 'created_at']
        read_only_fields = ['created_at']

class StaffSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='user',
        write_only=True
    )
    department = DepartmentSerializer(read_only=True)
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(),
        source='department',
        write_only=True,
        required=False,
        allow_null=True
    )
    activities = StaffActivitySerializer(many=True, read_only=True)
    trainings = TrainingSerializer(many=True, read_only=True)
    achievements = AchievementSerializer(many=True, read_only=True)
    schedules = ScheduleSerializer(many=True, read_only=True)
    full_name = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()

    class Meta:
        model = Staff
        fields = ['id', 'user', 'user_id', 'staff_id', 'role', 'department',
                 'department_id', 'status', 'status_display', 'specialization',
                 'qualifications', 'years_of_experience', 'license_number',
                 'phone', 'address', 'emergency_contact', 'joining_date',
                 'activities', 'trainings', 'achievements', 'schedules',
                 'full_name', 'created_at', 'updated_at']
        read_only_fields = ['staff_id', 'created_at', 'updated_at']

    def get_full_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"

    def get_status_display(self, obj):
        return obj.get_status_display()

    def create(self, validated_data):
        staff = Staff.objects.create(**validated_data)
        StaffActivity.objects.create(
            staff=staff,
            action='created',
            details='Staff member created',
            performed_by=self.context['request'].user
        )
        return staff

    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data.get('status', old_status)
        
        # Update staff
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Create activity entry if status changed
        if old_status != new_status:
            StaffActivity.objects.create(
                staff=instance,
                action='status_changed',
                details=f'Status changed from {old_status} to {new_status}',
                performed_by=self.context['request'].user
            )
        
        return instance 