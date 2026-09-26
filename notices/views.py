"""
Notices views — list/detail/add/edit.

Anyone logged-in can see notices visible to them.
Only admins (and optionally teachers for their courses) can post notices.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from notices.models import Notice
from notices.forms import NoticeForm


class NoticeListView(LoginRequiredMixin, ListView):
    model = Notice
    template_name = 'notices/list.html'
    context_object_name = 'notices'
    paginate_by = 10
    login_url = 'accounts:login'

    def get_queryset(self):
        return Notice.visible_to(self.request.user)


class NoticeDetailView(LoginRequiredMixin, DetailView):
    model = Notice
    template_name = 'notices/detail.html'
    context_object_name = 'notice'
    login_url = 'accounts:login'

    def get_queryset(self):
        return Notice.visible_to(self.request.user)


class NoticeCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Notice
    form_class = NoticeForm
    template_name = 'notices/add.html'
    success_url = reverse_lazy('notices:list')
    login_url = 'accounts:login'

    def test_func(self):
        u = self.request.user
        return u.is_authenticated and (u.is_admin_role or u.is_teacher)

    def handle_no_permission(self):
        messages.error(self.request, 'You cannot post notices.')
        return redirect('notices:list')

    def form_valid(self, form):
        form.instance.posted_by = self.request.user
        messages.success(self.request, 'Notice posted.')
        return super().form_valid(form)


class NoticeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Notice
    form_class = NoticeForm
    template_name = 'notices/edit.html'
    success_url = reverse_lazy('notices:list')
    login_url = 'accounts:login'

    def test_func(self):
        u = self.request.user
        if not u.is_authenticated:
            return False
        if u.is_admin_role:
            return True
        if u.is_teacher and self.get_object().posted_by == u:
            return True
        return False

    def handle_no_permission(self):
        messages.error(self.request, 'You cannot edit this notice.')
        return redirect('notices:list')


class NoticeDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Notice
    template_name = 'notices/delete.html'
    success_url = reverse_lazy('notices:list')
    login_url = 'accounts:login'

    def test_func(self):
        u = self.request.user
        return u.is_authenticated and (u.is_admin_role or self.get_object().posted_by == u)
