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

from decouple import config
from openai import OpenAI
import json


'''Global Variables'''


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
    clear_session_variables(request)
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


'''View for submitting first details set in the 'start' page'''
@csrf_exempt
def submit_itinerary(request):
    if request.method == 'POST':
        num_people = request.POST.get('num_people')
        start_location = request.POST.get('start_location')
        destinations = request.POST.get('destinations')  # This is a JSON string
        vacation_type = request.POST.get('vacation_type')

        # Convert destinations back to a Python list
        destinations = json.loads(destinations)

        # Save all data to request session data
        request.session['num_people'] = num_people
        request.session['start_location'] = start_location
        request.session['destinations'] = destinations
        request.session['primary_activity_preference'] = vacation_type

        return JsonResponse({
            'success': True,
            'num_people': num_people,
            'start_location': start_location,
            'destinations': destinations,
            'vacation_type': vacation_type
        })


'''View for submitting dates for vacation in the 'start' page'''
def submit_dates(request):
    if request.method == 'POST':
        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')
        print(f"From: {from_date} to: {to_date}")

        # Save dates to request session data
        request.session['vacation_start_date'] = from_date
        request.session['vacation_end_date'] = to_date

        return JsonResponse({'success': True})
    

'''View for submitting interested places in the 'start' page'''
def submit_interested_places(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        print("Interested places: \n", data)
        print()

        # Save interested places to request session data
        request.session['interested_places'] = data

        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False}, status=404)


'''View for choosing stay details in the 'start' page'''
def choose_stay(request):
    if request.method == 'POST':
        # Get the data from the request
        try:
            data = json.loads(request.body.decode('utf-8'))
            stay_name = data.get('name')
            stay_place = data.get('place')
            
            # Save stay details to request session data
            request.session[f'stay_place_at_{stay_place}'] = stay_name

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
    








# Helper function to interact with the OpenAI API
def generate_itinerary(itinerary_context, user_message=None):
    # Define the prompt template
    demo_template = """
    Create a detailed, personalized itinerary for a trip based on the following details:

    - Number of people: {num_people}
    - Start location: {start_location}
    - Destinations: {destinations}
    - Primary activity preference: {primary_activity_preference}
    - Vacation dates: {vacation_start_date} to {vacation_end_date}
    - Interested places: {interested_places}
    - Stay details: {stay_details}

    Generate the HTML code for the table representing this itinerary. Ensure the table is visually appealing and well-formatted. Use inline CSS to style the table. Include the following columns:
    - Date
    - Time
    - Activity
    - Location (place name, destination name)
    - Google Maps link

    Make sure to:
    1. Provide at least 5-6 activities per day.
    2. Include free time slots when appropriate.
    3. Order destinations logically if multiple are specified.
    4. Personalize activities based on user preferences and interests.
    5. Ensure the itinerary is clear and easy to understand.

    Return ONLY the HTML code for the table, enclosed within ``` symbols."""

    # Format the prompt based on the context and user request (if any)
    formatted_prompt = demo_template.format(
        num_people=itinerary_context['num_people'],
        start_location=itinerary_context['start_location'],
        destinations=', '.join(itinerary_context['destinations']),
        primary_activity_preference=itinerary_context['primary_activity_preference'],
        vacation_start_date=itinerary_context['vacation_start_date'],
        vacation_end_date=itinerary_context['vacation_end_date'],
        interested_places=', '.join(itinerary_context['interested_places']['interestedPlaces']),
        stay_details=', '.join([f"{key.split('_')[-1]}: {value}" for key, value in itinerary_context.items() if key.startswith('stay_place_at')])
    )

    client = OpenAI(api_key=config('OPENAI_API_KEY'))

    # Make the API request
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": formatted_prompt}],
        max_tokens=7000,
        temperature=0.8
    )

    # Extract and return the AI's response
    return response.choices[0].message.content.replace('```', '').replace('html', '')


