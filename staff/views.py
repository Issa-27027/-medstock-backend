from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Department, Staff, StaffActivity, Training, Achievement, Schedule
from .serializers import (
    DepartmentSerializer, StaffSerializer, StaffActivitySerializer,
    TrainingSerializer, AchievementSerializer, ScheduleSerializer
)
from django.db.models import Q, Count
import uuid

class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'])
    def staff(self, request, pk=None):
        department = self.get_object()
        staff = Staff.objects.filter(department=department)
        serializer = StaffSerializer(staff, many=True)
        return Response(serializer.data)

class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Staff.objects.all()
        search = self.request.query_params.get('search')
        role = self.request.query_params.get('role')
        department = self.request.query_params.get('department')
        status = self.request.query_params.get('status')
        sort_by = self.request.query_params.get('sort_by')
        sort_order = self.request.query_params.get('sort_order', 'asc')

        # Apply filters
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(staff_id__icontains=search) |
                Q(specialization__icontains=search)
            )
        if role:
            queryset = queryset.filter(role=role)
        if department:
            queryset = queryset.filter(department_id=department)
        if status:
            queryset = queryset.filter(status=status)

        # Apply sorting
        if sort_by:
            if sort_by == 'name':
                sort_field = 'user__last_name'
            elif sort_by == 'role':
                sort_field = 'role'
            elif sort_by == 'department':
                sort_field = 'department__name'
            elif sort_by == 'status':
                sort_field = 'status'
            elif sort_by == 'hire_date':
                sort_field = 'hire_date'
            else:
                sort_field = sort_by

            if sort_order == 'desc':
                sort_field = f'-{sort_field}'
            queryset = queryset.order_by(sort_field)

        return queryset

    def perform_create(self, serializer):
        staff_id = f"S{uuid.uuid4().hex[:5].upper()}"
        serializer.save(staff_id=staff_id)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        staff = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Staff.STATUS_CHOICES):
            return Response(
                {'error': 'Invalid status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = staff.status
        staff.status = new_status
        staff.save()

        # Create activity entry
        StaffActivity.objects.create(
            staff=staff,
            action='status_changed',
            details=f'Status changed from {old_status} to {new_status}',
            performed_by=request.user
        )

        return Response(StaffSerializer(staff).data)

    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        staff = self.get_object()
        activities = StaffActivity.objects.filter(staff=staff)
        serializer = StaffActivitySerializer(activities, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def trainings(self, request, pk=None):
        staff = self.get_object()
        trainings = Training.objects.filter(staff=staff)
        serializer = TrainingSerializer(trainings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def achievements(self, request, pk=None):
        staff = self.get_object()
        achievements = Achievement.objects.filter(staff=staff)
        serializer = AchievementSerializer(achievements, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        # Basic statistics
        total_staff = Staff.objects.count()
        active_staff = Staff.objects.filter(status='active').count()
        on_leave_staff = Staff.objects.filter(status='on_leave').count()
        
        # Role distribution
        role_distribution = Staff.objects.values('role').annotate(
            count=Count('id')
        )
        
        # Department distribution
        department_distribution = Staff.objects.values(
            'department__name'
        ).annotate(
            count=Count('id')
        )
        
        # Experience distribution
        experience_distribution = {
            '0-5': Staff.objects.filter(years_of_experience__lte=5).count(),
            '6-10': Staff.objects.filter(
                years_of_experience__gt=5,
                years_of_experience__lte=10
            ).count(),
            '11-20': Staff.objects.filter(
                years_of_experience__gt=10,
                years_of_experience__lte=20
            ).count(),
            '20+': Staff.objects.filter(years_of_experience__gt=20).count()
        }
        
        return Response({
            'overview': {
                'total_staff': total_staff,
                'active_staff': active_staff,
                'on_leave_staff': on_leave_staff
            },
            'role_distribution': role_distribution,
            'department_distribution': department_distribution,
            'experience_distribution': experience_distribution
        })

class TrainingViewSet(viewsets.ModelViewSet):
    queryset = Training.objects.all()
    serializer_class = TrainingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        staff_id = self.request.query_params.get('staff_id')
        if staff_id:
            return Training.objects.filter(staff_id=staff_id)
        return Training.objects.all()

class AchievementViewSet(viewsets.ModelViewSet):
    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        staff_id = self.request.query_params.get('staff_id')
        if staff_id:
            return Achievement.objects.filter(staff_id=staff_id)
        return Achievement.objects.all()

class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        staff_id = self.request.query_params.get('staff_id')
        if staff_id:
            return Schedule.objects.filter(staff_id=staff_id)
        return Schedule.objects.all() 