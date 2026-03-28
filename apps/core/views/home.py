from django.shortcuts import render

def home(request):
    """Renderiza la página de lectura principal"""
    return render(request, 'core/home.html')

def live_caption(request):
    """Renderiza la página de información de Live Caption"""
    return render(request, 'core/live_caption.html')
