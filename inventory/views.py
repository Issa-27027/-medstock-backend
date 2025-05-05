from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Supplier, Category, Medicine, Batch, InventoryLog
from .serializers import (
    SupplierSerializer, CategorySerializer, MedicineSerializer,
    BatchSerializer, InventoryLogSerializer
)
from datetime import date, timedelta
from django.db.models import Sum, Q
from core.permissions import IsAdmin, IsPharmacist, IsAdminOrPharmacist, RoleBasedPermission

# Create your views here.

class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrPharmacist]

    role_permissions = {
        'get': ['admin', 'pharmacist'],
        'post': ['admin'],
        'put': ['admin'],
        'patch': ['admin'],
        'delete': ['admin']
    }

    @action(detail=True, methods=['get'])
    def medicines(self, request, pk=None):
        supplier = self.get_object()
        medicines = Medicine.objects.filter(supplier=supplier)
        serializer = MedicineSerializer(medicines, many=True)
        return Response(serializer.data)

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrPharmacist]

    role_permissions = {
        'get': ['admin', 'pharmacist'],
        'post': ['admin'],
        'put': ['admin'],
        'patch': ['admin'],
        'delete': ['admin']
    }

    @action(detail=True, methods=['get'])
    def medicines(self, request, pk=None):
        category = self.get_object()
        medicines = Medicine.objects.filter(category=category)
        serializer = MedicineSerializer(medicines, many=True)
        return Response(serializer.data)

