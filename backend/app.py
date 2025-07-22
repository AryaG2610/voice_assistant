import speech_recognition as sr
import pyttsx3
import webbrowser
import subprocess
import os
import wikipedia
import requests
import openai
import threading
import re
import dateparser
import dateparser.search
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS

# Optional: Load these from environment variables or config file
OPENWEATHER_API_KEY = "62c0fb19fb4d603d082a334989c5edc3"
OPENAI_API_KEY = "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"
openai.api_key = OPENAI_API_KEY

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3001"}})

recognizer = sr.Recognizer()
engine = pyttsx3.init()

# Voice feedback toggle
voice_enabled = True

# For memory
memory = {}

# For managing speech threads and safe stopping
speak_lock = threading.Lock()
speaking_thread = None

def speak(text):
    global speaking_thread

    def run_speech():
        engine.say(text)
        engine.runAndWait()

    if voice_enabled:
        with speak_lock:
            # Stop any ongoing speech immediately
            engine.stop()

        # If previous speech thread is still running, we just start a new one
        speaking_thread = threading.Thread(target=run_speech)
        speaking_thread.start()

@app.route("/listen", methods=["GET"])
def listen():
    try:
        with speak_lock:
            engine.stop()  # Stop current speech if any

        with sr.Microphone() as source:
            print("Listening (from API)...")
            audio = recognizer.listen(source)
            command = recognizer.recognize_google(audio).lower()
            print(f"Recognized: {command}")
            response = handle_command(command)
            speak(response)
            return jsonify({"command": command, "response": response})
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"command": "", "response": "Failed to listen or recognize."})

@app.route("/toggle-voice", methods=["POST"])
def toggle_voice():
    global voice_enabled
    data = request.get_json()
    voice_enabled = data.get("enabled", True)
    return jsonify({"voice_enabled": voice_enabled})

@app.route("/get-voice-status", methods=["GET"])
def get_voice_status():
    return jsonify({"voice_enabled": voice_enabled})

# ------------------ Command Routing ------------------

def handle_command(command):
    global voice_enabled

    if "turn off voice" in command or "mute voice" in command:
        voice_enabled = False
        return "Voice feedback disabled"
    elif "turn on voice" in command or "unmute voice" in command:
        voice_enabled = True
        return "Voice feedback enabled"
    elif "open" in command:
        return handle_app_launch(command)
    elif "volume" in command or "mute" in command:
        return handle_volume(command)
    elif "screenshot" in command:
        return handle_screenshot()
    elif "time" in command or "date" in command:
        return handle_time_date(command)
    elif "weather" in command:
        return handle_weather(command)
    elif "calculate" in command or "what is" in command or "evaluate" in command or "solve" in command:
        return handle_math(command)
    elif "who is" in command or "what is" in command:
        return handle_wikipedia(command)
    elif "remember" in command or "what's my" in command:
        return handle_memory(command)
    elif "remind me" in command:
        return handle_reminder(command)
    elif "joke" in command:
        return handle_joke()
    elif "news" in command:
        return handle_news()
    elif "chat" in command or "talk" in command or "ai" in command:
        return handle_chatgpt(command)
    else:
        return "Sorry, I don't understand that."

# ------------------ Feature Handlers ------------------

def handle_app_launch(command):
    app_map = {
        "vs code": {
            "app_name": "Visual Studio Code",
            "url": "https://vscode.dev"
        },
        "spotify": {
            "app_name": "Spotify",
            "url": "https://open.spotify.com"
        },
        "slack": {
            "app_name": "Slack",
            "url": "https://slack.com"
        },
        "notion": {
            "app_name": "Notion",
            "url": "https://www.notion.so"
        },
        "discord": {
            "app_name": "Discord",
            "url": "https://discord.com/app"
        },
        "chrome": {
            "app_name": "Google Chrome",
            "url": "https://www.google.com"
        },
        "youtube": {
            "app_name": None,
            "url": "https://www.youtube.com"
        },
        "github": {
            "app_name": None,
            "url": "https://github.com"
        },
        "whatsapp": {
            "app_name": "WhatsApp",
            "url": "https://web.whatsapp.com"
        },
        "messages": {
            "app_name": "Messages",
            "url": None  # No browser fallback
        },
        "facetime": {
            "app_name": "FaceTime",
            "url": None  # No browser fallback
        }
    }

    for key, value in app_map.items():
        if key in command:
            app_name = value["app_name"]
            url = value["url"]

            # Try launching desktop app
            if app_name:
                try:
                    subprocess.Popen(["open", "-a", app_name])
                    return f"Opening {key.title()}"
                except Exception:
                    pass  # Fallback if available

            # Open URL if defined
            if url:
                webbrowser.open(url)
                return f"Opening {key.title()} in browser"

            return f"Could not open {key.title()}"

    return "App not recognized"


def handle_volume(command):
    if "mute" in command:
        os.system("osascript -e 'set volume output muted true'")
        return "Volume muted"
    elif "unmute" in command:
        os.system("osascript -e 'set volume output muted false'")
        return "Volume unmuted"
    elif "increase" in command:
        os.system("osascript -e 'set volume output volume ((output volume of (get volume settings)) + 10)'")
        return "Increasing volume"
    elif "decrease" in command:
        os.system("osascript -e 'set volume output volume ((output volume of (get volume settings)) - 10)'")
        return "Decreasing volume"
    return "Volume command not recognized"

