from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SupplierViewSet, CategoryViewSet, MedicineViewSet,
    BatchViewSet, InventoryLogViewSet
)

router = DefaultRouter()
router.register(r'suppliers', SupplierViewSet)
router.register(r'categories', CategoryViewSet)
router.register(r'medicines', MedicineViewSet)
router.register(r'batches', BatchViewSet)
router.register(r'inventory-logs', InventoryLogViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('adjust-inventory/', MedicineViewSet.as_view({'post': 'adjust_inventory'}), name='adjust-inventory'),
] 