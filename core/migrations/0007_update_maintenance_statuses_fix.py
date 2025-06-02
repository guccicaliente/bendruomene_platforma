from django.db import migrations
from django.utils import timezone

def update_maintenance_statuses(apps, schema_editor):
    Maintenance = apps.get_model('core', 'Maintenance')
    today = timezone.now().date()
    
    for maintenance in Maintenance.objects.all():
        if maintenance.status == 'past':
            continue
            
        if maintenance.end_date:
            if maintenance.end_date < today:
                maintenance.status = 'past'
            elif maintenance.start_date > today:
                maintenance.status = 'future'
            else:
                maintenance.status = 'current'
        else:
            if maintenance.start_date > today:
                maintenance.status = 'future'
            elif maintenance.start_date < today:
                maintenance.status = 'past'
            else:
                maintenance.status = 'current'
        
        maintenance.save()

class Migration(migrations.Migration):
    dependencies = [
        ('core', '0006_update_maintenance_statuses'),
    ]

    operations = [
        migrations.RunPython(update_maintenance_statuses),
    ] 