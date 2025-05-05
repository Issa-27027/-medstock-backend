from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Prescription, PrescriptionItem

class PrescriptionResource(resources.ModelResource):
    class Meta:
        model = Prescription

class PrescriptionItemResource(resources.ModelResource):
    class Meta:
        model = PrescriptionItem

class PrescriptionItemInline(admin.TabularInline):
    model = PrescriptionItem
    extra = 1

class PrescriptionInline(admin.TabularInline):
    model = Prescription
    extra = 0
    readonly_fields = ['date_prescribed']

@admin.register(Prescription)
class PrescriptionAdmin(ImportExportModelAdmin):
    resource_class = PrescriptionResource
    list_display = ('patient', 'date_prescribed', 'prescribed_by')
    list_filter = ('date_prescribed', 'prescribed_by')
    search_fields = ('patient__name', 'prescribed_by', 'notes')
    inlines = [PrescriptionItemInline]
    readonly_fields = ['date_prescribed']

@admin.register(PrescriptionItem)
class PrescriptionItemAdmin(ImportExportModelAdmin):
    resource_class = PrescriptionItemResource
    list_display = ('prescription', 'medicine', 'dosage', 'quantity')
    list_filter = ('medicine',)
    search_fields = ('prescription__patient__name', 'medicine__name')

# Register your models here.
