
from django.contrib import admin
from django.urls import path, include
from apps.students import views as student_views
from apps.core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', student_views.public_home, name='home'),

    # path('students/dashboard/', student_views.StudentDashboardView.as_view(), name='student-dashboard'),

    # Auth URLs
    path('accounts/', include('apps.auth.urls')),
    path('academics/', include('apps.academics.urls')),
    path('analytics/', include('apps.analytics.urls')),
    path('attendance/', include('apps.attendance.urls', namespace='attendance')),
    path('communications/', include('apps.communications.urls')),
    path('admission/', include('apps.admission.urls', namespace='admission')),
    path('exams/', include('apps.exams.urls', namespace='exams')),
    path('events/', include('apps.events.urls', namespace='events')),
    path('library/', include('apps.library.urls', namespace='library')),
    path('finance/', include('apps.finance.urls', namespace='finance')),
    path('hostel/', include('apps.hostel.urls', namespace='hostel')),
    path('hr/', include('apps.hr.urls', namespace='hr')),
    path('inventory/', include('apps.inventory.urls', namespace='inventory')),
    path('security/', include('apps.security.urls', namespace='security')),
    path('students/', include('apps.students.urls', namespace='students')),
    path('', include('apps.tenants.urls', namespace='tenants')),
    path('transportation/', include('apps.transportation.urls', namespace='transportation')),
    path('users/', include('apps.users.urls', namespace='users')),
 

    path('configuration/', include('apps.configuration.urls', namespace='configuration')),
    
    # Master Dashboard
    path('dashboard/', core_views.MasterDashboardView.as_view(), name='master_dashboard'),
    
    path('', include('apps.public.urls')),
    # path('accounts/login/', core_views.auth_signin, name='login'),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


# ============================================
# ERROR HANDLERS
# ============================================

handler404 = 'apps.core.views.custom_page_not_found_view'
handler500 = 'apps.core.views.custom_error_view'
handler403 = 'apps.core.views.custom_permission_denied_view'
handler400 = 'apps.core.views.custom_bad_request_view'