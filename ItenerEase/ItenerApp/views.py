from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required

from .forms import *
from .models import *
from .static.scripts import functions

from decouple import config
from openai import OpenAI
import json
from datetime import datetime
import os


'''Helper Function to Determine the Season'''
def determine_season(vacation_start_date):
    month = vacation_start_date.month
    if month in [12, 1, 2]:
        return 'Winter'
    elif month in [3, 4, 5]:
        return 'Spring'
    elif month in [6, 7, 8]:
        return 'Summer'
    elif month in [9, 10, 11]:
        return 'Fall'
    return 'Unknown'


'''Global Variables'''

def trips(request):
    # Add your logic for the 'trips' page
    return render(request, 'ItenerApp/trips.html')

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

        # Check if the passwords match
        if request.POST.get("Password Field") == request.POST.get("Password Confirmation Field"):
            try:
                # Create a new user with username and email
                user = User.objects.create_user(
                    username=request.POST['Username Field'],  # Capture username
                    email=request.POST['Email Field'],  # Capture email
                    password=request.POST['Password Field']  # Capture password
                )
                user.save()
                
                # Log the user in
                login(request, user)
                return redirect('dashboard')
            except IntegrityError:
                return render(request, "ItenerApp/signupuser.html", {"error": "Username or Email already exists! Please log in."})
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
    return render(request, 'ItenerApp/dashboard.html', {'username': request.user.username})


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
            stay_name = data.get('optionName')
            stay_place = data.get('destination')
            # Add price details here for the stay
            
            # Save stay details to request session data
            request.session[f'stay_place_at_{stay_place}'] = stay_name

            print("Stay place received successfully. Sending 'success' json response")
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
    

