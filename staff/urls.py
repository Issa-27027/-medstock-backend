from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StaffViewSet, DepartmentViewSet, TrainingViewSet, AchievementViewSet, ScheduleViewSet
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Staff, Department
from django.contrib.auth.models import User
import uuid
from django.utils import timezone
import random
import string

router = DefaultRouter()
router.register(r'staff', StaffViewSet)
router.register(r'departments', DepartmentViewSet)
router.register(r'trainings', TrainingViewSet)
router.register(r'achievements', AchievementViewSet)
router.register(r'schedules', ScheduleViewSet)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_staff(request):
    """
    A simple function-based view to create staff members directly.
    This bypasses the ViewSet permissions for testing.
    """
    try:
        print("Create staff request received:", request.data)
        
        # Create a user for the staff member
        # For simplicity, we'll use the staff ID as the username
        staff_id = request.data.get('id', f"S{uuid.uuid4().hex[:5].upper()}")
        
        # Generate a random password
        def generate_password(length=12):
            characters = string.ascii_letters + string.digits + string.punctuation
            return ''.join(random.choice(characters) for _ in range(length))
        
        # Get name components
        full_name = request.data.get('name', '')
        name_parts = full_name.split()
        first_name = name_parts[0] if name_parts else ''
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
        
        # Create user for the staff member
        username = f"staff_{staff_id.lower()}"
        email = request.data.get('email', f"{username}@example.com")
        
        # Create the user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=generate_password(),
            first_name=first_name,
            last_name=last_name
        )
        
        # Try to find a department by name
        department_name = request.data.get('department', 'Pharmacy')
        department, created = Department.objects.get_or_create(name=department_name)
        
        # Get emergency contact data
        emergency_contact = request.data.get('emergency_contact', {})
        if not emergency_contact and request.data.get('emergencyContact'):
            emergency_contact = request.data.get('emergencyContact')
        
        # Create the staff member
        staff = Staff.objects.create(
            user=user,  # Link to the newly created user
            staff_id=staff_id,
            role=request.data.get('role', 'pharmacist').lower(),
            department=department,
            status=request.data.get('status', 'active').lower(),
            phone=request.data.get('phone', ''),
            address=request.data.get('address', ''),
            specialization=request.data.get('specializations', ''),
            emergency_contact=emergency_contact,
            joining_date=request.data.get('dateOfJoining', timezone.now().date()),
            years_of_experience=int(request.data.get('yearsOfExperience', 0)),
            qualifications=request.data.get('qualifications', '').split(',') if isinstance(request.data.get('qualifications', ''), str) else request.data.get('qualifications', [])
        )
        
        # Return more complete information
        return Response({
            "message": "Staff member created successfully", 
            "id": staff.id,
            "staff_id": staff.staff_id,
            "name": full_name,
            "email": user.email,
            "phone": staff.phone,
            "role": staff.role,
            "department": department.name,
            "status": staff.status,
            "emergency_contact": staff.emergency_contact,
            "specializations": [staff.specialization] if staff.specialization else [],
            "qualifications": staff.qualifications,
            "years_of_experience": staff.years_of_experience,
            "joining_date": staff.joining_date
        })
    except Exception as e:
        print(f"Error creating staff member: {str(e)}")
        return Response({"error": str(e)}, status=500)

urlpatterns = [
    path('', include(router.urls)),
    path('create/', create_staff, name='create-staff'),
] 