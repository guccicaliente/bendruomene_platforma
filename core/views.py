from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone
from .forms import (
    ResidentRegistrationForm, NotificationForm,
    DocumentForm, MaintenanceForm, VotingTopicForm, ComplaintForm, UserProfileForm
)
from .models import (
    Resident, Notification, Document,
    Maintenance, MaintenanceImage, Vote, VotingTopic, Complaint, Apartment, UserProfile, ChatMessage, SystemAlert
)
import json
from datetime import timedelta
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from core.models import log_action
from django.utils.deprecation import MiddlewareMixin

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        login_type = request.POST.get('login_type')
        
        user = authenticate(request, username=username, password=password)
        log_action(user if user else None, 'login', 'User', username, changes='login_attempt')
        
        if user is not None:
            if login_type == 'admin' and not user.is_staff:
                return render(request, 'login.html', {'error': 'Šis vartotojas neturi administratoriaus teisių', 'attempted': True, 'login_type': login_type})
            elif login_type == 'resident' and user.is_staff:
                return render(request, 'login.html', {'error': 'Administratoriai turi prisijungti kaip administratoriai', 'attempted': True, 'login_type': login_type})
            
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Neteisingas vartotojo vardas arba slaptažodis', 'attempted': True, 'login_type': login_type})
    
    return render(request, 'login.html', {'attempted': False, 'login_type': ''})

@login_required
def home(request):
    unread_count = Notification.objects.exclude(read_by=request.user).count()
    if request.user.is_staff:
        context = {
            'unread_count': unread_count,
        }
        return render(request, 'home_admin.html', context)
    else:
        context = {
            'unread_count': unread_count
        }
        return render(request, 'home.html', context)

@login_required
def notifications_view(request):
    notifications = Notification.objects.all().order_by('-created_at')
    
    unread_notifications = notifications.exclude(read_by=request.user)
    for notification in unread_notifications:
        notification.read_by.add(request.user)
    
    if request.user.is_staff:
        form = NotificationForm()
        context = {
            'notifications': notifications,
            'unread_count': 0,  
            'form': form
        }
    else:
        context = {
            'notifications': notifications,
            'unread_count': 0  
        }
    
    return render(request, 'notifications.html', context)

@user_passes_test(lambda u: u.is_staff)
def register_resident(request):
    if request.method == 'POST':
        form = ResidentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            resident = Resident.objects.create(
                user=user,
                apartment=form.cleaned_data['apartment'],
                phone=form.cleaned_data['phone'],
                birth_date=form.cleaned_data['birth_date'],
                is_owner=form.cleaned_data['is_owner']
            )
            messages.success(request, 'Gyventojas sėkmingai užregistruotas')
            return redirect('residents')
    else:
        residents = Resident.objects.all().select_related('user')
        context = {
            'residents': residents,
            'form': form
        }
        return render(request, 'residents.html', context)
    return redirect('residents')

@user_passes_test(lambda u: u.is_staff)
def create_notification(request):
    if request.method == 'POST':
        form = NotificationForm(request.POST)
        if form.is_valid():
            notification = form.save(commit=False)
            notification.created_by = request.user
            notification.save()
            messages.success(request, 'Pranešimas sėkmingai sukurtas')
            return redirect('notifications')
    return redirect('notifications')

@login_required
def mark_notification_as_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    if request.user not in notification.read_by.all():
        notification.read_by.add(request.user)
    return JsonResponse({'status': 'success'})

@user_passes_test(lambda u: u.is_staff)
def delete_notification(request, notification_id):
    if request.method == 'POST':
        notification = get_object_or_404(Notification, id=notification_id)
        notification.delete()
        messages.success(request, 'Pranešimas sėkmingai ištrintas')
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@user_passes_test(lambda u: u.is_staff)
def delete_all_notifications(request):
    if request.method == 'POST':
        Notification.objects.all().delete()
        messages.success(request, 'Visi pranešimai sėkmingai ištrinti')
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@user_passes_test(lambda u: u.is_staff)
def residents_view(request):
    residents = Resident.objects.all().select_related('user')
    form = ResidentRegistrationForm()
    context = {
        'residents': residents,
        'form': form
    }
    return render(request, 'residents.html', context)

