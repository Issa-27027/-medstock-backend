from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from .models import UserProfile
from .serializers import UserSerializer, UserProfileSerializer, UserRegistrationSerializer
from .permissions import IsAdmin, IsDoctor, IsPharmacist, HasRoleAccess
from .access_rules import has_access
from core.permissions import RoleBasedPermission

class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'username': user.username,
                'role': user.userprofile.role,
            })
        else:
            return Response({"error": "Invalid credentials"}, status=401)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, RoleBasedPermission]

    role_permissions = {
        'get': ['admin'],
        'post': ['admin'],
        'put': ['admin'],
        'patch': ['admin'],
        'delete': ['admin']
    }

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.userprofile.role == 'admin':
            return User.objects.all()
        return User.objects.filter(id=user.id)

    @action(detail=False, methods=['post'])
    def register(self, request):
        if not request.user.userprofile.role == 'admin':
            return Response(
                {'error': 'Only admin can register new users'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, RoleBasedPermission]

    role_permissions = {
        'get': ['admin'],
        'post': ['admin'],
        'put': ['admin'],
        'patch': ['admin'],
        'delete': ['admin']
    }

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.userprofile.role == 'admin':
            return UserProfile.objects.all()
        return UserProfile.objects.filter(user=user)
    
    def retrieve(self, request, pk=None):
        # If no pk is provided or it's 'me', return the current user's profile
        if pk is None or pk == 'me':
            profile = request.user.userprofile
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        return super().retrieve(request, pk)

    @action(detail=False, methods=['get'])
    def by_role(self, request):
        if not request.user.userprofile.role == 'admin':
            return Response(
                {'error': 'Only admin can view users by role'},
                status=status.HTTP_403_FORBIDDEN
            )
        role = request.query_params.get('role')
        if not role:
            return Response({'error': 'Role is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        profiles = UserProfile.objects.filter(role=role)
        serializer = self.get_serializer(profiles, many=True)
        return Response(serializer.data)

class AccessCheckAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        page = request.query_params.get('page')
        if not page:
            return Response({'error': 'Page parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        has_permission = has_access(request.user, page)
        return Response({
            'has_access': has_permission,
            'role': request.user.userprofile.role
        })
