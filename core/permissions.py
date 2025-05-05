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

class IsAdminOrDoctor(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.userprofile.role in ['admin', 'doctor']

class IsAdminOrPharmacist(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.userprofile.role in ['admin', 'pharmacist']

class RoleBasedPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        # Admin has access to everything
        if request.user.userprofile.role == 'admin':
            return True

        # Check method-specific permissions
        if hasattr(view, 'role_permissions'):
            role_permissions = view.role_permissions
            method = request.method.lower()
            allowed_roles = role_permissions.get(method, [])
            return request.user.userprofile.role in allowed_roles

        return False

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        # Admin has access to everything
        if request.user.userprofile.role == 'admin':
            return True

        # Check if the object has a user field and if it matches the request user
        if hasattr(obj, 'user') and obj.user == request.user:
            return True

        # Check if the object has a created_by field and if it matches the request user
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True

        return False 