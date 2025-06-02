from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from .models import AuditLog, SystemAlert, Complaint
import json
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_login_failed

User = get_user_model()

def get_tracked_models():
    ignore = [AuditLog._meta.label, 'contenttypes.ContentType', 'sessions.Session', 'admin.LogEntry']
    return [m for m in apps.get_models() if m._meta.label not in ignore]

def get_changes(instance):
    if not instance.pk:
        return ""
    try:
        old = instance.__class__.objects.get(pk=instance.pk)
    except instance.__class__.DoesNotExist:
        return ""
    changes = {}
    for field in instance._meta.fields:
        fname = field.name
        old_val = getattr(old, fname, None)
        new_val = getattr(instance, fname, None)
        if old_val != new_val:
            changes[fname] = {'old': str(old_val), 'new': str(new_val)}
    return json.dumps(changes, ensure_ascii=False)

def register_audit_signals():
    for model in get_tracked_models():
        @receiver(post_save, sender=model, weak=False)
        def log_save(sender, instance, created, **kwargs):
            user = getattr(instance, '_audit_user', None)
            AuditLog.objects.create(
                model_name=sender.__name__,
                object_id=str(instance.pk),
                action='create' if created else 'update',
                user=user,
                changes=get_changes(instance) if not created else None
            )
        @receiver(post_delete, sender=model, weak=False)
        def log_delete(sender, instance, **kwargs):
            user = getattr(instance, '_audit_user', None)
            AuditLog.objects.create(
                model_name=sender.__name__,
                object_id=str(instance.pk),
                action='delete',
                user=user
            )

@receiver(post_save, sender=User)
def user_created_alert(sender, instance, created, **kwargs):
    if created:
        SystemAlert.objects.create(
            title="Naujas vartotojas",
            message=f"Sistemoje užregistruotas naujas vartotojas: {instance.username}",
            alert_type="info"
        )

@receiver(post_save, sender=Complaint)
def complaint_created_alert(sender, instance, created, **kwargs):
    if created:
        SystemAlert.objects.create(
            title="Naujas skundas",
            message=f"Gautas naujas skundas: {instance.title}",
            alert_type="warning"
        )

@receiver(user_login_failed)
def login_failed_alert(sender, credentials, request, **kwargs):
    SystemAlert.objects.create(
        title="Nesėkmingas prisijungimas",
        message=f"Nesėkmingas prisijungimas su vardu: {credentials.get('username', '')}",
        alert_type="security"
    )

register_audit_signals() 