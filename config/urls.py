"""
URL configuration for student_portal project.

Top-level routes are namespaced by app, and there is a small `core` namespace
under `accounts` that provides the dashboard view (used by all roles after
login).
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from accounts.views import dashboard

urlpatterns = [
    path('admin/', admin.site.urls),

    # Core dashboard (post-login landing page for all roles)
    path('dashboard/', dashboard, name='dashboard'),

    # Apps
    path('accounts/', include(('accounts.urls', 'accounts'), namespace='accounts')),
    path('students/', include(('students.urls', 'students'), namespace='students')),
    path('teachers/', include(('teachers.urls', 'teachers'), namespace='teachers')),
    path('academics/', include(('academics.urls', 'academics'), namespace='academics')),
    path('attendance/', include(('attendance.urls', 'attendance'), namespace='attendance')),
    path('results/', include(('results.urls', 'results'), namespace='results')),
    path('fees/', include(('fees.urls', 'fees'), namespace='fees')),
    path('notices/', include(('notices.urls', 'notices'), namespace='notices')),
    path('chatbot/', include(('chatbot.urls', 'chatbot'), namespace='chatbot')),
]

# Provide a `core:` namespace alias so LOGIN_REDIRECT_URL='core:dashboard' works.
# We register the same view under core namespace as well.
urlpatterns += [
    path('', dashboard, name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
