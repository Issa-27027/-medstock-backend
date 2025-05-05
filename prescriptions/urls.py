from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PatientViewSet, PrescriptionViewSet, PrescriptionItemViewSet
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Prescription, PrescriptionItem
from django.contrib.auth.models import User
from patients.models import Patient
from inventory.models import Medicine
from datetime import date

router = DefaultRouter()
router.register(r'patients', PatientViewSet)
router.register(r'prescriptions', PrescriptionViewSet)
router.register(r'prescription-items', PrescriptionItemViewSet)

@api_view(['POST'])
def test_post(request):
    # This is just a test endpoint to see if POST requests work
    print("POST request received!")
    return Response({"message": "POST request received!"})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_prescription(request):
    """
    A simple function-based view to create prescriptions directly.
    This bypasses the ViewSet permissions for testing.
    """
    try:
        print("======= Create prescription request received =======")
        print(f"User: {request.user.username}")
        print(f"Request data: {request.data}")
        
        # Get patient
        patient_id = request.data.get('patient_id')
        if not patient_id:
            print("Error: No patient_id provided")
            return Response({"error": "Patient ID is required"}, status=400)
        
        try:
            # Use the Patient model from patients app, not prescriptions
            patient = Patient.objects.get(id=patient_id)
            print(f"Found patient: {patient.name} (ID: {patient.id})")
        except Patient.DoesNotExist:
            print(f"Error: Patient with ID {patient_id} not found")
            return Response({"error": f"Patient with ID {patient_id} not found"}, status=404)
        
        # Set default expiry date if none provided
        expiry_date = request.data.get('expiry_date')
        if not expiry_date:
            expiry_date = date(2024, 1, 1)  # Default expiry date
            print(f"Using default expiry date: {expiry_date}")
        else:
            print(f"Using provided expiry date: {expiry_date}")
            
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
        print(f"Creating prescription with data: {prescription_data}")
        
        prescription = Prescription.objects.create(**prescription_data)
        print(f"Prescription created successfully with ID: {prescription.id}")
        
        # Add items
        items_data = request.data.get('items', [])
        print(f"Processing {len(items_data)} medication items")
        
        for i, item_data in enumerate(items_data):
            print(f"Processing item {i+1}/{len(items_data)}: {item_data}")
            # Get medicine
            medicine_id = item_data.get('medicine_id')
            if not medicine_id:
                print(f"Skipping item {i+1}: No medicine_id provided")
                continue
                
            try:
                medicine = Medicine.objects.get(id=medicine_id)
                print(f"Found medicine: {medicine.name} (ID: {medicine.id})")
            except Medicine.DoesNotExist:
                print(f"Medicine with ID {medicine_id} not found, skipping")
                continue
                
            # Create prescription item
            item = PrescriptionItem.objects.create(
                prescription=prescription,
                medicine=medicine,
                drug_name=item_data.get('drug_name', ''),
                dosage=item_data.get('dosage', ''),
                quantity=item_data.get('quantity', 1),
                frequency=item_data.get('frequency', ''),
                duration=item_data.get('duration', ''),
                route=item_data.get('route', 'oral'),
                special_instructions=item_data.get('special_instructions', '')
            )
            print(f"Created PrescriptionItem with ID: {item.id}")
        
        # Verify the prescription was created successfully
        saved_prescription = Prescription.objects.get(id=prescription.id)
        print(f"Verified prescription exists in database: ID={saved_prescription.id}, patient={saved_prescription.patient.name}")
        print(f"Item count: {saved_prescription.items.count()}")
        
        # Create a history entry
        from .models import PrescriptionHistory
        PrescriptionHistory.objects.create(
            prescription=prescription,
            action='created',
            performed_by=request.user,
            notes='Created via API'
        )
        print("Created prescription history entry")
        
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

urlpatterns = [
    path('', include(router.urls)),
    path('test-post/', test_post, name='test-post'),
    path('create/', create_prescription, name='create-prescription'),
] 