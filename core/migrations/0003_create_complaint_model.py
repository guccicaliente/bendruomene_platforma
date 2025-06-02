from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_update_resident_model'),
    ]

    operations = [
        migrations.CreateModel(
            name='Complaint',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Pavadinimas')),
                ('description', models.TextField(verbose_name='Aprašymas')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Sukurta')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atnaujinta')),
                ('is_resolved', models.BooleanField(default=False, verbose_name='Išspręsta')),
                ('apartment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.apartment', verbose_name='Butas')),
            ],
            options={
                'verbose_name': 'Skundas',
                'verbose_name_plural': 'Skundai',
                'ordering': ['-created_at'],
            },
        ),
    ] 