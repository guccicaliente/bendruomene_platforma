from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            return render(request, 'admin_login.html', {'error': 'Neteisingi prisijungimo duomenys'})
    return render(request, 'admin_login.html') 