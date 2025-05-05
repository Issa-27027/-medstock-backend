from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.userprofile.role == 'admin'

class IsDoctor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.userprofile.role == 'doctor'

class IsPharmacist(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.userprofile.role == 'pharmacist'

class HasRoleAccess(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        # Admin has access to everything
        if request.user.userprofile.role == 'admin':
            return True
            
        # Get the required role from the view
        required_role = getattr(view, 'required_role', None)
        if not required_role:
            return False
            
        # Check if user has the required role
        return request.user.userprofile.role == required_role