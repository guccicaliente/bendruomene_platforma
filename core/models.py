from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    birth_date = models.DateField(verbose_name="Gimimo data", null=True, blank=True)
    phone = models.CharField(max_length=15, verbose_name="Telefono numeris", default="")
    
    class Meta:
        verbose_name = "Vartotojo profilis"
        verbose_name_plural = "Vartotojų profiliai"

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} profilis"

class Resident(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, verbose_name="Vardas")
    last_name = models.CharField(max_length=100, verbose_name="Pavardė")
    apartment = models.ForeignKey('Apartment', on_delete=models.CASCADE, verbose_name="Butas")
    email = models.EmailField(verbose_name="El. paštas")
    phone = models.CharField(max_length=15, verbose_name="Telefono numeris", default="")
    birth_date = models.DateField(null=True, blank=True)
    is_owner = models.BooleanField(default=False, verbose_name="Savininkas")

    class Meta:
        verbose_name = "Gyventojas"
        verbose_name_plural = "Gyventojai"

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.apartment}"

class Apartment(models.Model):
    number = models.CharField(max_length=10, unique=True, verbose_name='Buto numeris')
    floor = models.PositiveIntegerField(verbose_name='Aukštas')
    
    class Meta:
        verbose_name = 'Butas'
        verbose_name_plural = 'Butai'
        ordering = ['number']
    
    def __str__(self):
        return f"Butas {self.number}"

class Document(models.Model):
    DOCUMENT_TYPES = [
        ('contract', 'Nuomos sutartis'),
        ('invoice', 'Sąskaita'),
        ('other', 'Kitas dokumentas')
    ]

    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255, verbose_name="Pavadinimas")
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES, verbose_name="Dokumento tipas")
    file = models.FileField(upload_to='documents/%Y/%m/%d/', verbose_name="Failas")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Įkėlimo data")
    description = models.TextField(blank=True, null=True, verbose_name="Aprašymas")

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Dokumentas"
        verbose_name_plural = "Dokumentai"

    def __str__(self):
        return f"{self.title} - {self.resident}"

    def filename(self):
        return self.file.name.split('/')[-1]

class Notification(models.Model):
    title = models.CharField(max_length=200, verbose_name="Pavadinimas")
    content = models.TextField(verbose_name="Pranešimo turinys")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Sukūrimo laikas")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Sukūrė")
    read_by = models.ManyToManyField(User, related_name='read_notifications', blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Pranešimas"
        verbose_name_plural = "Pranešimai"

    def __str__(self):
        return self.title

    def is_read_by(self, user):
        return self.read_by.filter(id=user.id).exists()

class Maintenance(models.Model):
    STATUS_CHOICES = [
        ('past', 'Atliktas'),
        ('current', 'Dabartinis'),
        ('future', 'Ateities'),
    ]

    title = models.CharField(max_length=200, verbose_name="Pavadinimas")
    description = models.TextField(verbose_name="Aprašymas")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name="Statusas")
    start_date = models.DateField(verbose_name="Pradžios data")
    end_date = models.DateField(verbose_name="Pabaigos data", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Sukūrimo data")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Sukūrė")

    class Meta:
        ordering = ['-start_date']
        verbose_name = "Remontas/darbas"
        verbose_name_plural = "Remontai ir darbai"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        today = timezone.now().date()
        
        if self.status != 'past':
            if self.end_date:
                if self.end_date < today:
                    self.status = 'past'
                elif self.start_date > today:
                    self.status = 'future'
                else:
                    self.status = 'current'
            else:
                if self.start_date > today:
                    self.status = 'future'
                elif self.start_date < today:
                    self.status = 'past'
                else:
                    self.status = 'current'
        
        super().save(*args, **kwargs)

class MaintenanceImage(models.Model):
    maintenance = models.ForeignKey(Maintenance, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='maintenance/%Y/%m/%d/', verbose_name="Nuotrauka")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Remonto nuotrauka"
        verbose_name_plural = "Remonto nuotraukos"

