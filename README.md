# **AI-Powered Itinerary Planner**

This project - **AI-powered itinerary planner** - is our submission for the Smart India Hackathon '24, designed to create personalized travel plans for users. It dynamically collects user inputs through a chatbot interface, processes the data to generate a tailored itinerary, and allows for real-time modifications based on user preferences, travel conditions, and past behavior. The backend uses Django, while the front-end consists of vanilla HTML, CSS, and JavaScript.

## **Table of Contents**
1. [Project Overview](#project-overview)
2. [Features](#features)
3. [User Interaction Flow](#user-interaction-flow)
4. [Technical Stack](#technical-stack)
5. [Installation](#installation)
6. [Usage](#usage)
7. [Data Structure](#data-structure)
8. [Saving User Data for Continual Learning](#saving-user-data-for-continual-learning)
9. [Contributors](#contributors)

---

## **Project Overview**

This project enables users to create personalized travel itineraries. The system collects user information (e.g., number of travelers, destinations, vacation dates, activity preferences), and uses an AI-driven engine to suggest the best itinerary. Users can modify their itinerary based on their preferences in a chatbot-style interface. The system continually learns from the user’s travel patterns and provides better suggestions for future trips.

---

## **Features**

- **Dynamic Chatbot Interaction**: Collects user details such as number of travelers, destinations, travel dates, and preferences.
- **Real-time Itinerary Generation**: Uses AI to create custom itineraries based on user input, weather data, and nearby must-visit spots.
- **Continual Learning**: Saves and analyzes user data over time to offer personalized recommendations in future trips.
- **User Behavior Analysis**: Learns travel patterns like preferred activities, budgets, and destinations.
- **Django Backend**: Handles user data and itinerary generation requests.
- **Frontend with Vanilla JavaScript**: Offers a seamless user experience with chatbot-style interactions.

---

## **User Interaction Flow**

1. **Welcome Message**: The chatbot welcomes the user and asks how many people are traveling and for basic trip details (e.g., destinations, vacation type).
2. **Form Submission**: The user submits travel details (dates, location, preferences) through dynamic forms.
3. **Itinerary Display**: The AI generates an itinerary in an easy-to-read table format and allows the user to modify it.
4. **Continual Feedback Loop**: Users can modify the itinerary by interacting with the chatbot, and their feedback is incorporated.
5. **Finalization**: The user confirms the finalized itinerary, and the system saves the user’s preferences for future trips.

---

## **Technical Stack**

- **Backend**: Django (Python)
- **Frontend**: HTML, CSS, JavaScript
- **AI/ML**: OpenAI GPT-4 API for itinerary generation
- **Database**: Django ORM for managing user data
- **Media Storage**: Django media directory for storing user behavior data

---

## **Installation**

1. Clone the repository:
   ```bash
   git clone https://github.com/shravan-18/itinerary-planner.git
   cd itinerary-planner
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up Django migrations:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. Run the Django server:
   ```bash
   python manage.py runserver
   ```

## **Usage**

1. **Access the Web App**: Open your browser and go to `http://localhost:8000/`.
2. **Interact with the Chatbot**: Provide trip details, such as the number of travelers, destination, and dates.
3. **Get Your Itinerary**: The system generates an itinerary based on your inputs.
4. **Modify Itinerary**: Use the chatbot interface to customize the itinerary further.
5. **Finalize Itinerary**: Confirm your trip plan, which is saved for future analysis.

## **Saving User Data for Continual Learning**

The user data is saved constantly after each itinerary to track behavioral patterns and improve future suggestions. The data is stored in a structured format using Django’s media directory, enabling continual learning through RAG (Retrieval-Augmented Generation).

## **Contributors**

- [Shravan Venkatraman](https://github.com/shravan-18) ![GitHub Icon](https://img.shields.io/badge/-GitHub-181717?style=flat-square&logo=github&logoColor=white)
- [Pavan Kumar S](https://github.com/pavan-0725) ![GitHub Icon](https://img.shields.io/badge/-GitHub-181717?style=flat-square&logo=github&logoColor=white)
- [Santhosh Malarvannan](https://github.com/Sandy055) ![GitHub Icon](https://img.shields.io/badge/-GitHub-181717?style=flat-square&logo=github&logoColor=white)
- [Meghana Sunil](https://github.com/meghanaasunil) ![GitHub Icon](https://img.shields.io/badge/-GitHub-181717?style=flat-square&logo=github&logoColor=white)
- [Jayasankar K S](https://github.com/ksjayasankar) ![GitHub Icon](https://img.shields.io/badge/-GitHub-181717?style=flat-square&logo=github&logoColor=white)
- [Gowri Ajith](https://github.com/June465) ![GitHub Icon](https://img.shields.io/badge/-GitHub-181717?style=flat-square&logo=github&logoColor=white)

We welcome contributions! Feel free to submit issues or pull requests.
