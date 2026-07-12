from django.shortcuts import render

def landing(request):
    """
    Public Landing Page
    """
    return render(request, "landing.html")