class VotingTopic(models.Model):
    STATUS_CHOICES = [
        ('active', 'Aktyvus'),
        ('completed', 'Užbaigtas'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Pavadinimas")
    description = models.TextField(verbose_name="Aprašymas")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Sukūrimo data")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Sukūrė")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active', verbose_name="Būsena")
    end_date = models.DateField(null=True, blank=True, verbose_name="Pabaigos data")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Užbaigimo data")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Balsavimo tema"
        verbose_name_plural = "Balsavimo temos"

    def __str__(self):
        return self.title

    @property
    def is_active(self):
        return self.status == 'active'

    @property
    def votes_count(self):
        return self.votes.count()

    @property
    def votes_for(self):
        return self.votes.filter(vote_type='for').count()

    @property
    def votes_against(self):
        return self.votes.filter(vote_type='against').count()

class Vote(models.Model):
    VOTE_TYPES = [
        ('for', 'Už'),
        ('against', 'Prieš')
    ]
    
    resident = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name='votes')
    topic = models.ForeignKey(VotingTopic, on_delete=models.CASCADE, related_name='votes', null=True, blank=True)
    vote_type = models.CharField(max_length=7, choices=VOTE_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = [('resident', 'topic')]
        verbose_name = "Balsas"
        verbose_name_plural = "Balsai"

    def __str__(self):
        return f"{self.resident} - {self.get_vote_type_display()} - {self.topic.title if self.topic else 'Be temos'}"

class Complaint(models.Model):
    apartment = models.ForeignKey(Apartment, on_delete=models.CASCADE, verbose_name='Butas')
    title = models.CharField(max_length=200, verbose_name='Pavadinimas')
    description = models.TextField(verbose_name='Aprašymas')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Sukurta')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Atnaujinta')
    is_resolved = models.BooleanField(default=False, verbose_name='Išspręsta')

    class Meta:
        verbose_name = "Skundas"
        verbose_name_plural = "Skundai"
        ordering = ['-created_at']

    def __str__(self):
        return f"Skundas #{self.id} - {self.title}"

    @classmethod
    def can_create_complaint(cls, apartment):
        """Patikrina, ar butas gali kurti naują skundą"""
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        next_month = (current_month + timezone.timedelta(days=32)).replace(day=1)
        
        complaints_this_month = cls.objects.filter(
            apartment=apartment,
            created_at__gte=current_month,
            created_at__lt=next_month
        ).count()
        
        return complaints_this_month < 2

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Siuntėjas')
    content = models.TextField(verbose_name='Žinutė')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        verbose_name = "Chat žinutė"
        verbose_name_plural = "Chat žinutės"

    def __str__(self):
        return f"{self.user}: {self.content[:30]}" 

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("create", "Sukūrimas"),
        ("update", "Keitimas"),
        ("delete", "Ištrynimas"),
    ]
    model_name = models.CharField(max_length=100, verbose_name="Modelis")
    object_id = models.CharField(max_length=50, verbose_name="Objekto ID")
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, verbose_name="Veiksmas")
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="Vartotojas")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Data ir laikas")
    changes = models.TextField(blank=True, null=True, verbose_name="Pokyčiai")

    class Meta:
        verbose_name = "Veiklos žurnalas"
        verbose_name_plural = "Veiklos žurnalas"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.model_name} ({self.object_id}) - {self.get_action_display()}"

class SystemAlert(models.Model):
    ALERT_TYPES = [
        ("info", "Informacija"),
        ("warning", "Įspėjimas"),
        ("error", "Klaida"),
        ("security", "Saugumas"),
    ]
    title = models.CharField(max_length=200, verbose_name="Pavadinimas")
    message = models.TextField(verbose_name="Pranešimo turinys")
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES, default="info", verbose_name="Tipas")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Sukūrimo laikas")
    is_read = models.BooleanField(default=False, verbose_name="Perskaityta")

    class Meta:
        verbose_name = "Sistemos įspėjimas"
        verbose_name_plural = "Sistemos įspėjimai"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_alert_type_display()}: {self.title}"

