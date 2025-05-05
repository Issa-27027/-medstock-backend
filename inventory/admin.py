from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin
from .models import Medicine, Supplier, Category, Batch, InventoryLog

class MedicineResource(resources.ModelResource):
    class Meta:
        model = Medicine

class SupplierResource(resources.ModelResource):
    class Meta:
        model = Supplier

class CategoryResource(resources.ModelResource):
    class Meta:
        model = Category

class BatchResource(resources.ModelResource):
    class Meta:
        model = Batch

class InventoryLogResource(resources.ModelResource):
    class Meta:
        model = InventoryLog

@admin.register(Medicine)
class MedicineAdmin(ImportExportModelAdmin):
    resource_class = MedicineResource
    list_display = ['name', 'category', 'supplier', 'min_quantity', 'price_per_unit']
    list_filter = ['category', 'supplier']
    search_fields = ['name', 'barcode']

@admin.register(Supplier)
class SupplierAdmin(ImportExportModelAdmin):
    resource_class = SupplierResource
    list_display = ['name', 'contact_person', 'phone', 'email']
    search_fields = ['name', 'contact_person']

@admin.register(Category)
class CategoryAdmin(ImportExportModelAdmin):
    resource_class = CategoryResource
    list_display = ['name', 'description']
    search_fields = ['name']

@admin.register(Batch)
class BatchAdmin(ImportExportModelAdmin):
    resource_class = BatchResource
    list_display = ['batch_number', 'medicine', 'quantity', 'expiration_date', 'cost_per_unit']
    list_filter = ['medicine', 'expiration_date']
    search_fields = ['batch_number', 'medicine__name']

@admin.register(InventoryLog)
class InventoryLogAdmin(ImportExportModelAdmin):
    resource_class = InventoryLogResource
    list_display = ['medicine', 'batch', 'action', 'quantity', 'timestamp', 'performed_by']
    list_filter = ['action', 'timestamp']
    search_fields = ['medicine__name', 'batch__batch_number', 'performed_by']
