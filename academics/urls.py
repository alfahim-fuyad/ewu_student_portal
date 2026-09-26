"""URL routes for academics app."""
from django.urls import path
from academics.views import (
    DepartmentListView, DepartmentCreateView, DepartmentUpdateView, DepartmentDeleteView,
    SemesterListView, SemesterCreateView, SemesterUpdateView, SemesterDeleteView,
    CourseListView, CourseDetailView, CourseCreateView, CourseUpdateView, CourseDeleteView,
    EnrollmentListView, EnrollmentCreateView,
)

urlpatterns = [
    # Departments
    path('departments/', DepartmentListView.as_view(), name='departments'),
    path('departments/add/', DepartmentCreateView.as_view(), name='department_add'),
    path('departments/<int:pk>/edit/', DepartmentUpdateView.as_view(), name='department_edit'),
    path('departments/<int:pk>/delete/', DepartmentDeleteView.as_view(), name='department_delete'),

    # Semesters
    path('semesters/', SemesterListView.as_view(), name='semesters'),
    path('semesters/add/', SemesterCreateView.as_view(), name='semester_add'),
    path('semesters/<int:pk>/edit/', SemesterUpdateView.as_view(), name='semester_edit'),
    path('semesters/<int:pk>/delete/', SemesterDeleteView.as_view(), name='semester_delete'),

    # Courses
    path('courses/', CourseListView.as_view(), name='courses'),
    path('courses/add/', CourseCreateView.as_view(), name='course_add'),
    path('courses/<int:pk>/', CourseDetailView.as_view(), name='course_detail'),
    path('courses/<int:pk>/edit/', CourseUpdateView.as_view(), name='course_edit'),
    path('courses/<int:pk>/delete/', CourseDeleteView.as_view(), name='course_delete'),

    # Enrollment
    path('enrollment/', EnrollmentListView.as_view(), name='enrollment'),
    path('enrollment/add/', EnrollmentCreateView.as_view(), name='enrollment_add'),
]