class MedicineViewSet(viewsets.ModelViewSet):
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    permission_classes = [permissions.IsAuthenticated, RoleBasedPermission]

    role_permissions = {
        'get': ['admin', 'pharmacist', 'doctor'],
        'post': ['admin', 'pharmacist'],
        'put': ['admin', 'pharmacist'],
        'patch': ['admin', 'pharmacist'],
        'delete': ['admin']
    }

    def get_queryset(self):
        queryset = Medicine.objects.all()
        search = self.request.query_params.get('search', None)
        category = self.request.query_params.get('category', None)
        supplier = self.request.query_params.get('supplier', None)
        barcode = self.request.query_params.get('barcode', None)

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(barcode__icontains=search)
            )
        if category:
            queryset = queryset.filter(category_id=category)
        if supplier:
            queryset = queryset.filter(supplier_id=supplier)
        if barcode:
            queryset = queryset.filter(barcode=barcode)

        return queryset

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        if not request.user.userprofile.role in ['admin', 'pharmacist']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        medicines = Medicine.objects.all()
        low_stock_medicines = []
        for medicine in medicines:
            total_quantity = sum(batch.quantity for batch in medicine.batches.all())
            if total_quantity <= medicine.min_quantity:
                low_stock_medicines.append(medicine)
        serializer = self.get_serializer(low_stock_medicines, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        if not request.user.userprofile.role in ['admin', 'pharmacist']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        days = request.query_params.get('days', 30)
        expiry_date = date.today() + timedelta(days=int(days))
        batches = Batch.objects.filter(expiration_date__lte=expiry_date)
        medicines = Medicine.objects.filter(batches__in=batches).distinct()
        serializer = self.get_serializer(medicines, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_batch(self, request, pk=None):
        if not request.user.userprofile.role in ['admin', 'pharmacist']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        medicine = self.get_object()
        serializer = BatchSerializer(data=request.data)
        if serializer.is_valid():
            batch = serializer.save(medicine=medicine)
            InventoryLog.objects.create(
                medicine=medicine,
                batch=batch,
                action='ADD',
                quantity=batch.quantity,
                performed_by=request.user.username,
                notes=f'Added new batch {batch.batch_number}'
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['post'])
    def adjust_inventory(self, request):
        """
        Adjust inventory based on completed orders or prescriptions
        """
        if not request.user.userprofile.role in ['admin', 'pharmacist']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        source_type = request.data.get('source_type')  # 'order' or 'prescription'
        source_id = request.data.get('source_id')
        items = request.data.get('items', [])
        
        for item in items:
            medicine_id = item.get('medicine_id')
            quantity = item.get('quantity')
            batch_id = item.get('batch_id')
            
            try:
                medicine = Medicine.objects.get(id=medicine_id)
                batch = None
                if batch_id:
                    batch = Batch.objects.get(id=batch_id)
                
                # For orders (adding to inventory)
                if source_type == 'order':
                    if not batch:
                        # Check for existing batch with same order source
                        existing_batch = Batch.objects.filter(
                            medicine=medicine,
                            batch_number__startswith=f"ORD-{source_id}-"
                        ).first()
                        
                        if existing_batch:
                            # Update existing batch
                            existing_batch.quantity += quantity
                            existing_batch.save()
                            batch = existing_batch
                        else:
                            # Create a new batch if none exists
                            batch = Batch.objects.create(
                                medicine=medicine,
                                batch_number=f"ORD-{source_id}-{medicine_id}",
                                quantity=quantity,
                                expiration_date=item.get('expiration_date', date.today() + timedelta(days=365)),
                                cost_per_unit=item.get('cost_per_unit', medicine.price_per_unit)
                            )
                    else:
                        # Update existing batch
                        batch.quantity += quantity
                        batch.save()
                    
                    action = 'ADD'
                    
                # For prescriptions (removing from inventory)
                elif source_type == 'prescription':
                    if not batch:
                        # Find batches with the earliest expiration dates first
                        batches = Batch.objects.filter(
                            medicine=medicine, 
                            quantity__gt=0
                        ).order_by('expiration_date')
                        
                        remaining_quantity = quantity
                        for b in batches:
                            if remaining_quantity <= 0:
                                break
                                
                            if b.quantity >= remaining_quantity:
                                # This batch has enough
                                b.quantity -= remaining_quantity
                                b.save()
                                
                                # Create log for this batch
                                InventoryLog.objects.create(
                                    medicine=medicine,
                                    batch=b,
                                    action='DISPENSE',
                                    quantity=-remaining_quantity,
                                    performed_by=request.user.username,
                                    notes=f'Dispensed for prescription #{source_id}'
                                )
                                
                                remaining_quantity = 0
                            else:
                                # Use all in this batch and continue to next
                                remaining_quantity -= b.quantity
                                
                                # Create log for this batch
                                InventoryLog.objects.create(
                                    medicine=medicine,
                                    batch=b,
                                    action='DISPENSE',
                                    quantity=-b.quantity,
                                    performed_by=request.user.username,
                                    notes=f'Dispensed for prescription #{source_id}'
                                )
                                
                                b.quantity = 0
                                b.save()
                        
                        if remaining_quantity > 0:
                            return Response(
                                {'error': f'Insufficient stock for {medicine.name}'},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        
                        continue  # Skip the log creation below as we created them in the loop
                    else:
                        # Use specified batch
                        if batch.quantity < quantity:
                            return Response(
                                {'error': f'Insufficient stock in batch {batch.batch_number}'},
                                status=status.HTTP_400_BAD_REQUEST
                            )
                        
                        batch.quantity -= quantity
                        batch.save()
                    
                    action = 'DISPENSE'
                    quantity = -quantity
                
                # Create inventory log entry
                InventoryLog.objects.create(
                    medicine=medicine,
                    batch=batch,
                    action=action,
                    quantity=quantity,
                    performed_by=request.user.username,
                    notes=f'{source_type.capitalize()} #{source_id}'
                )
                
            except Medicine.DoesNotExist:
                return Response(
                    {'error': f'Medicine with ID {medicine_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except Batch.DoesNotExist:
                return Response(
                    {'error': f'Batch with ID {batch_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response({'status': 'success'})

class BatchViewSet(viewsets.ModelViewSet):
    queryset = Batch.objects.all()
    serializer_class = BatchSerializer
    permission_classes = [permissions.IsAuthenticated, RoleBasedPermission]

    role_permissions = {
        'get': ['admin', 'pharmacist'],
        'post': ['admin', 'pharmacist'],
        'put': ['admin', 'pharmacist'],
        'patch': ['admin', 'pharmacist'],
        'delete': ['admin']
    }

    def get_queryset(self):
        medicine_id = self.request.query_params.get('medicine_id')
        if medicine_id:
            return Batch.objects.filter(medicine_id=medicine_id)
        return Batch.objects.all()

    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        days = request.query_params.get('days', 30)
        expiry_date = date.today() + timedelta(days=int(days))
        batches = Batch.objects.filter(expiration_date__lte=expiry_date)
        serializer = self.get_serializer(batches, many=True)
        return Response(serializer.data)

class InventoryLogViewSet(viewsets.ModelViewSet):
    queryset = InventoryLog.objects.all()
    serializer_class = InventoryLogSerializer
    permission_classes = [permissions.IsAuthenticated, RoleBasedPermission]

    role_permissions = {
        'get': ['admin', 'pharmacist'],
        'post': ['admin', 'pharmacist'],
        'put': ['admin'],
        'patch': ['admin'],
        'delete': ['admin']
    }

    def get_queryset(self):
        medicine_id = self.request.query_params.get('medicine_id')
        batch_id = self.request.query_params.get('batch_id')
        action = self.request.query_params.get('action')
        
        queryset = InventoryLog.objects.all()
        if medicine_id:
            queryset = queryset.filter(medicine_id=medicine_id)
        if batch_id:
            queryset = queryset.filter(batch_id=batch_id)
        if action:
            queryset = queryset.filter(action=action)
        return queryset

    def perform_create(self, serializer):
        serializer.save(performed_by=self.request.user.username)
