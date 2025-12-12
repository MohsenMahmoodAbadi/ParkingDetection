from django.shortcuts import render
import socket

def home(request):
    """صفحه اصلی"""
    return render(request, 'home.html')

def mobile_stream(request):
    """صفحه استریم برای موبایل"""
   
    try:
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
    except:
        ip_address = 'localhost'
    
    context = {
        'ip_address': ip_address,
        'ws_url': f'ws://{request.get_host()}/ws/video/stream/'
    }
    return render(request, 'mobile_stream.html', context)

def test_page(request):
    """صفحه تست ساده"""
    return render(request, 'test.html')