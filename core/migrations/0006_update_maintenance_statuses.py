from django.db import migrations
from django.utils import timezone

def update_maintenance_statuses(apps, schema_editor):
    Maintenance = apps.get_model('core', 'Maintenance')
    today = timezone.now().date()
    
    for maintenance in Maintenance.objects.all():
        if maintenance.end_date:
            if maintenance.end_date < today:
                maintenance.status = 'past'
            elif maintenance.start_date <= today <= maintenance.end_date:
                maintenance.status = 'current'
            else:
                maintenance.status = 'future'
        else:
            if maintenance.start_date > today:
                maintenance.status = 'future'
            elif maintenance.start_date <= today:
                maintenance.status = 'current'
        maintenance.save()

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0005_maintenance_maintenanceimage'),
    ]

    operations = [
        migrations.RunPython(update_maintenance_statuses),
    ] 