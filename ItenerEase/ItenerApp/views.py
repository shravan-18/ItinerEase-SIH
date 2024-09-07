from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.conf import settings
from django.http import StreamingHttpResponse, JsonResponse, HttpResponse, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required

from .forms import *
from .models import *
from .static.scripts import functions

import os
import cv2
import json
import base64


'''Global Variables'''
camera_instance = None


'''Function to fully delete all session variables from latest session'''
def clear_session_variables(request):
    # List of session keys you want to clear
    session_keys = []
    
    for key in session_keys:
        try:
            if key in request.session:
                del request.session[key]
        except Exception as e:
            # Optionally log the exception if needed
            print(f"An error occurred while deleting session key '{key}': {e}")


'''View to render landing page'''
def home(request):
    return render(request, "ItenerApp/index.html")


'''View to signup user'''
def signupuser(request):
    if request.method == 'GET':
        return render(request, "ItenerApp/signupuser.html")
    
    else:
        print(request.POST)
        # Validate Email...
        if functions.check_email(request.POST.get("Email Field")) == False:
            return render(request, "ItenerApp/signupuser.html", {"error": "Invalid Email Address!"})

        # Create a new user...
        if request.POST.get("Password Field") == request.POST.get("Password Confirmation Field"):
            try:
                user = User.objects.create_user(request.POST['Email Field'], password=request.POST['Password Field'])
                user.save()
                login(request, user)
                return redirect('dashboard')
            except IntegrityError:
                return render(request, "ItenerApp/signupuser.html", {"error": "Email already exists! Please Log in."})

        else:
            return render(request, "ItenerApp/signupuser.html", {"error": "Passwords did not match!"})
        

'''View to login user'''
def loginuser(request):
    if request.method == 'GET':
        return render(request, "ItenerApp/loginuser.html")
    
    else:
        # Validate Email...
        email = request.POST.get("Email")
        if not functions.check_email(email):
            return render(request, "ItenerApp/loginuser.html", {"error": "Invalid Email Address!"})
        
        # Check if the user exists
        try:
            user = User.objects.get(username=email)
        except User.DoesNotExist:
            return render(request, "ItenerApp/loginuser.html", {"error": "No user exists with this email address!"})
        
        # Authenticate the user
        user = authenticate(request, username=email, password=request.POST.get("Password"))
        if user is None:
            return render(request, "ItenerApp/loginuser.html", {"error": "Email and Password did not match!"})
        else:
            login(request, user)
            return redirect('dashboard')


'''View to logout user'''
@login_required
def logoutuser(request):
    if request.method == 'POST':
        logout(request)
        return redirect('home')


'''View to render dashboard'''
@login_required
def dashboard(request):
    return render(request, 'ItenerApp/dashboard.html')


'''View for the first starting page of creating a new itenary user'''
@login_required
def start(request):
    return render(request, 'ItenerApp/start.html')


'''View for the '''
@csrf_exempt
def submit_itinerary(request):
    if request.method == 'POST':
        num_people = request.POST.get('num_people')
        start_location = request.POST.get('start_location')
        destinations = request.POST.get('destinations')  # This is a JSON string
        vacation_type = request.POST.get('vacation_type')

        # Convert destinations back to a Python list
        import json
        destinations = json.loads(destinations)

        # Process the data as needed...

        return JsonResponse({
            'success': True,
            'num_people': num_people,
            'start_location': start_location,
            'destinations': destinations,
            'vacation_type': vacation_type
        })
    
def submit_dates(request):
    if request.method == 'POST':
        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')
        print(f"From: {from_date} to: {to_date}")

        # Process the dates as needed...

        return JsonResponse({'success': True})
    
def submit_interested_places(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        print(data)
        # Handle data here
        return JsonResponse({'success': True})
    return JsonResponse({'success': False}, status=404)


def choose_stay(request):
    if request.method == 'POST':
        # Get the data from the request
        try:
            data = json.loads(request.body.decode('utf-8'))
            stay_name = data.get('name')
            print(stay_name)
            
            # Process the data (e.g., save it to the database)
            # Here you would handle the chosen stay item as needed

            response = {
                'success': True,
                'message': f'Stay item {stay_name} selected successfully!'
            }
        except json.JSONDecodeError:
            response = {
                'success': False,
                'message': 'Invalid data format.'
            }
        
        return JsonResponse(response)
    else:
        return JsonResponse({'success': False, 'message': 'Invalid request method.'})
    