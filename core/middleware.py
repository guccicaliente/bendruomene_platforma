from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib.admin.sites import site
from django.contrib.auth.forms import AuthenticationForm

class OnlySisadminAdminMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/') and request.user.is_authenticated:
            if request.user.username != 'sisadmin':
                from django.contrib.auth import logout
                logout(request)
                return redirect(f'/admin/login/?error=sisadmin&next={request.path}')

        if request.path.startswith('/admin/login') and request.method == 'POST':
            username = request.POST.get('username')
            if username and username != 'sisadmin':
                context = {
                    'request': request,
                    'error': 'sisadmin',
                    'form': AuthenticationForm(request, data=request.POST),
                    'title': 'Prisijungimas',
                    'site_title': site.site_title,
                    'site_header': site.site_header,
                    'next': request.GET.get('next', '/admin/'),
                }
                return render(request, 'admin/login.html', context)
        return self.get_response(request) 