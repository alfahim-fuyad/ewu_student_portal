from django.contrib import admin
from fees.models import Fee, Payment


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ('student', 'semester', 'fee_type', 'amount', 'status', 'due_date')
    list_filter = ('fee_type', 'status', 'semester')
    search_fields = ('student__student_id', 'description')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('fee', 'amount', 'method', 'paid_at', 'received_by', 'is_verified')
    list_filter = ('method', 'is_verified')
    search_fields = ('transaction_id', 'fee__student__student_id')