@user_passes_test(lambda u: u.is_staff)
def edit_resident(request, resident_id):
    if request.method == 'POST':
        resident = get_object_or_404(Resident, id=resident_id)
        user = resident.user

        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.save()

        apartment_id = request.POST.get('apartment')
        apartment = get_object_or_404(Apartment, id=apartment_id)
        resident.apartment = apartment
        resident.phone = request.POST.get('phone')
        resident.birth_date = request.POST.get('birth_date')
        resident.is_owner = request.POST.get('is_owner') == 'true'
        resident.save()

        messages.success(request, 'Gyventojo informacija sėkmingai atnaujinta')
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)

@user_passes_test(lambda u: u.is_staff)
def delete_resident(request, resident_id):
    if request.method == 'POST':
        resident = get_object_or_404(Resident, id=resident_id)
        user = resident.user
        
        resident.delete()
        user.delete()
        
        messages.success(request, 'Gyventojas sėkmingai ištrintas')
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def documents_view(request):
    if request.user.is_staff:
        # Adminui rodyk visus dokumentus arba specialų šabloną
        documents = Document.objects.all()
        context = {
            'documents': documents,
            'form': DocumentForm()
        }
        return render(request, 'admin_documents.html', context)
    else:
        resident = get_object_or_404(Resident, user=request.user)
        documents = Document.objects.filter(resident=resident)
        context = {
            'documents': documents,
            'form': DocumentForm()
        }
        return render(request, 'documents.html', context)

@user_passes_test(lambda u: u.is_staff)
def admin_documents(request):
    return render(request, 'admin_documents.html')

@user_passes_test(lambda u: u.is_staff)
def documents_by_residents(request):
    residents = Resident.objects.all().prefetch_related('documents')
    context = {
        'residents': residents
    }
    return render(request, 'documents_by_residents.html', context)

@user_passes_test(lambda u: u.is_staff)
def documents_by_apartments(request):
    apartments = (
        Resident.objects.values('apartment__number')
        .annotate(
            resident_count=Count('id'),
            document_count=Count('documents')
        )
        .order_by('apartment__number')
    )
    apartments = [
        {
            'number': apt['apartment__number'],
            'resident_count': apt['resident_count'],
            'document_count': apt['document_count']
        }
        for apt in apartments
    ]
    context = {
        'apartments': apartments
    }
    return render(request, 'documents_by_apartments.html', context)

@user_passes_test(lambda u: u.is_staff)
def apartment_residents(request, apartment_number):
    residents = Resident.objects.filter(
        apartment__number=apartment_number
    ).prefetch_related('documents')
    context = {
        'apartment_number': apartment_number,
        'residents': residents
    }
    return render(request, 'apartment_residents.html', context)

@user_passes_test(lambda u: u.is_staff)
def resident_documents(request, resident_id):
    resident = get_object_or_404(Resident, id=resident_id)
    documents = Document.objects.filter(resident=resident)
    
    context = {
        'resident': resident,
        'documents': documents,
        'form': DocumentForm()
    }
    return render(request, 'documents.html', context)

