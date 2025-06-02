from django.db import migrations, models
import django.db.models.deletion

def create_apartments(apps, schema_editor):
    Resident = apps.get_model('core', 'Resident')
    Apartment = apps.get_model('core', 'Apartment')
    
    for resident in Resident.objects.all():
        apartment, created = Apartment.objects.get_or_create(
            number=resident.apartment_number,
            defaults={'floor': int(resident.apartment_number.split('-')[0]) if '-' in resident.apartment_number else 1}
        )

def link_residents_to_apartments(apps, schema_editor):
    Resident = apps.get_model('core', 'Resident')
    Apartment = apps.get_model('core', 'Apartment')
    
    for resident in Resident.objects.all():
        apartment = Apartment.objects.get(number=resident.apartment_number)
        resident.apartment = apartment
        resident.phone = resident.phone_number
        resident.save()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Apartment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(max_length=10, unique=True, verbose_name='Buto numeris')),
                ('floor', models.PositiveIntegerField(verbose_name='Aukštas')),
            ],
            options={
                'verbose_name': 'Butas',
                'verbose_name_plural': 'Butai',
                'ordering': ['number'],
            },
        ),
        migrations.RunPython(create_apartments),
        migrations.AddField(
            model_name='resident',
            name='apartment',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='core.apartment', verbose_name='Butas'),
        ),
        migrations.AddField(
            model_name='resident',
            name='is_owner',
            field=models.BooleanField(default=False, verbose_name='Savininkas'),
        ),
        migrations.RunPython(link_residents_to_apartments),
        migrations.RemoveField(
            model_name='resident',
            name='apartment_number',
        ),
        migrations.RemoveField(
            model_name='resident',
            name='phone_number',
        ),
        migrations.AlterField(
            model_name='resident',
            name='apartment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.apartment', verbose_name='Butas'),
        ),
    ] 