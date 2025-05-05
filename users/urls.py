from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserProfileViewSet, LoginAPIView, AccessCheckAPIView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.decorators import api_view
from rest_framework.response import Response

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'profiles', UserProfileViewSet)

# Custom view to handle the user-profile endpoint
@api_view(['GET'])
def current_user_profile(request):
    profile = request.user.userprofile
    serializer = UserProfileViewSet.serializer_class(profile)
    return Response(serializer.data)

urlpatterns = [
    path('', include(router.urls)),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('check-access/', AccessCheckAPIView.as_view(), name='check-access'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('user-profile/', current_user_profile, name='user-profile'),
]