def handle_screenshot():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"{os.path.expanduser('~')}/Desktop/screenshot_{timestamp}.png"
    os.system(f"screencapture {path}")
    return f"Screenshot saved to Desktop as screenshot_{timestamp}.png"

def handle_time_date(command):
    if "time" in command:
        return f"The time is {datetime.now().strftime('%I:%M %p')}"
    elif "date" in command:
        return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}"
    return "Time or date not recognized"

def handle_weather(command):
    import re
    city = re.search(r"weather in (.+)", command)
    if not city:
        return "Please specify a city, like 'weather in London'"
    city_name = city.group(1).strip()
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHER_API_KEY}&units=imperial"
    try:
        res = requests.get(url)
        print(f"Weather API response: {res.status_code} - {res.text}")
        data = res.json()
        if data.get("cod") != 200:
            return f"Error fetching weather: {data.get('message', 'unknown error')}"
        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]
        return f"The weather in {city_name} is {desc} with a temperature of {temp}°F."
    except Exception as e:
        print("Weather API error:", e)
        return "Couldn't fetch weather data."

def handle_wikipedia(command):
    try:
        topic = command.replace("who is", "").replace("what is", "").strip()
        print(f"Searching Wikipedia for: {topic}")
        result = wikipedia.summary(topic, sentences=2)
        return result
    except Exception as e:
        print("Wikipedia error:", e)
        return "Couldn't fetch Wikipedia info."

def handle_math(command):
    try:
        # Remove common leading phrases from the command
        expression = command.lower()
        expression = re.sub(r"(calculate|what is|solve|evaluate|convert|please|the|answer to)", "", expression)

        # Now expression should be just the math expression, like "2 + 2"

        # Remove any unwanted characters (keep digits, operators, parentheses, spaces)
        expression = re.sub(r"[^0-9\.\+\-\*\/\%\(\)\s]+", "", expression).strip()

        if not expression:
            return "Sorry, I couldn't find a valid math expression."

        print(f"Math expression to evaluate: '{expression}'")

        # Evaluate the math expression safely
        result = eval(expression)

        return f"The result is {result}"
    except Exception as e:
        print("Math evaluation error:", e)
        return "Sorry, I couldn't solve that."


def handle_chatgpt(command):
    try:
        prompt = command.replace("chat", "").replace("ai", "").replace("talk", "").strip()
        print(f"Sending prompt to ChatGPT: {prompt}")
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        print("ChatGPT error:", e)
        return "Failed to contact ChatGPT."

def handle_memory(command):
    if "remember" in command:
        key = command.replace("remember", "").strip().split(" is ")
        if len(key) == 2:
            memory[key[0].strip()] = key[1].strip()
            return f"Okay, I’ll remember that {key[0].strip()} is {key[1].strip()}"
    else:
        for k in memory:
            if k in command:
                return f"Your {k} is {memory[k]}"
    return "Sorry, couldn't store or retrieve memory."

def handle_reminder(command):
    try:
        task_match = re.search(r"remind me to (.+)", command)
        if not task_match:
            return "Sorry, I couldn't understand the reminder task."

        reminder_text = task_match.group(1).strip()
        search_result = dateparser.search.search_dates(reminder_text, settings={'PREFER_DATES_FROM': 'future'})

        reminder_time = None
        task_clean = reminder_text

        if search_result:
            first_date_text, first_date_obj = search_result[0]
            reminder_time = first_date_obj
            
            task_clean = reminder_text.replace(first_date_text, "").strip(" ,.-")

        if reminder_time and reminder_time > datetime.now():
            apple_date_str = reminder_time.strftime('%A, %B %d, %Y at %I:%M:%S %p')

            applescript = f'''
            tell application "Reminders"
                set newReminder to make new reminder with properties {{name:"{task_clean}"}}
                set due date of newReminder to date "{apple_date_str}"
            end tell
            '''
            subprocess.run(["osascript", "-e", applescript])
            return f"Reminder set: '{task_clean}' at {reminder_time.strftime('%I:%M %p on %b %d')}"
        else:
            applescript = f'''
            tell application "Reminders"
                make new reminder with properties {{name:"{task_clean}"}}
            end tell
            '''
            subprocess.run(["osascript", "-e", applescript])
            return f"Reminder set: '{task_clean}' without a specific time"
    except Exception as e:
        print("Reminder error:", e)
        return "Sorry, couldn't set the reminder."


def handle_joke():
    return "Why do programmers prefer dark mode? Because light attracts bugs!"

def handle_news():
    try:
        headers = {
            "User-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        res = requests.get("https://www.reddit.com/r/news/.rss", headers=headers)
        print(f"News API response: {res.status_code}")
        import xml.etree.ElementTree as ET
        root = ET.fromstring(res.text)
        titles = [item.find("title").text for item in root.findall(".//item")[:3]]
        return "Here are the top news headlines: " + "; ".join(titles)
    except Exception as e:
        print("News API error:", e)
        return "Couldn't fetch news."

if __name__ == "__main__":
    app.run(debug=True)