class BackupRestore(models.Model):
    class Meta:
        verbose_name = 'Atsarginės kopijos'
        verbose_name_plural = 'Atsarginės kopijos'
        app_label = 'core'
        managed = False
    def __str__(self):
        return 'Atsarginės kopijos'

class Settings(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=255)
    class Meta:
        verbose_name = 'Sistemos nustatymas'
        verbose_name_plural = 'Sistemos nustatymai'
    def __str__(self):
        return f"{self.key}: {self.value}"

def get_default_settings():
    return [
        {"key": "site_name", "value": "Bendruomenės platforma"},
        {"key": "support_email", "value": "pagalba@bendruomene.lt"},
        {"key": "maintenance_mode", "value": "off"},
        {"key": "default_language", "value": "lt"},
        {"key": "allow_registration", "value": "true"},
        {"key": "max_upload_size_mb", "value": "10"},
        {"key": "password_min_length", "value": "8"},
        {"key": "session_timeout_minutes", "value": "60"},
        {"key": "enable_notifications", "value": "true"},
        {"key": "show_dashboard_stats", "value": "true"},
        {"key": "default_timezone", "value": "Europe/Vilnius"},
        {"key": "contact_phone", "value": "+37060000000"},
        {"key": "enable_chat", "value": "true"},
        {"key": "max_chat_message_length", "value": "500"},
        {"key": "allow_document_download", "value": "true"},
        {"key": "privacy_policy_url", "value": "https://bendruomene.lt/privatumas"},
        {"key": "terms_of_service_url", "value": "https://bendruomene.lt/taisykles"},
        {"key": "logo_url", "value": ""},
        {"key": "enable_email_verification", "value": "false"},
        {"key": "max_residents_per_apartment", "value": "6"},
    ]

@receiver(post_migrate)
def create_default_settings(sender, **kwargs):
    from .models import Settings
    if sender.name == "core":
        for setting in get_default_settings():
            Settings.objects.get_or_create(key=setting["key"], defaults={"value": setting["value"]})

def get_default_alerts():
    return [
        {"title": "Sveiki prisijungę!", "message": "Sveikiname prisijungus prie bendruomenės platformos.", "alert_type": "info"},
        {"title": "Planuojami darbai", "message": "Rugpjūčio 10 d. bus vykdomi sistemos atnaujinimo darbai.", "alert_type": "warning"},
        {"title": "Aptikta klaida", "message": "Buvo aptikta laikina klaida, kuri jau ištaisyta.", "alert_type": "error"},
        {"title": "Saugumo patarimas", "message": "Niekada nesidalinkite savo slaptažodžiu su kitais.", "alert_type": "security"},
    ]

@receiver(post_migrate)
def create_default_alerts(sender, **kwargs):
    from .models import SystemAlert
    from django.utils import timezone
    if sender.name == "core" and not SystemAlert.objects.exists():
        for alert in get_default_alerts():
            SystemAlert.objects.create(
                title=alert["title"],
                message=alert["message"],
                alert_type=alert["alert_type"],
                created_at=timezone.now(),
                is_read=False
            )

def log_action(user, action, model_name, object_id=None, changes=None):
    from .models import AuditLog
    AuditLog.objects.create(
        model_name=model_name,
        object_id=str(object_id) if object_id else '',
        action=action,
        user=user if user and hasattr(user, 'is_authenticated') and user.is_authenticated else None,
        changes=changes
    )

class SystemAdmin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='system_admin')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Sistemos administratorius"
        verbose_name_plural = "Sistemos administratoriai"

    def __str__(self):
        return f"Sistemos administratorius: {self.user.username}" 