# Helper function to interact with the OpenAI API
def generate_itinerary_updated(existing_itinerary, itinerary_context, user_message=None):
    # Define the prompt template
    demo_template = """
    Existing itinerary: {existing_itinerary}

    User request: {additional_request}

    Update the itinerary based on the user's request. If the user wants modifications to the existing itinerary, make those changes. If the user requests a fresh itinerary, create one from scratch using the following instructions:

    Create a detailed, personalized itinerary for a trip based on the following details:

    - Number of people: {num_people}
    - Start location: {start_location}
    - Destinations: {destinations}
    - Primary activity preference: {primary_activity_preference}
    - Vacation dates: {vacation_start_date} to {vacation_end_date}
    - Interested places: {interested_places}
    - Stay details: {stay_details}

    Generate the HTML code for the table representing this itinerary. Ensure the table is visually appealing and well-formatted. Use inline CSS to style the table. Include the following columns:
    - Date
    - Time
    - Activity
    - Location (place name, destination name)
    - Google Maps link

    Make sure to:
    1. Provide at least 5-6 activities per day.
    2. Include free time slots when appropriate.
    3. Order destinations logically if multiple are specified.
    4. Personalize activities based on user preferences and interests.
    5. Ensure the itinerary is clear and easy to understand.

    Return ONLY the HTML code for the table, enclosed within ``` symbols."""

    # Format the prompt based on the context and user request (if any)
    formatted_prompt = demo_template.format(
        existing_itinerary=existing_itinerary,
        additional_request=user_message,
        num_people=itinerary_context['num_people'],
        start_location=itinerary_context['start_location'],
        destinations=', '.join(itinerary_context['destinations']),
        primary_activity_preference=itinerary_context['primary_activity_preference'],
        vacation_start_date=itinerary_context['vacation_start_date'],
        vacation_end_date=itinerary_context['vacation_end_date'],
        interested_places=', '.join(itinerary_context['interested_places']['interestedPlaces']),
        stay_details=', '.join([f"{key.split('_')[-1]}: {value}" for key, value in itinerary_context.items() if key.startswith('stay_place_at')])
    )


    print(formatted_prompt)

    client = OpenAI(api_key=config('OPENAI_API_KEY'))

    # Make the API request
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": formatted_prompt}],
        max_tokens=7000,
        temperature=0.8
    )

    # Extract and return the AI's response
    return response.choices[0].message.content.replace('```', '').replace('html', '')

# View for rendering the itinerary showing page
def finalize_itinerary(request):
    itinerary_context = {
        'num_people': request.session.get('num_people'),
        'start_location': request.session.get('start_location'),
        'destinations': request.session.get('destinations'),
        'primary_activity_preference': request.session.get('primary_activity_preference'),
        'vacation_start_date': request.session.get('vacation_start_date'),
        'vacation_end_date': request.session.get('vacation_end_date'),
        'interested_places': request.session.get('interested_places'),
    }

    # Include stay places in the itinerary context
    for key, value in request.session.items():
        if key.startswith('stay_place_at') and not any(x in key.lower() for x in ['hotel', 'airbnb', 'villa']):
            itinerary_context[key] = value

    if request.method == 'GET':
        generated_itinerary = generate_itinerary(itinerary_context)
        print(generated_itinerary)
        request.session['itinerary'] = generated_itinerary
        
        return render(request, 'ItenerApp/finalize_itinerary.html', {
            'initial_message': "How is this itinerary?",
            'itinerary': generated_itinerary,
            'itinerary_context': itinerary_context,
        })

    # Handle POST request
    user_message = json.loads(request.body)['user_message']
    print(user_message)
    
    # Modify the existing itinerary based on user input
    modified_itinerary = generate_itinerary_updated(request.session['itinerary'], itinerary_context, user_message)
    request.session['itinerary'] = modified_itinerary
    print(modified_itinerary)
    
    # Return a JSON response for the frontend to handle
    return JsonResponse({
        'success': True,
        'itinerary_html': modified_itinerary  # This should be HTML that you inject via JS
    })