'''Helper function for generating itinerary from scratch'''
def generate_itinerary(itinerary_context, user_message=None):
    # Define the base prompt template
    demo_template = """
        Create a detailed, personalized itinerary for a trip based on the following details:

        - Number of people: {num_people}
        - Start location: {start_location}
        - Destinations: {destinations}
        - Primary activity preference: {primary_activity_preference}
        - Vacation dates: {vacation_start_date} to {vacation_end_date}
        - Interested places: {interested_places}
        - Stay details: {stay_details}

        Weather Forecast Consideration:
        Based on the weather forecast retrieved from the OpenWeatherMap API for the specified dates, please adjust the activities to match the weather. For example:
        - Avoid outdoor activities such as boating or hiking if it's expected to rain.
        - Suggest indoor alternatives such as museums, cafes, or other cultural experiences if weather is unfavorable.

        Must-Visit Spots:
        Make sure to include must-visit places that are within a reasonable distance from the destination, even if they are outside the city. For example, if visiting Delhi, include a day trip to the Taj Mahal, as it's a must-see spot nearby.

        Based on previous user trips, here are some insights:
        {historical_data}

        Additionally, here are some user reviews and opinions on the places you're visiting:
        {forum_reviews}

        
        Generate the HTML code for the table representing this itinerary. Ensure the table is visually appealing and well-formatted. Use inline CSS to style the table. Include the following columns:
        - Date (in Day, Month format. Eg: 21st Sep)
        - Time
        - Activity
        - Location (place name, destination name)
        - Google Maps link
        - Weather Notes: [Weather condition for the day]
        - Adjustments or alternate plans for unfavorable weather (Always suggest atleast 1 adjustment like a change of plan nearby the previous location).

        Make sure to:
        1. Provide at least 4-5 activities per day.
        2. Include free time slots when appropriate.
        3. Order destinations logically if multiple are specified.
        4. Personalize activities based on user preferences and interests.
        5. Ensure the itinerary is clear and easy to understand.
        6. Suggest any notable attractions that are close to the main destinations but not part of the city itself.

        Do not style the table in any way. Return ONLY the unstyled HTML code for the table, enclosed within ``` symbols. 
    """

    # Load historical JSON files for the user
    user_id = itinerary_context.get('user_id')  # Assuming 'user_id' is part of the context
    user_data_path = os.path.join(settings.MEDIA_ROOT, f'user_data/user_{user_id}/')
    historical_data = ""

    # Check if the user's data directory exists
    if os.path.exists(user_data_path):
        # Loop through all the JSON files and extract relevant data
        for file_name in os.listdir(user_data_path):
            if file_name.endswith('.json'):
                file_path = os.path.join(user_data_path, file_name)
                with open(file_path, 'r') as f:
                    itinerary_data = json.load(f)
                    # Extract relevant info (trip duration, season, itinerary highlights)
                    trip_duration = itinerary_data['metadata'].get('trip_duration', 'Unknown')
                    season = itinerary_data['metadata'].get('season', 'Unknown')
                    destinations = ', '.join(itinerary_data['itinerary'].get('destinations', []))

                    # Append the historical data to be included in the prompt
                    historical_data += f"- Trip to {destinations} ({trip_duration} days, {season} season)\n"

                    # Check if there are any interested places from the previous trip
                    interested_places = itinerary_data.get('interested_places', {}).get('interestedPlaces', [])
                    if interested_places:
                        historical_data += f"  - Interested places: {', '.join(interested_places)}\n"
                    else:
                        historical_data += "  - Interested places: No specific preferences\n"
    else:
        historical_data = "No previous trip data available."

    # Load forum reviews
    forum_reviews_path = os.path.join(settings.MEDIA_ROOT, 'forum/reviews.json')
    forum_reviews = ""

    if os.path.exists(forum_reviews_path):
        with open(forum_reviews_path, 'r') as f:
            reviews_data = json.load(f)
            # Extract and format the reviews
            for place_entry in reviews_data.get('places', []):
                place = place_entry.get('place', 'Unknown place')
                for review in place_entry.get('reviews', []):
                    user = review.get('user', 'Anonymous')
                    rating = review.get('rating', 'No rating provided')
                    comment = review.get('comment', 'No comment provided')
                    forum_reviews += f"- {place}: Reviewed by {user} - Rating: {rating} - Comment: {comment}\n"
    else:
        forum_reviews = "No forum reviews available."

    # Format the prompt with the itinerary context and historical data
    try:
        formatted_prompt = demo_template.format(
            num_people=itinerary_context['num_people'],
            start_location=itinerary_context['start_location'],
            destinations=', '.join(itinerary_context['destinations']),
            primary_activity_preference=itinerary_context['primary_activity_preference'],
            vacation_start_date=itinerary_context['vacation_start_date'],
            vacation_end_date=itinerary_context['vacation_end_date'],
            interested_places=', '.join(itinerary_context['interested_places']['interestedPlaces']),
            stay_details=', '.join([f"{key.split('_')[-1]}: {value}" for key, value in itinerary_context.items() if key.startswith('stay_place_at')]),
            historical_data=historical_data,
            forum_reviews=forum_reviews
        )
    except KeyError as e:
        # Handle any missing keys or fallbacks
        formatted_prompt = demo_template.format(
            num_people=itinerary_context.get('num_people', 'Unknown'),
            start_location=itinerary_context.get('start_location', 'Unknown'),
            destinations=', '.join(itinerary_context.get('destinations', [])),
            primary_activity_preference=itinerary_context.get('primary_activity_preference', 'Unknown'),
            vacation_start_date=itinerary_context.get('vacation_start_date', 'Unknown'),
            vacation_end_date=itinerary_context.get('vacation_end_date', 'Unknown'),
            interested_places='Open to explore and visit any place, there are no preferences',
            stay_details=', '.join([f"{key.split('_')[-1]}: {value}" for key, value in itinerary_context.items() if key.startswith('stay_place_at')]),
            historical_data=historical_data,
            forum_reviews=forum_reviews
        )

    print("Formatted prompt: \n", formatted_prompt)

    # Send the formatted prompt to OpenAI API
    client = OpenAI(api_key=config('OPENAI_API_KEY'))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": formatted_prompt}],
        max_tokens=7000,
        temperature=0.8
    )

    # Extract and return the AI's response
    return response.choices[0].message.content.replace('```', '').replace('html', '')


