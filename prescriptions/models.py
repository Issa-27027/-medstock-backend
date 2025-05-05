from django.db import models
from django.contrib.auth.models import User
from inventory.models import Medicine
from patients.models import Patient
from datetime import date

class Prescription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    prescribed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    staff_id = models.CharField(max_length=50, blank=True, null=True)
    prescriber_contact = models.CharField(max_length=100, blank=True, null=True)
    date_prescribed = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField(default=date(2024, 1, 1))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    notes = models.TextField(blank=True)
    special_instructions = models.TextField(blank=True)
    refill_count = models.PositiveIntegerField(default=0)
    max_refills = models.PositiveIntegerField(default=0)
    last_refill_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Prescription for {self.patient.name} on {self.date_prescribed.date()}"

    def can_refill(self):
        return self.status == 'active' and self.refill_count < self.max_refills

class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    drug_name = models.CharField(max_length=200, blank=True, null=True)
    dosage = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    frequency = models.CharField(max_length=100)  # e.g., "twice daily", "every 8 hours"
    duration = models.CharField(max_length=100)  # e.g., "7 days", "until finished"
    route = models.CharField(max_length=50)  # e.g., "oral", "intravenous"
    special_instructions = models.TextField(blank=True)

    def __str__(self):
        return f"{self.quantity}x {self.medicine.name} for {self.prescription.patient.name}"

class PrescriptionHistory(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE)
    action = models.CharField(max_length=50)  # e.g., "created", "refilled", "cancelled"
    performed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.action} on {self.prescription} by {self.performed_by.username}"

# Create your models here.
