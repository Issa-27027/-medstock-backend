from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Prescription, PrescriptionItem, PrescriptionHistory
from patients.models import Patient
from .serializers import (
    PatientSerializer, PrescriptionSerializer, PrescriptionItemSerializer,
    PrescriptionHistorySerializer
)
from datetime import datetime, timedelta, date
from django.db.models import Count, Q
from django.utils import timezone
from core.permissions import (
    IsAdmin, IsDoctor, IsPharmacist, 
    IsAdminOrDoctor, IsAdminOrPharmacist, 
    RoleBasedPermission
)

# Create your views here.

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'])
    def prescriptions(self, request, pk=None):
        patient = self.get_object()
        prescriptions = Prescription.objects.filter(patient=patient)
        serializer = PrescriptionSerializer(prescriptions, many=True)
        return Response(serializer.data)

class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all()
    serializer_class = PrescriptionSerializer
    permission_classes = [permissions.IsAuthenticated, RoleBasedPermission]

    role_permissions = {
        'get': ['admin', 'doctor', 'pharmacist'],
        'post': ['admin', 'doctor'],
        'put': ['admin', 'doctor'],
        'patch': ['admin', 'doctor'],
        'delete': ['admin']
    }

    def get_queryset(self):
        print("PrescriptionViewSet.get_queryset() called")
        queryset = Prescription.objects.all()
        
        # Debug: Print out all prescriptions in the database
        all_prescriptions = Prescription.objects.all()
        print(f"All prescriptions in database: {all_prescriptions.count()}")
        for p in all_prescriptions:
            print(f"ID: {p.id}, Patient: {p.patient.name}, Status: {p.status}")
        
        # If user is not admin, filter based on role
        role = getattr(self.request.user, 'userprofile', None)
        if role:
            role = role.role
            print(f"User role: {role}")
            if role != 'admin':
                if role == 'doctor':
                    print(f"Filtering for doctor: {self.request.user.username}")
                    queryset = queryset.filter(prescribed_by=self.request.user)
                elif role == 'pharmacist':
                    print("Filtering for pharmacist (active/pending only)")
                    # Pharmacists can see all active and pending prescriptions
                    queryset = queryset.filter(status__in=['active', 'pending'])
        else:
            print("No user role found, providing all prescriptions")
        
        # Filter by patient
        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            print(f"Filtering by patient ID: {patient_id}")
            queryset = queryset.filter(patient_id=patient_id)
        
        # Filter by status
        status = self.request.query_params.get('status')
        if status:
            print(f"Filtering by status: {status}")
            queryset = queryset.filter(status=status)
        
        # Filter by priority
        priority = self.request.query_params.get('priority')
        if priority:
            print(f"Filtering by priority: {priority}")
            queryset = queryset.filter(priority=priority)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date and end_date:
            print(f"Filtering by date range: {start_date} to {end_date}")
            queryset = queryset.filter(
                date_prescribed__range=[start_date, end_date]
            )
        
        # Debug: Print final filtered queryset
        print(f"Final filtered queryset: {queryset.count()} prescriptions")
        for p in queryset:
            print(f"ID: {p.id}, Patient: {p.patient.name}, Status: {p.status}")
            
        return queryset

    def perform_create(self, serializer):
        print("Creating prescription with data:", self.request.data)
        # Check if the specific fields are in the request data
        staff_id = self.request.data.get('staff_id')
        prescriber_contact = self.request.data.get('prescriber_contact')
        notes = self.request.data.get('notes')
        
        print(f"Staff ID: {staff_id}")
        print(f"Prescriber Contact: {prescriber_contact}")
        print(f"Notes: {notes}")
        
        # Save with all fields
        instance = serializer.save(
            prescribed_by=self.request.user,
            staff_id=staff_id,
            prescriber_contact=prescriber_contact,
            notes=notes
        )
        print(f"Prescription created with ID: {instance.id}")
        return instance

    def perform_update(self, serializer):
        print("Updating prescription with data:", self.request.data)
        # Check if the specific fields are in the request data
        staff_id = self.request.data.get('staff_id')
        prescriber_contact = self.request.data.get('prescriber_contact')
        notes = self.request.data.get('notes')
        
        print(f"Staff ID: {staff_id}")
        print(f"Prescriber Contact: {prescriber_contact}")
        print(f"Notes: {notes}")
        
        # Update with all fields if they're provided
        update_data = {}
        if staff_id is not None:
            update_data['staff_id'] = staff_id
        if prescriber_contact is not None:
            update_data['prescriber_contact'] = prescriber_contact
        if notes is not None:
            update_data['notes'] = notes
            
        instance = serializer.save(**update_data)
        print(f"Prescription updated: {instance.id}")
        
        # Create history entry
        PrescriptionHistory.objects.create(
            prescription=instance,
            action='updated',
            performed_by=self.request.user,
            notes='Updated via API'
        )
        return instance

    @action(detail=False, methods=['get'])
    def recent(self, request):
        days = int(request.query_params.get('days', 7))
        date_threshold = timezone.now() - timedelta(days=days)
        prescriptions = self.get_queryset().filter(
            date_prescribed__gte=date_threshold
        ).order_by('-date_prescribed')
        serializer = self.get_serializer(prescriptions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        prescriptions = self.get_queryset().filter(status='active')
        serializer = self.get_serializer(prescriptions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expired(self, request):
        prescriptions = self.get_queryset().filter(
            Q(status='active') & Q(expiry_date__lt=timezone.now().date())
        )
        serializer = self.get_serializer(prescriptions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def refill(self, request, pk=None):
        if not request.user.userprofile.role in ['admin', 'pharmacist']:
            return Response(
                {'error': 'Only pharmacists can refill prescriptions'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        prescription = self.get_object()
        if not prescription.can_refill():
            return Response(
                {'error': 'Prescription cannot be refilled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        prescription.refill_count += 1
        prescription.last_refill_date = timezone.now()
        prescription.save()
        
        # Create history entry
        PrescriptionHistory.objects.create(
            prescription=prescription,
            action='refilled',
            performed_by=request.user
        )
        
        serializer = self.get_serializer(prescription)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        if not request.user.userprofile.role in ['admin', 'doctor']:
            return Response(
                {'error': 'Only doctors can cancel prescriptions'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        prescription = self.get_object()
        if prescription.status != 'active':
            return Response(
                {'error': 'Only active prescriptions can be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        prescription.status = 'cancelled'
        prescription.save()
        
        # Create history entry
        PrescriptionHistory.objects.create(
            prescription=prescription,
            action='cancelled',
            performed_by=request.user,
            notes=request.data.get('notes', '')
        )
        
        serializer = self.get_serializer(prescription)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        if not request.user.userprofile.role in ['admin', 'doctor']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Get date range
        days = int(request.query_params.get('days', 30))
        date_threshold = timezone.now() - timedelta(days=days)
        
        # Get base queryset
        queryset = self.get_queryset().filter(date_prescribed__gte=date_threshold)
        
        # Calculate statistics
        total_prescriptions = queryset.count()
        
        active_prescriptions = queryset.filter(
            status='active'
        ).count()
        
        expired_prescriptions = queryset.filter(
            Q(status='active') & Q(expiry_date__lt=timezone.now().date())
        ).count()
        
        prescriptions_by_status = queryset.values('status').annotate(
            count=Count('id')
        )
        
        prescriptions_by_priority = queryset.values('priority').annotate(
            count=Count('id')
        )
        
        return Response({
            'total_prescriptions': total_prescriptions,
            'active_prescriptions': active_prescriptions,
            'expired_prescriptions': expired_prescriptions,
            'by_status': list(prescriptions_by_status),
            'by_priority': list(prescriptions_by_priority)
        })

class PrescriptionItemViewSet(viewsets.ModelViewSet):
    queryset = PrescriptionItem.objects.all()
    serializer_class = PrescriptionItemSerializer
    permission_classes = [permissions.IsAuthenticated, RoleBasedPermission]

    role_permissions = {
        'get': ['admin', 'doctor', 'pharmacist'],
        'post': ['admin', 'doctor'],
        'put': ['admin', 'doctor'],
        'patch': ['admin', 'doctor'],
        'delete': ['admin']
    }

    def get_queryset(self):
        queryset = PrescriptionItem.objects.all()
        prescription_id = self.request.query_params.get('prescription_id')
        if prescription_id:
            queryset = queryset.filter(prescription_id=prescription_id)
            
        # If user is not admin, filter based on role
        if not self.request.user.userprofile.role == 'admin':
            if self.request.user.userprofile.role == 'doctor':
                queryset = queryset.filter(prescription__prescribed_by=self.request.user)
            elif self.request.user.userprofile.role == 'pharmacist':
                # Pharmacists can see items from active and pending prescriptions
                queryset = queryset.filter(prescription__status__in=['active', 'pending'])
                
        return queryset

    def perform_create(self, serializer):
        print("Creating prescription item with data:", self.request.data)
        # Check for specific fields in the request data
        drug_name = self.request.data.get('drug_name')
        dosage = self.request.data.get('dosage')
        quantity = self.request.data.get('quantity')
        frequency = self.request.data.get('frequency')
        duration = self.request.data.get('duration')
        route = self.request.data.get('route')
        special_instructions = self.request.data.get('special_instructions')
        
        print(f"Drug Name: {drug_name}")
        print(f"Dosage: {dosage}")
        print(f"Quantity: {quantity}")
        print(f"Frequency: {frequency}")
        print(f"Duration: {duration}")
        print(f"Route: {route}")
        print(f"Special Instructions: {special_instructions}")
        
        # Save with all fields
        instance = serializer.save(
            drug_name=drug_name,
            dosage=dosage,
            quantity=quantity if quantity else 1,
            frequency=frequency,
            duration=duration,
            route=route if route else 'oral',
            special_instructions=special_instructions
        )
        print(f"Prescription item created with ID: {instance.id}")
        return instance
        
    def perform_update(self, serializer):
        print("Updating prescription item with data:", self.request.data)
        # Check for specific fields in the request data
        drug_name = self.request.data.get('drug_name')
        dosage = self.request.data.get('dosage')
        quantity = self.request.data.get('quantity')
        frequency = self.request.data.get('frequency')
        duration = self.request.data.get('duration')
        route = self.request.data.get('route')
        special_instructions = self.request.data.get('special_instructions')
        
        print(f"Drug Name: {drug_name}")
        print(f"Dosage: {dosage}")
        print(f"Quantity: {quantity}")
        print(f"Frequency: {frequency}")
        print(f"Duration: {duration}")
        print(f"Route: {route}")
        print(f"Special Instructions: {special_instructions}")
        
        # Update with all fields if they're provided
        update_data = {}
        if drug_name is not None:
            update_data['drug_name'] = drug_name
        if dosage is not None:
            update_data['dosage'] = dosage
        if quantity is not None:
            update_data['quantity'] = quantity
        if frequency is not None:
            update_data['frequency'] = frequency
        if duration is not None:
            update_data['duration'] = duration
        if route is not None:
            update_data['route'] = route
        if special_instructions is not None:
            update_data['special_instructions'] = special_instructions
            
        instance = serializer.save(**update_data)
        print(f"Prescription item updated: {instance.id}")
        return instance

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_prescription(request):
    try:
        # Get patient
        patient_id = request.data.get('patient_id')
        if not patient_id:
            return Response(
                {'error': 'Patient ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            patient = Patient.objects.get(id=patient_id)
        except Patient.DoesNotExist:
            return Response(
                {'error': 'Patient not found'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Validate items and check stock
        items_data = request.data.get('items', [])
        if not items_data:
            return Response(
                {'error': 'At least one medication item is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check stock availability for all items
        from inventory.models import Medicine
        insufficient_stock = []
        for item_data in items_data:
            medicine_id = item_data.get('medicine_id')
            quantity = item_data.get('quantity', 1)
            
            try:
                medicine = Medicine.objects.get(id=medicine_id)
                if medicine.quantity < quantity:
                    insufficient_stock.append({
                        'medicine': medicine.name,
                        'required': quantity,
                        'available': medicine.quantity
                    })
            except Medicine.DoesNotExist:
                return Response(
                    {'error': f'Medicine with ID {medicine_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
                
        if insufficient_stock:
            return Response(
                {
                    'error': 'Insufficient stock for some medications',
                    'details': insufficient_stock
                },
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Calculate expiry date (default to 30 days from now)
        expiry_date = request.data.get('expiry_date')
        if not expiry_date:
            expiry_date = date.today() + timedelta(days=30)
            
        # Create prescription
        prescription_data = {
            'patient': patient,
            'prescribed_by': request.user,
            'staff_id': request.data.get('staff_id', ''),
            'prescriber_contact': request.data.get('prescriber_contact', ''),
            'status': request.data.get('status', 'active'),
            'notes': request.data.get('notes', ''),
            'special_instructions': request.data.get('special_instructions', ''),
            'max_refills': request.data.get('max_refills', 0),
            'expiry_date': expiry_date,
            'priority': request.data.get('priority', 'medium')
        }
        
        prescription = Prescription.objects.create(**prescription_data)
        
        # Add items
        for item_data in items_data:
            medicine_id = item_data.get('medicine_id')
            medicine = Medicine.objects.get(id=medicine_id)
            
            PrescriptionItem.objects.create(
                prescription=prescription,
                medicine=medicine,
                drug_name=medicine.name,  # Use medicine name as drug name
                dosage=item_data.get('dosage', ''),
                quantity=item_data.get('quantity', 1),
                frequency=item_data.get('frequency', ''),
                duration=item_data.get('duration', ''),
                route=item_data.get('route', 'oral'),
                special_instructions=item_data.get('special_instructions', '')
            )
            
        # Create history entry
        PrescriptionHistory.objects.create(
            prescription=prescription,
            action='created',
            performed_by=request.user,
            notes='Created via API'
        )
        
        # Generate item details for response
        item_details = []
        for item in prescription.items.all():
            item_details.append({
                "id": item.id,
                "medicine_id": item.medicine.id,
                "medicine_name": item.medicine.name,
                "drug_name": item.drug_name,
                "dosage": item.dosage,
                "quantity": item.quantity,
                "frequency": item.frequency,
                "duration": item.duration,
                "route": item.route,
                "special_instructions": item.special_instructions
            })
        
        return Response({
            "message": "Prescription created successfully", 
            "id": prescription.id,
            "patient": prescription.patient.name,
            "patient_id": prescription.patient.id,
            "status": prescription.status,
            "staff_id": prescription.staff_id,
            "prescriber_contact": prescription.prescriber_contact,
            "date_prescribed": prescription.date_prescribed,
            "expiry_date": prescription.expiry_date,
            "priority": prescription.priority,
            "notes": prescription.notes,
            "special_instructions": prescription.special_instructions,
            "items_count": prescription.items.count(),
            "items": item_details
        })
    except Exception as e:
        print(f"Error creating prescription: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({"error": str(e)}, status=500)
