from rest_framework import serializers
from .models import Supplier, Category, Medicine, Batch, InventoryLog

class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ['id', 'name', 'contact_person', 'phone', 'email', 'address', 'created_at', 'updated_at']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']

class BatchSerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer(read_only=True)
    supplier_id = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(),
        source='supplier',
        write_only=True
    )
    days_until_expiry = serializers.SerializerMethodField()

    class Meta:
        model = Batch
        fields = ['id', 'batch_number', 'expiration_date', 'quantity',
                 'cost_per_unit', 'supplier', 'supplier_id', 'days_until_expiry', 'created_at']
        read_only_fields = ['created_at']

    def get_days_until_expiry(self, obj):
        from datetime import date
        today = date.today()
        return (obj.expiration_date - today).days

class MedicineSerializer(serializers.ModelSerializer):
    supplier = SupplierSerializer(read_only=True)
    supplier_id = serializers.PrimaryKeyRelatedField(
        queryset=Supplier.objects.all(),
        source='supplier',
        write_only=True
    )
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        write_only=True
    )
    batches = BatchSerializer(many=True, read_only=True)
    total_quantity = serializers.SerializerMethodField()
    low_stock = serializers.SerializerMethodField()

    class Meta:
        model = Medicine
        fields = ['id', 'name', 'barcode', 'category', 'category_id',
                 'min_quantity', 'supplier', 'supplier_id',
                 'price_per_unit', 'batches', 'total_quantity', 'low_stock',
                 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

    def get_total_quantity(self, obj):
        return sum(batch.quantity for batch in obj.batches.all())

    def get_low_stock(self, obj):
        return self.get_total_quantity(obj) <= obj.min_quantity

class InventoryLogSerializer(serializers.ModelSerializer):
    medicine = MedicineSerializer(read_only=True)
    medicine_id = serializers.PrimaryKeyRelatedField(
        queryset=Medicine.objects.all(),
        source='medicine',
        write_only=True
    )
    batch = BatchSerializer(read_only=True)
    batch_id = serializers.PrimaryKeyRelatedField(
        queryset=Batch.objects.all(),
        source='batch',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = InventoryLog
        fields = ['id', 'medicine', 'medicine_id', 'batch', 'batch_id',
                 'action', 'quantity', 'timestamp', 'performed_by', 'notes']
        read_only_fields = ['timestamp'] 