@login_required
def upload_document(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            resident = get_object_or_404(Resident, user=request.user)
            document.resident = resident
            document.save()
            messages.success(request, 'Dokumentas sėkmingai įkeltas')
            return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def delete_document(request, document_id):
    if request.method == 'POST':
        document = get_object_or_404(Document, id=document_id)
        if request.user.is_staff or document.resident.user == request.user:
            document.file.delete()  
            document.delete()
            messages.success(request, 'Dokumentas sėkmingai ištrintas')
            return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def delete_all_documents(request):
    if request.method == 'POST':
        if request.user.is_staff:
            documents = Document.objects.all()
        else:
            resident = get_object_or_404(Resident, user=request.user)
            documents = Document.objects.filter(resident=resident)
        
        for document in documents:
            document.file.delete()
        documents.delete()
        
        messages.success(request, 'Visi dokumentai sėkmingai ištrinti')
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def maintenance_list(request):
    today = timezone.now().date()
    past_works = Maintenance.objects.filter(status='past').prefetch_related('images')
    current_works = Maintenance.objects.filter(status='current').prefetch_related('images')
    future_works = Maintenance.objects.filter(status='future').prefetch_related('images')
    
    context = {
        'past_works': past_works,
        'current_works': current_works,
        'future_works': future_works,
        'form': MaintenanceForm() if request.user.is_staff else None
    }
    return render(request, 'maintenance_list.html', context)

@user_passes_test(lambda u: u.is_staff)
def create_maintenance(request):
    if request.method == 'POST':
        form = MaintenanceForm(request.POST)
        if form.is_valid():
            maintenance = form.save(commit=False)
            maintenance.created_by = request.user
            maintenance.save()
            
            images = request.FILES.getlist('images')
            for image in images:
                MaintenanceImage.objects.create(
                    maintenance=maintenance,
                    image=image
                )
            
            messages.success(request, 'Remontas/darbas sėkmingai sukurtas')
            return redirect('maintenance_list')
        else:
            messages.error(request, 'Klaida kuriant remontą/darbą')
    
    return redirect('maintenance_list')

@user_passes_test(lambda u: u.is_staff)
def delete_maintenance(request, maintenance_id):
    if request.method == 'POST':
        maintenance = get_object_or_404(Maintenance, id=maintenance_id)
        
        for image in maintenance.images.all():
            image.image.delete()
            image.delete()
            
        maintenance.delete()
        messages.success(request, 'Remontas/darbas sėkmingai ištrintas')
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)

