from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from core.views import (
    login_view, home, register_resident,
    create_notification, mark_notification_as_read,
    notifications_view, delete_notification,
    delete_all_notifications, residents_view,
    edit_resident, delete_resident,
    documents_view, upload_document,
    delete_document, delete_all_documents,
    admin_documents, documents_by_residents,
    documents_by_apartments, apartment_residents,
    resident_documents, maintenance_list,
    create_maintenance, delete_maintenance,
    complete_maintenance
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # Include core URLs
    path('login/', login_view, name='login'),
    path('home/', home, name='home'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register-resident/', register_resident, name='register_resident'),
    path('notifications/', notifications_view, name='notifications'),
    path('create-notification/', create_notification, name='create_notification'),
    path('mark-notification-as-read/<int:notification_id>/', mark_notification_as_read, name='mark_notification_as_read'),
    path('delete-notification/<int:notification_id>/', delete_notification, name='delete_notification'),
    path('delete-all-notifications/', delete_all_notifications, name='delete_all_notifications'),
    path('residents/', residents_view, name='residents'),
    path('edit-resident/<int:resident_id>/', edit_resident, name='edit_resident'),
    path('delete-resident/<int:resident_id>/', delete_resident, name='delete_resident'),
    path('documents/', documents_view, name='documents'),
    path('upload-document/', upload_document, name='upload_document'),
    path('delete-document/<int:document_id>/', delete_document, name='delete_document'),
    path('delete-all-documents/', delete_all_documents, name='delete_all_documents'),
    path('admin-documents/', admin_documents, name='admin_documents'),
    path('documents-by-residents/', documents_by_residents, name='documents_by_residents'),
    path('documents-by-apartments/', documents_by_apartments, name='documents_by_apartments'),
    path('apartment-residents/<str:apartment_number>/', apartment_residents, name='apartment_residents'),
    path('resident-documents/<int:resident_id>/', resident_documents, name='resident_documents'),
    path('maintenance/', maintenance_list, name='maintenance_list'),
    path('create-maintenance/', create_maintenance, name='create_maintenance'),
    path('delete-maintenance/<int:maintenance_id>/', delete_maintenance, name='delete_maintenance'),
    path('complete-maintenance/<int:maintenance_id>/', complete_maintenance, name='complete_maintenance'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 