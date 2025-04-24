import datetime
import os
import pickle
import re
import sqlite3
import threading
import time

import google.generativeai as genai
import pyttsx3
import pytz
import requests
import speech_recognition as sr
from dateutil import parser
from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# .env
GEMINI_API_KEY="AIzaSyDDDiZjqA9Eti944   Gil9ZyWrY7y9jml94U"
ACCESS_TOKEN="CYu7LZR6J5vGG8c_UDLTUWS28Rgu32oS"
CALENDAR_ID="cal_Z@E6OJt82XJxIhhT_60sGxx09KtjKoqkl2pes5A"

# === Init Speech Recognition and TTS Engines ===
recognizer = sr.Recognizer()
engine = pyttsx3.init()
wake_word = "sahara"

# === Timezone Setup ===
LOCAL_TZ = pytz.timezone("Asia/Kolkata")  # Change this if your timezone is different

# === Reminders Storage ===
reminders = []

# === Google Calendar API Configuration ===
SCOPES = ['https://www.googleapis.com/auth/calendar']

# === Initialize Gemini API ===
genai.configure(api_key=GEMINI_API_KEY)


# === Speech Functions ===
def speak(text):
    """Text-to-speech output function"""
    print(f"Sahara: {text}")
    engine.say(text)
    engine.runAndWait()


def listen():
    """Speech recognition function"""
    with sr.Microphone() as source:
        print("Listening...")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            print("Audio received.")
            command = recognizer.recognize_google(audio)
            print(f"User said: {command}")
            return command.lower()
        except (sr.UnknownValueError, sr.WaitTimeoutError):
            print("Could not understand audio.")
            return ""
        except sr.RequestError:
            speak("Sorry, I couldn't connect to the recognition service.")
            return ""


def detect_wake_word(wake_word="sahara"):
    """Specific function to detect wake word"""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for wake word...")
        audio = r.listen(source, phrase_time_limit=3)
    try:
        text = r.recognize_google(audio)
        print("Heard:", text)
        return wake_word.lower() in text.lower()
    except:
        return False


# === Time Utilities ===
def parse_time_string(time_str):
    """Parse spoken time into datetime objects"""
    try:
        print(f"Spoken time: {time_str}")
        parts = time_str.lower().replace(".", "").replace(" ", "")
        if "am" in parts or "pm" in parts:
            meridian = "am" if "am" in parts else "pm"
            digits = ''.join(filter(str.isdigit, parts))
            if len(digits) == 3:
                time_str = f"{digits[0]}:{digits[1:]} {meridian}"
            elif len(digits) == 4:
                time_str = f"{digits[:2]}:{digits[2:]} {meridian}"
        parsed_time = parser.parse(time_str)
        print(f"Parsed time: {parsed_time.strftime('%I:%M %p')}")
        return parsed_time
    except Exception as e:
        print(f"Time parsing failed: {e}")
        return None


def extract_seconds(text):
    """Extract time duration from text"""
    pattern = r"(\d+)\s*(seconds?|minutes?|hours?)"
    match = re.search(pattern, text.lower())
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        if "second" in unit:
            return amount
        elif "minute" in unit:
            return amount * 60
        elif "hour" in unit:
            return amount * 3600
    return None


