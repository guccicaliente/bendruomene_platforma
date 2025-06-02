import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import SystemAdmin

# Create superuser if it doesn't exist
if not User.objects.filter(username='sisadmin').exists():
    User.objects.create_superuser('sisadmin', 'admin@example.com', 'admin123')
    print("Superuser 'sisadmin' created successfully!")
else:
    print("Superuser 'sisadmin' already exists!")

# Create SystemAdmin if it doesn't exist
if not SystemAdmin.objects.filter(user__username='sisadmin').exists():
    user = User.objects.get(username='sisadmin')
    SystemAdmin.objects.create(user=user, is_active=True)
    print("SystemAdmin created successfully!")
else:
    print("SystemAdmin already exists!") 