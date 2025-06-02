from django import forms
from django.contrib import admin
from .models import ChatMessage, Apartment, Resident, Notification, Document, Maintenance, VotingTopic, Vote, Complaint, AuditLog, SystemAlert, BackupRestore, Settings
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import UserCreationForm
from django.db import models
from django.urls import path, reverse, re_path
from django.template.response import TemplateResponse
from django.contrib.admin import AdminSite
from django.http import HttpResponseRedirect, FileResponse, JsonResponse
import os
import tempfile
from django.core.management import call_command
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import json
from django.utils.html import format_html
from django.contrib.auth.admin import UserAdmin
from core.models import log_action
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

admin.site.site_header = "Sistemos administravimas"
admin.site.site_title = "Sistemos administravimas"
admin.site.index_title = "Sistemos administravimas"

class ApartmentAdmin(admin.ModelAdmin):
    list_display = ('number', 'floor', 'residents_count', 'residents_list')
    search_fields = ('number',)
    list_filter = ('floor',)

    def residents_count(self, obj):
        return Resident.objects.filter(apartment=obj).count()
    residents_count.short_description = 'Gyventojų skaičius'

    def residents_list(self, obj):
        residents = Resident.objects.filter(apartment=obj)
        return ", ".join([f"{r.first_name} {r.last_name}" for r in residents]) or "-"
    residents_list.short_description = 'Gyventojai'

class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('title', 'apartment', 'created_at', 'is_resolved')
    list_filter = ('is_resolved', 'created_at', 'apartment')
    search_fields = ('title', 'description', 'apartment__number')
    actions = ['mark_as_resolved']

    def mark_as_resolved(self, request, queryset):
        updated = queryset.update(is_resolved=True)
        self.message_user(request, f"{updated} skundų pažymėta kaip išspręsti.")
    mark_as_resolved.short_description = "Pažymėti kaip išspręstus"

admin.site.register(Apartment, ApartmentAdmin)
admin.site.register(Notification)
admin.site.register(Resident)
admin.site.register(Document)
admin.site.register(Maintenance)
admin.site.register(VotingTopic)
admin.site.register(Vote)
admin.site.register(Complaint, ComplaintAdmin)
admin.site.register(ChatMessage) 

class GroupListFilter(admin.SimpleListFilter):
    title = 'Grupė'
    parameter_name = 'group'

    def lookups(self, request, model_admin):
        return [
            ('Namo administratoriai', 'Namo administratoriai'),
            ('Gyventojai', 'Gyventojai'),
        ]

    def queryset(self, request, queryset):
        if self.value() == 'Namo administratoriai':
            return queryset.filter(groups__name='Namo administratoriai')
        if self.value() == 'Gyventojai':
            return queryset.filter(groups__name='Gyventojai')
        return queryset

class SettingsAdmin(admin.ModelAdmin):
    list_display = ('key', 'value')
    search_fields = ('key',)
    list_editable = ('value',)
    list_per_page = 50

admin.site.register(Settings, SettingsAdmin)

class CustomAdminSite(AdminSite):
    site_header = "Sistemos administravimas"
    site_title = "Sistemos administravimas"
    index_title = "Sistemos administravimas"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('statistika/', self.admin_view(self.stats_view), name='stats'),
        ]
        return custom_urls + urls

    def stats_view(self, request):
        from .models import User, Document, Notification, VotingTopic, Complaint
        stats = {
            'users': User.objects.count(),
            'documents': Document.objects.count(),
            'notifications': Notification.objects.count(),
            'voting_topics': VotingTopic.objects.count(),
            'complaints': Complaint.objects.count(),
        }
        return TemplateResponse(request, 'admin/stats.html', {'stats': stats})

custom_admin_site = CustomAdminSite()

class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "model_name", "object_id", "action", "user")
    search_fields = ("model_name", "object_id", "user__username", "changes")
    list_filter = ("action", "model_name", "user")
    readonly_fields = ("timestamp", "model_name", "object_id", "action", "user", "changes")
    ordering = ("-timestamp",)

admin.site.register(AuditLog, AuditLogAdmin)

class SystemAlertAdmin(admin.ModelAdmin):
    list_display = ("created_at", "alert_type", "title", "is_read")
    search_fields = ("title", "message")
    list_filter = ("alert_type", "is_read")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

admin.site.register(SystemAlert, SystemAlertAdmin)

def backup_restore_view(request):
    context = {
        'app_label': 'core',
        'title': 'Atsarginės kopijos',
    }
    return render(request, 'admin/backup_restore.html', context)

admin.site.get_urls = (lambda get_urls: lambda: [
    re_path(r'^backup-restore/$', admin.site.admin_view(backup_restore_view), name='backup-restore'),
] + get_urls())(admin.site.get_urls)

# Užregistruoju User modelį su UserAdmin
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

class AuditLogUserAdmin(UserAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        log_action(request.user, 'update' if change else 'create', obj.__class__.__name__, obj.pk, changes=str(form.cleaned_data))
    def delete_model(self, request, obj):
        log_action(request.user, 'delete', obj.__class__.__name__, obj.pk)
        super().delete_model(request, obj)

admin.site.register(User, AuditLogUserAdmin)

class AuditLogResidentAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        log_action(request.user, 'update' if change else 'create', obj.__class__.__name__, obj.pk, changes=str(form.cleaned_data))
    def delete_model(self, request, obj):
        log_action(request.user, 'delete', obj.__class__.__name__, obj.pk)
        super().delete_model(request, obj)

admin.site.unregister(Resident)
admin.site.register(Resident, AuditLogResidentAdmin)

class AuditLogDocumentAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        log_action(request.user, 'update' if change else 'create', obj.__class__.__name__, obj.pk, changes=str(form.cleaned_data))
    def delete_model(self, request, obj):
        log_action(request.user, 'delete', obj.__class__.__name__, obj.pk)
        super().delete_model(request, obj)

admin.site.unregister(Document)
admin.site.register(Document, AuditLogDocumentAdmin)

# Prisijungimų logginimas
@receiver(user_logged_in)
def log_admin_login(sender, request, user, **kwargs):
    if request.path.startswith('/admin/'):
        log_action(user, 'login', 'admin', '-', changes='Prisijungimas prie admin')

@receiver(user_logged_out)
def log_admin_logout(sender, request, user, **kwargs):
    if request.path.startswith('/admin/'):
        log_action(user, 'logout', 'admin', '-', changes='Atsijungimas nuo admin') 