'''Helper function for generating itinerary from user updates'''
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
    1. Provide at least 4-5 activities per day.
    2. Include free time slots when appropriate.
    3. Order destinations logically if multiple are specified.
    4. Personalize activities based on user preferences and interests.
    5. Ensure the itinerary is clear and easy to understand.

    Do not style the table in any way. Return ONLY the unstyled HTML code for the table, enclosed within ``` symbols."""

    # Format the prompt based on the context and user request (if any)
    try:
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
    except:
        formatted_prompt = demo_template.format(
            existing_itinerary=existing_itinerary,
            additional_request=user_message,
            num_people=itinerary_context['num_people'],
            start_location=itinerary_context['start_location'],
            destinations=', '.join(itinerary_context['destinations']),
            primary_activity_preference=itinerary_context['primary_activity_preference'],
            vacation_start_date=itinerary_context['vacation_start_date'],
            vacation_end_date=itinerary_context['vacation_end_date'],
            interested_places='Open to explore and visit any place, there are no preferences',
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



'''View for rendering itinerary and updating it otg using a chat mechanism'''
def finalize_itinerary(request):
    itinerary_context = {
        'user_id': request.user.id,
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

    if request.method == 'POST':
        if "send" in request.POST:
            # Handle POST request
            user_message = json.loads(request.body)['user_message']
            print(user_message)
            
            # Modify the existing itinerary based on user input
            print("Updating itinerary...")
            modified_itinerary = generate_itinerary_updated(request.session['itinerary'], itinerary_context, user_message)
            request.session['itinerary'] = modified_itinerary
            print(modified_itinerary)
            
            # Return a JSON response for the frontend to handle
            return JsonResponse({
                'success': True,
                'itinerary_html': modified_itinerary  # This should be HTML that you inject via JS
            })
        elif "finalize" in request.POST:
            print("Finalize in request.POST")

            # Parse the vacation_start_date and vacation_end_date strings to datetime objects
            start_date_str = itinerary_context['vacation_start_date']
            end_date_str = itinerary_context['vacation_end_date']

            # Convert date strings to datetime objects
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d') if start_date_str else None
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') if end_date_str else None

            # Calculate the trip duration
            trip_duration = (end_date - start_date).days if start_date and end_date else 'Unknown'

            # Inferred season from start date
            season = determine_season(start_date) if start_date else 'Unknown'

            itinerary_metadata = {
                'trip_duration': trip_duration,
                'season': season,
                'created_at': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            }

            user_itinerary_data = {
                'itinerary': itinerary_context,
                'metadata': itinerary_metadata,
            }
            print("User JSON Collected Data: \n", user_itinerary_data)

            # Save data in the user's directory
            user_id = request.user.id
            directory_path = os.path.join(settings.MEDIA_ROOT, f'user_data/user_{user_id}/')

            if not os.path.exists(directory_path):
                os.makedirs(directory_path)

            file_name = f'itinerary_{timezone.now().strftime("%Y%m%d_%H%M%S")}.json'
            file_path = os.path.join(directory_path, file_name)
            
            with open(file_path, 'w') as f:
                json.dump(user_itinerary_data, f)

            print(f'status: Itinerary saved successfully at path: {file_path}')
            return redirect('completed_itinerary')
    
    print("Crafting initial itinerary...")
    generated_itinerary = generate_itinerary(itinerary_context)
    print(generated_itinerary)
    request.session['itinerary'] = generated_itinerary
    
    return render(request, 'ItenerApp/finalize_itinerary.html', {
        'initial_message': "How is this itinerary?",
        'itinerary': generated_itinerary,
        'itinerary_context': itinerary_context,
    })


'''View to render final display of the itinerary'''
@login_required
def completed_itinerary(request):
    if request.method == 'POST':
        if 'go_to_dashboard' in request.POST:
            return redirect('dashboard')
        else:
            print("Unknown name in request.POST")

    return render(request, 'ItenerApp/completed_itinerary.html')
