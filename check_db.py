import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from core.models import SystemAdmin

# Check if any users exist
users = User.objects.all()
print(f"Total users in database: {users.count()}")
for user in users:
    print(f"Username: {user.username}, Email: {user.email}, Is staff: {user.is_staff}, Is superuser: {user.is_superuser}")

# Check if any system admins exist
system_admins = SystemAdmin.objects.all()
print(f"\nTotal system admins: {system_admins.count()}")
for admin in system_admins:
    print(f"Admin user: {admin.user.username}, Is active: {admin.is_active}")

# Create a superuser if none exists
if not User.objects.filter(username='sisadmin').exists():
    print("\nCreating superuser 'sisadmin'...")
    User.objects.create_superuser('sisadmin', 'admin@example.com', 'admin123')
    print("Superuser created successfully!") 