from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_role')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'userprofile__role')
    search_fields = ('username', 'first_name', 'last_name', 'email')

    def get_role(self, obj):
        return obj.userprofile.role
    get_role.short_description = 'Role'

admin.site.unregister(User)
admin.site.register(User, UserAdmin)


# Register your models here.
