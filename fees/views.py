"""
Fees views — list fees, record payment, view payment history.

Students see only their own fees. Admins see all and can create fees & record payments.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, DetailView

from fees.models import Fee, Payment
from fees.forms import FeeForm, PaymentForm


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = 'accounts:login'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin_role

    def handle_no_permission(self):
        messages.error(self.request, 'Admin access required.')
        return redirect('dashboard')


class FeeListView(LoginRequiredMixin, ListView):
    model = Fee
    template_name = 'fees/fee_list.html'
    context_object_name = 'fees'
    paginate_by = 20
    login_url = 'accounts:login'

    def get_queryset(self):
        qs = Fee.objects.select_related('student', 'student__user', 'semester')
        if self.request.user.is_student:
            profile = getattr(self.request.user, 'student_profile', None)
            qs = qs.filter(student=profile) if profile else qs.none()
        return qs

    def get_context_data(self, **kw):
        ctx = super().get_context_data(**kw)
        if self.request.user.is_student:
            profile = getattr(self.request.user, 'student_profile', None)
            if profile:
                ctx['total_due'] = sum(f.due_amount for f in Fee.objects.filter(student=profile).exclude(status='paid'))
        return ctx


class FeeCreateView(AdminRequiredMixin, CreateView):
    model = Fee
    form_class = FeeForm
    template_name = 'fees/fee_form.html'
    success_url = reverse_lazy('fees:list')

    def form_valid(self, form):
        messages.success(self.request, 'Fee record created.')
        return super().form_valid(form)


class PaymentView(LoginRequiredMixin, DetailView):
    """View a fee's details and add a payment against it."""
    model = Fee
    template_name = 'fees/payment.html'
    context_object_name = 'fee'
    login_url = 'accounts:login'

    def get_context_data(self, **kw):
        ctx = super().get_context_data(**kw)
        ctx['form'] = PaymentForm(initial={'fee': self.object})
        ctx['payments'] = self.object.payments.all()
        return ctx

    def post(self, request, pk):
        if not request.user.is_admin_role:
            messages.error(request, 'Only admins can record payments.')
            return redirect('fees:payment', pk=pk)
        fee = get_object_or_404(Fee, pk=pk)
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.received_by = request.user
            payment.save()
            messages.success(request, 'Payment recorded.')
        else:
            messages.error(request, 'Invalid payment details.')
        return redirect('fees:payment', pk=pk)


class PaymentHistoryView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'fees/payment_history.html'
    context_object_name = 'payments'
    paginate_by = 20
    login_url = 'accounts:login'

    def get_queryset(self):
        qs = Payment.objects.select_related('fee', 'fee__student', 'received_by')
        if self.request.user.is_student:
            profile = getattr(self.request.user, 'student_profile', None)
            qs = qs.filter(fee__student=profile) if profile else qs.none()
        return qs