@user_passes_test(lambda u: u.is_staff)
def complete_maintenance(request, maintenance_id):
    if request.method == 'POST':
        try:
            maintenance = get_object_or_404(Maintenance, id=maintenance_id)
            
            completion_date = timezone.localtime(timezone.now()).date()
            
            maintenance.status = 'past'
            maintenance.end_date = completion_date
            maintenance.save()
            
            images = request.FILES.getlist('images')
            for image in images:
                MaintenanceImage.objects.create(
                    maintenance=maintenance,
                    image=image
                )
            
            maintenance.refresh_from_db()
            if maintenance.status != 'past':
                maintenance.status = 'past'
                maintenance.save()
            
            messages.success(request, 'Darbas sėkmingai pažymėtas kaip atliktas')
            return JsonResponse({
                'status': 'success',
                'completion_date': completion_date.strftime('%Y-%m-%d')
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def vote(request, topic_id):
    if request.method == 'POST':
        vote_type = request.POST.get('vote_type')
        resident = request.user.resident
        topic = get_object_or_404(VotingTopic, pk=topic_id)
        
        if Vote.objects.filter(resident=resident, topic=topic).exists():
            messages.error(request, 'Jūs jau balsavote šiame balsavime!')
            return redirect('voting')
        
        Vote.objects.create(
            resident=resident,
            topic=topic,
            vote_type=vote_type
        )
        messages.success(request, 'Jūsų balsas sėkmingai įskaitytas!')
        return redirect('voting')
    
    return redirect('home')

@login_required
def get_vote_stats(request):
    total_votes = Vote.objects.count()
    votes_for = Vote.objects.filter(vote_type='for').count()
    votes_against = Vote.objects.filter(vote_type='against').count()
    
    return JsonResponse({
        'total_votes': total_votes,
        'votes_for': votes_for,
        'votes_against': votes_against,
    })

@login_required
def voting_view(request):
    active_topics = VotingTopic.objects.filter(
        status='active',
        end_date__gte=timezone.now().date()
    ).order_by('-created_at')
    
    completed_topics = VotingTopic.objects.filter(
        status='completed'
    ).order_by('-completed_at')
    
    topics_with_votes = []
    completed_topics_with_votes = []
    resident = request.user.resident

    for topic in active_topics:
        has_voted = Vote.objects.filter(resident=resident, topic=topic).exists()
        topics_with_votes.append({
            'topic': topic,
            'votes_for': Vote.objects.filter(topic=topic, vote_type='for').count(),
            'votes_against': Vote.objects.filter(topic=topic, vote_type='against').count(),
            'votes_count': topic.votes.count(),
            'has_voted': has_voted
        })

    for topic in completed_topics:
        completed_topics_with_votes.append({
            'topic': topic,
            'votes_for': Vote.objects.filter(topic=topic, vote_type='for').count(),
            'votes_against': Vote.objects.filter(topic=topic, vote_type='against').count(),
            'votes_count': topic.votes.count()
        })

    context = {
        'active_topics': topics_with_votes,
        'completed_topics': completed_topics_with_votes
    }
    return render(request, 'core/voting.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_voting_view(request):
    active_topics = VotingTopic.objects.filter(status='active').order_by('-created_at')
    completed_topics = VotingTopic.objects.filter(status='completed').order_by('-completed_at')
    
    def prepare_topics(topics):
        return [{
            'topic': topic,
            'votes_for': Vote.objects.filter(topic=topic, vote_type='for').count(),
            'votes_against': Vote.objects.filter(topic=topic, vote_type='against').count(),
            'votes_count': topic.votes.count()
        } for topic in topics]
    
    context = {
        'active_topics': prepare_topics(active_topics),
        'completed_topics': prepare_topics(completed_topics),
        'form': VotingTopicForm()
    }
    return render(request, 'core/admin_voting.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def create_voting(request):
    if request.method == 'POST':
        form = VotingTopicForm(request.POST)
        if form.is_valid():
            voting = form.save(commit=False)
            voting.created_by = request.user
            voting.save()
            messages.success(request, 'Balsavimas sėkmingai sukurtas!')
            return redirect('admin_voting')
    return redirect('admin_voting')

@login_required
@user_passes_test(lambda u: u.is_staff)
def get_voting(request, pk):
    voting = get_object_or_404(VotingTopic, pk=pk)
    data = {
        'title': voting.title,
        'description': voting.description,
        'end_date': voting.end_date.isoformat() if voting.end_date else None
    }
    return JsonResponse(data)

@login_required
@user_passes_test(lambda u: u.is_staff)
def edit_voting(request, pk):
    voting = get_object_or_404(VotingTopic, pk=pk)
    if request.method == 'POST':
        form = VotingTopicForm(request.POST, instance=voting)
        if form.is_valid():
            form.save()
            messages.success(request, 'Balsavimas sėkmingai atnaujintas!')
            return redirect('admin_voting')
    return redirect('admin_voting')

@login_required
@user_passes_test(lambda u: u.is_staff)
def delete_voting(request, pk):
    if request.method == 'POST':
        try:
            voting = get_object_or_404(VotingTopic, pk=pk)
            votes = Vote.objects.filter(topic=voting)
            votes.delete()
            voting.delete()
            messages.success(request, 'Balsavimas sėkmingai ištrintas')
            return JsonResponse({'status': 'success'})
        except VotingTopic.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Balsavimas nerastas'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Klaida trinant balsavimą: {str(e)}'
            }, status=500)
    return JsonResponse({
        'status': 'error',
        'message': 'Metodas neleidžiamas'
    }, status=405)

@login_required
@user_passes_test(lambda u: u.is_staff)
def toggle_voting(request, pk):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            is_active = data.get('is_active')
            
            if not isinstance(is_active, bool):
                return JsonResponse({
                    'status': 'error',
                    'message': f'Neteisingas aktyvumo būsenos formatas: {is_active}'
                }, status=400)
            
            updated = VotingTopic.objects.filter(pk=pk).update(is_active=is_active)
            
            if updated:
                voting = VotingTopic.objects.get(pk=pk)
                if voting.is_active == is_active:
                    messages.success(request, 'Balsavimo būsena sėkmingai atnaujinta')
                    return JsonResponse({
                        'status': 'success',
                        'is_active': voting.is_active
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Nepavyko atnaujinti būsenos'
                    }, status=500)
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Balsavimas nerastas'
                }, status=404)
                
        except json.JSONDecodeError as e:
            print(f"JSON klaida: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': 'Neteisingas užklausos formatas'
            }, status=400)
        except Exception as e:
            print(f"Nenumatyta klaida: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)
    return JsonResponse({'status': 'error', 'message': 'Metodas neleidžiamas'}, status=405)

@user_passes_test(lambda u: u.is_staff)
def get_resident(request, resident_id):
    resident = get_object_or_404(Resident, id=resident_id)
    data = {
        'first_name': resident.first_name,
        'last_name': resident.last_name,
        'email': resident.email,
        'apartment_number': resident.apartment.number if resident.apartment else '',
        'phone_number': resident.phone,
        'birth_date': resident.birth_date.isoformat() if resident.birth_date else None,
        'is_owner': resident.is_owner
    }
    return JsonResponse(data)

@login_required
@user_passes_test(lambda u: u.is_staff)
def complete_voting(request, pk):
    if request.method == 'POST':
        try:
            voting = get_object_or_404(VotingTopic, pk=pk)
            if voting.status == 'active':
                voting.status = 'completed'
                voting.completed_at = timezone.now()
                voting.save()
                messages.success(request, 'Balsavimas sėkmingai užbaigtas')
                return redirect('admin_voting')
            else:
                messages.error(request, 'Balsavimas jau yra užbaigtas')
                return redirect('admin_voting')
        except Exception as e:
            messages.error(request, f'Klaida bandant užbaigti balsavimą: {str(e)}')
            return redirect('admin_voting')
    return redirect('admin_voting')

@login_required
def complaints_view(request):
    """Skundų sąrašo peržiūra"""
    if request.user.is_staff:
        complaints = Complaint.objects.all()
    else:
        complaints = Complaint.objects.filter(apartment=request.user.resident.apartment)
    
    context = {
        'complaints': complaints,
        'form': ComplaintForm(),
        'can_create': request.user.resident.apartment.complaint_set.filter(
            created_at__gte=timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        ).count() < 2 if not request.user.is_staff else False
    }
    return render(request, 'core/complaints.html', context)

@login_required
def create_complaint(request):
    """Naujo skundo sukūrimas"""
    if request.user.is_staff:
        messages.error(request, "Administratoriai negali kurti skundų.")
        return redirect('complaints')
    
    if request.method == 'POST':
        form = ComplaintForm(request.POST, apartment=request.user.resident.apartment)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.apartment = request.user.resident.apartment
            complaint.save()
            messages.success(request, "Skundas sėkmingai sukurtas.")
            return redirect('complaints')
        else:
            messages.error(request, "Klaida kuriant skundą. Patikrinkite įvestus duomenis.")
    return redirect('complaints')

@login_required
def edit_complaint(request, complaint_id):
    """Skundo redagavimas"""
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    if request.user.is_staff:
        messages.error(request, "Administratoriai negali redaguoti skundų.")
        return redirect('complaints')
        
    if complaint.apartment != request.user.resident.apartment:
        messages.error(request, "Jūs negalite redaguoti šio skundo.")
        return redirect('complaints')
    
    if request.method == 'POST':
        form = ComplaintForm(request.POST, instance=complaint)
        if form.is_valid():
            form.save()
            messages.success(request, "Skundas sėkmingai atnaujintas.")
        else:
            messages.error(request, "Klaida atnaujinant skundą. Patikrinkite įvestus duomenis.")
    return redirect('complaints')

@login_required
def get_complaint(request, complaint_id):
    """Gauti skundo duomenis redagavimui"""
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    if request.user.is_staff or complaint.apartment != request.user.resident.apartment:
        return JsonResponse({'status': 'error', 'message': 'Neturite teisių'}, status=403)
    
    data = {
        'title': complaint.title,
        'description': complaint.description
    }
    return JsonResponse(data)

@login_required
def delete_complaint(request, complaint_id):
    """Skundo ištrynimas"""
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    if request.user.is_staff or complaint.apartment == request.user.resident.apartment:
        complaint.delete()
        messages.success(request, "Skundas sėkmingai ištrintas.")
    else:
        messages.error(request, "Jūs negalite ištrinti šio skundo.")
    
    return redirect('complaints')

@login_required
def calendar_view(request):
    """Kalendoriaus vaizdas"""
    if request.user.is_staff:
        birthdays = list(UserProfile.objects.exclude(birth_date=None).select_related('user'))
        birthdays.extend(list(Resident.objects.exclude(birth_date=None).select_related('user')))
    else:
        birthdays = list(Resident.objects.exclude(birth_date=None).select_related('user'))
    
    maintenance_works = Maintenance.objects.all()
    
    events = []
    
    for person in birthdays:
        if hasattr(person, 'user'):
            name = f"{person.user.first_name} {person.user.last_name}"
            date = person.birth_date
        else:
            name = f"{person.first_name} {person.last_name}"
            date = person.birth_date
        
        if date:
            events.append({
                'title': f"{name} gimtadienis",
                'start': date.strftime('%Y-%m-%d'),
                'className': 'birthday-event',
                'type': 'birthday',
                'allDay': True
            })
    
    for work in maintenance_works:
        if work.start_date:
            event = {
                'title': work.title,
                'start': work.start_date.strftime('%Y-%m-%d'),
                'type': 'maintenance',
                'className': f'maintenance-{work.status}',
                'allDay': True,
                'id': work.id
            }
            if work.end_date:
                event['end'] = (work.end_date + timedelta(days=1)).strftime('%Y-%m-%d')  # Pridedame vieną dieną, kad įtrauktų paskutinę dieną
            events.append(event)
    
    events_json = json.dumps(events, ensure_ascii=False)
    
    context = {
        'events': events_json,
        'events_count': len(events),
        'birthdays_count': len(birthdays),
        'maintenance_count': maintenance_works.count()
    }
    
    return render(request, 'core/calendar.html', context)

@login_required
def profile_view(request):
    """Profilio peržiūros ir redagavimo vaizdas"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profilis sėkmingai atnaujintas')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    
    context = {
        'form': form,
        'profile': profile
    }
    return render(request, 'core/profile.html', context)

def chat_view(request):
    chat_messages = ChatMessage.objects.select_related('user').order_by('created_at')
    return render(request, 'chat.html', {'chat_messages': chat_messages})

@require_POST
@login_required
def send_message(request):
    content = request.POST.get('content', '').strip()
    if content:
        msg = ChatMessage.objects.create(user=request.user, content=content)
        return JsonResponse({'status': 'success', 'id': msg.id, 'user': request.user.get_full_name() or request.user.username, 'content': msg.content, 'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M'), 'is_edited': msg.is_edited})
    return JsonResponse({'status': 'error', 'error': 'Tuščia žinutė'})

@require_POST
@login_required
def edit_message(request, msg_id):
    try:
        msg = ChatMessage.objects.get(id=msg_id, user=request.user)
        new_content = request.POST.get('content', '').strip()
        if new_content:
            msg.content = new_content
            msg.is_edited = True
            msg.updated_at = timezone.now()
            msg.save()
            return JsonResponse({'status': 'success', 'content': msg.content, 'updated_at': msg.updated_at.strftime('%Y-%m-%d %H:%M'), 'is_edited': msg.is_edited})
        return JsonResponse({'status': 'error', 'error': 'Tuščia žinutė'})
    except ChatMessage.DoesNotExist:
        return JsonResponse({'status': 'error', 'error': 'Žinutė nerasta arba neturite teisės redaguoti'})

@require_POST
@login_required
def delete_message(request, msg_id):
    try:
        msg = ChatMessage.objects.get(id=msg_id, user=request.user)
        msg.delete()
        return JsonResponse({'status': 'success'})
    except ChatMessage.DoesNotExist:
        return JsonResponse({'status': 'error', 'error': 'Žinutė nerasta arba neturite teisės trinti'})

def csrf_failure(request, reason=""):
    return render(request, "403_csrf.html", status=403)

class AuditLogAllActionsMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method == 'POST':
            from core.models import log_action
            user = request.user if hasattr(request, 'user') else None
            log_action(
                user,
                'action',
                view_func.__name__,
                object_id=None,
                changes=f'POST to {request.path}'
            )
        return None 