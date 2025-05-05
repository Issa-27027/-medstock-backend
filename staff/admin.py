from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Staff, Department, Schedule, Leave

class StaffResource(resources.ModelResource):
    class Meta:
        model = Staff

class DepartmentResource(resources.ModelResource):
    class Meta:
        model = Department

class ScheduleResource(resources.ModelResource):
    class Meta:
        model = Schedule

class LeaveResource(resources.ModelResource):
    class Meta:
        model = Leave

@admin.register(Staff)
class StaffAdmin(ImportExportModelAdmin):
    resource_class = StaffResource
    list_display = ['user', 'department', 'role', 'phone', 'joining_date']
    list_filter = ['department', 'role']
    search_fields = ['user__username', 'user__email', 'phone']

@admin.register(Department)
class DepartmentAdmin(ImportExportModelAdmin):
    resource_class = DepartmentResource
    list_display = ['name', 'description', 'head_of_department']
    search_fields = ['name', 'head_of_department__user__username']

@admin.register(Schedule)
class ScheduleAdmin(ImportExportModelAdmin):
    resource_class = ScheduleResource
    list_display = ['staff', 'day_of_week', 'start_time', 'end_time']
    list_filter = ['day_of_week']
    search_fields = ['staff__user__username']

@admin.register(Leave)
class LeaveAdmin(ImportExportModelAdmin):
    resource_class = LeaveResource
    list_display = ['staff', 'leave_type', 'start_date', 'end_date', 'status']
    list_filter = ['leave_type', 'status']
    search_fields = ['staff__user__username'] 