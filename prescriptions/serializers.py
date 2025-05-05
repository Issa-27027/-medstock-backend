from rest_framework import serializers
from django.contrib.auth.models import User
from inventory.models import Medicine
from patients.models import Patient
from .models import Prescription, PrescriptionItem, PrescriptionHistory
from patients.serializers import PatientSerializer
from inventory.serializers import MedicineSerializer


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']

class PrescriptionItemSerializer(serializers.ModelSerializer):
    medicine = MedicineSerializer(read_only=True)
    medicine_id = serializers.PrimaryKeyRelatedField(
        queryset=Medicine.objects.all(),
        source='medicine',
        write_only=True
    )

    class Meta:
        model = PrescriptionItem
        fields = '__all__'

class PrescriptionHistorySerializer(serializers.ModelSerializer):
    performed_by = UserSerializer(read_only=True)

    class Meta:
        model = PrescriptionHistory
        fields = '__all__'
        read_only_fields = ['performed_by', 'timestamp']

class PrescriptionSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    patient_id = serializers.PrimaryKeyRelatedField(
        queryset=Patient.objects.all(),
        source='patient',
        write_only=True
    )
    prescribed_by = UserSerializer(read_only=True)
    items = PrescriptionItemSerializer(many=True, read_only=True)
    history = PrescriptionHistorySerializer(many=True, read_only=True)
    can_refill = serializers.SerializerMethodField()

    class Meta:
        model = Prescription
        fields = '__all__'
        read_only_fields = ['prescribed_by', 'date_prescribed', 'refill_count', 'last_refill_date']

    def get_can_refill(self, obj):
        return obj.can_refill()

    def create(self, validated_data):
        prescription = Prescription.objects.create(
            **validated_data,
            prescribed_by=self.context['request'].user
        )
        # Create history entry
        PrescriptionHistory.objects.create(
            prescription=prescription,
            action='created',
            performed_by=self.context['request'].user
        )
        return prescription

    def update(self, instance, validated_data):
        # Create history entry before update
        PrescriptionHistory.objects.create(
            prescription=instance,
            action='updated',
            performed_by=self.context['request'].user
        )
        return super().update(instance, validated_data) 