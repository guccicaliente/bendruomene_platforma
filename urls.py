from django.urls import path
from . import views
 
urlpatterns = [
    # ... existing urls ...
    path('admin/login/', views.admin_login, name='admin_login'),
] 