# === Event Database Functions ===
def initialize_db():
    """Initialize the SQLite database for events"""
    conn = sqlite3.connect("sahara_events.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    conn.commit()
    conn.close()


def store_event_locally(title, start_time, end_time):
    """Store an event in the local SQLite database"""
    conn = sqlite3.connect("sahara_events.db")
    c = conn.cursor()
    c.execute("INSERT INTO events (title, start_time, end_time) VALUES (?, ?, ?)", (title, start_time, end_time))
    conn.commit()
    conn.close()


def list_local_events():
    """List all events from the local database"""
    conn = sqlite3.connect("sahara_events.db")
    c = conn.cursor()
    c.execute("SELECT * FROM events ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return rows


# === Google Calendar Functions ===
def authenticate_google_account():
    """Authenticate with Google Calendar API"""
    creds = None
    # Check if token.pickle file exists
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there's no valid token, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save credentials for future use
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds


def test_google_calendar_api():
    """Test connection to Google Calendar API"""
    try:
        creds = authenticate_google_account()
        service = build('calendar', 'v3', credentials=creds)
        calendar = service.calendarList().list().execute()  # Get list of calendars
        print("Successfully authenticated with Google Calendar")
        print("Your calendars:", calendar)
        return True, calendar
    except Exception as e:
        print(f"Error connecting to Google Calendar: {e}")
        return False, str(e)


# === Cronofy Calendar Functions ===
def create_cronofy_event(title, time_obj):
    """Create an event in Cronofy calendar"""
    now = datetime.datetime.now(LOCAL_TZ)
    event_datetime = datetime.datetime.combine(now.date(), time_obj.time())
    event_datetime = LOCAL_TZ.localize(event_datetime)

    if event_datetime < now:
        event_datetime += datetime.timedelta(days=1)

    event_datetime_utc = event_datetime.astimezone(pytz.utc)

    start_time_iso = event_datetime_utc.isoformat()
    end_time_iso = (event_datetime_utc + datetime.timedelta(minutes=30)).isoformat()

    event_data = {
        "event_id": f"sahara-event-{int(datetime.datetime.now().timestamp())}",
        "summary": title,
        "start": start_time_iso,
        "end": end_time_iso
    }

    url = f"https://api.cronofy.com/v1/calendars/{CALENDAR_ID}/events"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=event_data, headers=headers)
    if response.status_code == 202:
        speak("Your event has been successfully created.")
        store_event_locally(title, start_time_iso, end_time_iso)
        return True
    else:
        speak("Sorry, there was an error creating the event. Please try again.")
        print(f"Error response: {response.text}")
        return False


def list_upcoming_events():
    """List upcoming events from local database"""
    now_utc = datetime.datetime.now(pytz.utc)
    conn = sqlite3.connect("sahara_events.db")
    c = conn.cursor()
    c.execute("""
        SELECT title, start_time FROM events
        ORDER BY start_time ASC
    """)
    events = c.fetchall()
    conn.close()

    upcoming_events = []
    for title, start_time in events:
        event_time = parser.parse(start_time).astimezone(LOCAL_TZ)
        if event_time > datetime.datetime.now(LOCAL_TZ):
            upcoming_events.append((title, event_time))

    if upcoming_events:
        speak(f"You have {len(upcoming_events)} upcoming event{'s' if len(upcoming_events) > 1 else ''}.")
        for title, event_time in upcoming_events:
            speak(f"{title} at {event_time.strftime('%I:%M %p')}")
    else:
        speak("You have no upcoming events.")


# === Timer Functions ===
def set_timer(duration_seconds):
    """Set a timer for specified duration"""
    def alert():
        speak("⏰ Time's up! This is your reminder.")

    threading.Timer(duration_seconds, alert).start()


# === Reminder Functions ===
def handle_reminders(query):
    """Process reminder requests"""
    global reminders
    if "at" in query:
        parts = query.split("at")
        medicine = parts[0].replace("remind me to take", "").strip()
        time_str = parts[1].strip()

        reminders.append({"medicine": medicine, "time": time_str, "taken": False})
        speak(f"Okay, I will remind you to take {medicine} at {time_str}")
    else:
        speak("Please specify a time to remind.")


def check_reminders():
    """Check and notify about due reminders"""
    global reminders
    current_time = time.strftime("%H:%M")
    for reminder in reminders:
        if reminder["time"] == current_time and not reminder["taken"]:
            speak(f"It's time to take your {reminder['medicine']}. Have you taken it?")
            response = listen()
            if response and "yes" in response:
                speak("Great! I've marked it as taken.")
                reminder["taken"] = True
            else:
                speak("Okay, I will remind you again soon.")


def check_medication_reminders(command):
    """Check and manage medication reminders"""
    global reminders
    if "set" in command.lower():
        try:
            parts = command.lower().split(" at ")
            medicine = parts[0].replace("set reminder for", "").strip()
            time_str = parts[1].strip()
            reminder_time = datetime.datetime.strptime(time_str, "%I %p").time()
            reminders.append((medicine, reminder_time))
            return f"Reminder set for {medicine} at {time_str}."
        except:
            return "Sorry, I couldn't understand the time."
    
    elif "done" in command.lower() or "taken" in command.lower():
        medicine = command.lower().replace("i have taken", "").strip()
        reminders = [r for r in reminders if r[0] != medicine]
        return f"Okay, marked {medicine} as taken."

    now = datetime.datetime.now().time()
    due = [r for r in reminders if r[1].hour == now.hour and r[1].minute == now.minute]
    if due:
        return f"It's time to take: {', '.join([r[0] for r in due])}"
    return "No reminders due now."


# === Gemini Chat Functions ===
def chat_with_gemini(prompt):
    """Chat with Google's Gemini AI"""
    try:
        model = genai.GenerativeModel("models/gemini-2.0-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error with Gemini API: {e}"


# === Wake Word Handler ===
def wait_for_wake_word():
    """Wait until wake word is detected"""
    speak("Sahara is now listening. Say the wake word to begin.")
    while True:
        print("Listening for wake word...")
        wake_input = listen()
        if wake_word in wake_input:
            return
        elif wake_input:
            print(f"Heard something else: {wake_input}")


# === Background Processes ===
def start_reminder_checker():
    """Start background thread to check reminders"""
    def check_periodically():
        while True:
            check_reminders()
            time.sleep(60)  # Check every minute
    
    reminder_thread = threading.Thread(target=check_periodically, daemon=True)
    reminder_thread.start()


# === Main Function ===
def main():
    """Main function to run the voice assistant"""
    # Initialize database
    initialize_db()
    
    # Start background processes
    start_reminder_checker()
    
    # Wait for wake word
    wait_for_wake_word()
    speak("Hello, how can I help you?")

    while True:
        user_input = listen()

        if not user_input:
            speak("I'm still here. What would you like me to do?")
            continue

        # Calendar event creation
        if "create event" in user_input:
            speak("What is the event title?")
            title = listen()

            speak("When is the event? Please say the time like 8:30 PM.")
            time_spoken = listen()
            time_obj = parse_time_string(time_spoken)

            if time_obj:
                speak(f"Creating event '{title}' at {time_obj.strftime('%I:%M %p')}.")
                create_cronofy_event(title, time_obj)
            else:
                speak("Sorry, I couldn't understand the time. Please try again.")

        # Timer functionality
        elif "reminder" in user_input or "alarm" in user_input or "timer" in user_input:
            seconds = extract_seconds(user_input)
            if seconds:
                speak(f"Okay, a timer for {seconds} seconds is set! I'll let you know when it's up.")
                set_timer(seconds)
            else:
                speak("Please tell me the duration for the reminder.")

        # Calendar event listing
        elif any(kw in user_input for kw in ["show", "list", "calendar", "event", "upcoming"]):
            if "event" in user_input or "calendar" in user_input or "upcoming" in user_input:
                list_upcoming_events()
            else:
                speak("Did you mean to list your upcoming events?")

        # Medicine reminders
        elif "medicine" in user_input or "medication" in user_input:
            response = check_medication_reminders(user_input)
            speak(response)

        # Test Google Calendar connectivity
        elif "test google" in user_input or "google calendar" in user_input:
            speak("Testing connection to Google Calendar...")
            success, message = test_google_calendar_api()
            if success:
                speak("Successfully connected to Google Calendar.")
            else:
                speak(f"Failed to connect to Google Calendar. {message}")

        # Exit command
        elif any(kw in user_input for kw in ["stop", "cancel", "exit", "bye"]):
            speak("Okay, ending the session. Call me again if you need anything.")
            break

        # Default: chat with Gemini
        else:
            response = chat_with_gemini(user_input)
            speak(response)

        time.sleep(1)


# Run the application
if __name__ == "__main__":
    main()