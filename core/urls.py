from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('valdymas/dokumentai/', views.documents_view, name='admin_documents'),
    path('notifications/create/', views.create_notification, name='create_notification'),
    path('maintenance/create/', views.create_maintenance, name='create_maintenance'),
    path('', views.login_view, name='login'),
    path('home/', views.home, name='home'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('documents/', views.documents_view, name='documents'),
    path('maintenance/', views.maintenance_list, name='maintenance_list'),
    path('residents/', views.residents_view, name='residents_view'),
    path('residents/<int:resident_id>/', views.get_resident, name='get_resident'),
    path('residents/<int:resident_id>/edit/', views.edit_resident, name='edit_resident'),
    path('residents/<int:resident_id>/delete/', views.delete_resident, name='delete_resident'),
    path('residents/register/', views.register_resident, name='register_resident'),
    path('documents/by-residents/', views.documents_by_residents, name='documents_by_residents'),
    path('documents/by-apartments/', views.documents_by_apartments, name='documents_by_apartments'),
    path('documents/apartment/<str:apartment_number>/', views.apartment_residents, name='apartment_residents'),
    path('documents/resident/<int:resident_id>/', views.resident_documents, name='resident_documents'),
    path('documents/upload/', views.upload_document, name='upload_document'),
    path('documents/delete/<int:document_id>/', views.delete_document, name='delete_document'),
    path('documents/delete-all/', views.delete_all_documents, name='delete_all_documents'),
    path('voting/', views.voting_view, name='voting'),
    path('voting/<int:topic_id>/vote/', views.vote, name='vote'),
    path('voting/<int:topic_id>/stats/', views.get_vote_stats, name='vote_stats'),
    path('valdymas/balsavimai/', views.admin_voting_view, name='admin_voting'),
    path('valdymas/balsavimai/naujas/', views.create_voting, name='create_voting'),
    path('valdymas/balsavimai/<int:pk>/', views.get_voting, name='get_voting'),
    path('valdymas/balsavimai/<int:voting_id>/redaguoti/', views.edit_voting, name='edit_voting'),
    path('valdymas/balsavimai/<int:voting_id>/trinti/', views.delete_voting, name='delete_voting'),
    path('valdymas/balsavimai/<int:voting_id>/uzbaigti/', views.complete_voting, name='complete_voting'),
    
    path('skundai/', views.complaints_view, name='complaints'),
    path('skundai/kurti/', views.create_complaint, name='create_complaint'),
    path('skundai/<int:complaint_id>/', views.get_complaint, name='get_complaint'),
    path('skundai/<int:complaint_id>/redaguoti/', views.edit_complaint, name='edit_complaint'),
    path('skundai/<int:complaint_id>/trinti/', views.delete_complaint, name='delete_complaint'),

    path('kalendorius/', views.calendar_view, name='calendar'),
    path('profilis/', views.profile_view, name='profile'),

    path('chat/', views.chat_view, name='chat'),
    path('chat/send/', views.send_message, name='send_message'),
    path('chat/edit/<int:msg_id>/', views.edit_message, name='edit_message'),
    path('chat/delete/<int:msg_id>/', views.delete_message, name='delete_message'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) 