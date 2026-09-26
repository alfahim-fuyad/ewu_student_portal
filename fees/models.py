"""
Fee & Payment models.

A Fee is what a student owes for a given reason (tuition, lab, library,
registration). A Payment is one transaction against a fee — multiple payments
can be made against the same fee.
"""
from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _


class Fee(models.Model):
    """An invoice/charge against a student."""

    class FeeType(models.TextChoices):
        TUITION = 'tuition', _('Tuition')
        LAB = 'lab', _('Lab Fee')
        LIBRARY = 'library', _('Library Fee')
        REGISTRATION = 'registration', _('Registration Fee')
        EXAM = 'exam', _('Exam Fee')
        LATE = 'late', _('Late Fine')
        OTHER = 'other', _('Other')

    class Status(models.TextChoices):
        UNPAID = 'unpaid', _('Unpaid')
        PARTIAL = 'partial', _('Partially Paid')
        PAID = 'paid', _('Paid')

    student = models.ForeignKey(
        'students.Student',
        on_delete=models.CASCADE,
        related_name='fees',
    )
    semester = models.ForeignKey(
        'academics.Semester',
        on_delete=models.CASCADE,
        related_name='fees',
    )
    fee_type = models.CharField(
        max_length=20, choices=FeeType.choices,
        default=FeeType.TUITION,
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=200, blank=True)
    due_date = models.DateField(blank=True, null=True)
    status = models.CharField(
        max_length=10, choices=Status.choices,
        default=Status.UNPAID,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('fee')
        verbose_name_plural = _('fees')

    def __str__(self):
        return f'{self.student.student_id} — {self.get_fee_type_display()} — {self.amount}'

    @property
    def paid_amount(self) -> Decimal:
        total = sum(
            p.amount for p in self.payments.filter(is_verified=True)
        )
        return Decimal(total or 0)

    @property
    def due_amount(self) -> Decimal:
        return Decimal(self.amount) - self.paid_amount

    def refresh_status(self):
        paid = self.paid_amount
        if paid <= 0:
            self.status = self.Status.UNPAID
        elif paid >= Decimal(self.amount):
            self.status = self.Status.PAID
        else:
            self.status = self.Status.PARTIAL
        self.save(update_fields=['status', 'updated_at'])


class Payment(models.Model):
    """A single payment transaction against a Fee."""

    fee = models.ForeignKey(
        Fee,
        on_delete=models.CASCADE,
        related_name='payments',
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(
        max_length=20,
        choices=[('cash', 'Cash'), ('bank', 'Bank'), ('online', 'Online'), ('card', 'Card')],
        default='cash',
    )
    transaction_id = models.CharField(max_length=100, blank=True)
    paid_at = models.DateTimeField(auto_now_add=True)
    received_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='received_payments',
    )
    is_verified = models.BooleanField(default=True)
    note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-paid_at']
        verbose_name = _('payment')
        verbose_name_plural = _('payments')

    def __str__(self):
        return f'Payment {self.amount} for Fee #{self.fee_id}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update parent Fee status
        self.fee.refresh_status()
