from django.shortcuts import render

def home(request):
    """Renderiza la página de lectura principal"""
    return render(request, 'core/home.html')
