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
import pytz
from wake_word_listener import start_wake_word_thread
from fuzzywuzzy import fuzz, process
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS

# apis
OPENWEATHER_API_KEY = "API_KEY_HERE"
# OPENAI_API_KEY = "API_KEY_HERE"
# openai.api_key = OPENAI_API_KEY

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

recognizer = sr.Recognizer()
engine = pyttsx3.init()

# voice feedback toggle
voice_enabled = True

# managing speech threads and safe stopping
speak_lock = threading.Lock()
speaking_thread = None

def speak(text):
    global speaking_thread

    def run_speech():
        engine.say(text)
        engine.runAndWait()

    if voice_enabled:
        with speak_lock:
            engine.stop()

        speaking_thread = threading.Thread(target=run_speech)
        speaking_thread.start()

@app.route("/listen", methods=["GET"])
def listen():
    try:
        with speak_lock:
            engine.stop()  

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

# Global state to hold last voice response
latest_result = {"command": None, "response": None}

@app.route("/listenNova", methods=["POST"])
def listenNova():
    global latest_result
    try:
        with sr.Microphone() as source:
            print("🎙 Listening for command...")
            audio = recognizer.listen(source, timeout=5)

        command = recognizer.recognize_google(audio)
        print(f"🧠 You said: {command}")
        engine.say(f"You said: {command}")
        engine.runAndWait()

        response = handle_command(command)
        latest_result = {"command": command, "response": response}

        return jsonify({"status": "success", "command": command, "response": response})

    except Exception as e:
        print("❌ Error:", str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/get-latest-response")
def get_latest_response():
    return jsonify(latest_result)
    

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
    elif "how" in command or "search" in command:
        return handle_google_search(command)
    elif "open" in command:
        return handle_app_launch(command)
    elif "volume" in command or "mute" in command:
        return handle_volume(command)
    elif "time" in command or "date" in command:
        return handle_time_date(command)
    elif "weather" in command:
        return handle_weather(command)
    elif "calculate" in command or "what is" in command or "evaluate" in command or "solve" in command:
        return handle_math(command)
    elif "who is" in command or "what is" in command:
        return handle_wikipedia(command)
    elif "remind me" in command:
        return handle_reminder(command)
    elif "joke" in command:
        return handle_joke()
    elif "news" in command:
        return handle_news()
    elif "chat" in command or "talk" in command or "ai" in command:
        return handle_chatgpt(command)
    elif "play" in command or "pause" in command or "stop" in command or "next" in command or "previous" in command or "skip" in command:
        return handle_music(command)
    if "send text to" in command and "that" in command:
        if "group" in command.lower():
            return handle_group_text_message(command)
        else:
            return handle_text_message(command)
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
            "url": None  
        },
        "facetime": {
            "app_name": "FaceTime",
            "url": None 
        },
        "google": {
            "app_name": None,
            "url": "https://www.google.com"
        },
        "chat gpt": {
            "app_name": "ChatGPT",
            "url": "https://chat.openai.com"
        },
        "calendar": {
            "app_name": "Calendar",
            "url": None  
        },
        "notes": {
            "app_name": "Notes",
            "url": None  
        }
    }

    for key, value in app_map.items():
        if key in command:
            app_name = value["app_name"]
            url = value["url"]

            if app_name:
                try:
                    subprocess.Popen(["open", "-a", app_name])
                    return f"Opening {key.title()}"
                except Exception:
                    pass 
                
            if url:
                webbrowser.open(url)
                return f"Opening {key.title()} in browser"

            return f"Could not open {key.title()}"

    return "App not recognized"

def handle_google_search(command):
    print(f"Handling Google search command: '{command}'")
    try:
        query = re.sub(r"\b(how|search)\b", "", command, flags=re.IGNORECASE)
        query = re.sub(r"\b(for|to|about|in|on|at)\b", "", query, flags=re.IGNORECASE).strip()
        if query:
            search_url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
            print(f"Opening search URL: {search_url}")
            webbrowser.open(search_url)
            return f"Searching Google for: {query}"
        return "Please provide a query after 'how' or 'search' to search on Google"
    except Exception as e:
        print(f"Google search error: {e}")
        return "Failed to perform Google search."

def handle_volume(command):
    if "unmute" in command:
        os.system("osascript -e 'set volume output muted false' -e 'set volume output volume 50'")
        return "Volume unmuted"
    elif "mute" in command:
        os.system("osascript -e 'set volume output muted true'")
        return "Volume muted" 
    elif "increase" in command:
        os.system("osascript -e 'set volume output volume ((output volume of (get volume settings)) + 10)'")
        return "Increasing volume"
    elif "decrease" in command:
        os.system("osascript -e 'set volume output volume ((output volume of (get volume settings)) - 10)'")
        return "Decreasing volume"
    return "Volume command not recognized"

def handle_time_date(command):
    try:
        if "time" in command and "in" not in command:
            return f"The current local time is {datetime.now().strftime('%I:%M %p')}"

        location_match = re.search(r"time in (.+)", command, re.IGNORECASE)
        if location_match:
            city_name = location_match.group(1).strip()
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHER_API_KEY}"
            try:
                res = requests.get(url)
                print(f"Time API response for {city_name}: {res.status_code} - {res.text}")
                data = res.json()
                if data.get("cod") != 200:
                    return f"Error fetching time for {city_name}: {data.get('message', 'unknown error')}"
                
                timezone_offset = data["timezone"]  
                utc_time = datetime.now(pytz.UTC)
                
                local_time = utc_time + timedelta(seconds=timezone_offset)
                return f"The current time in {city_name} is {local_time.strftime('%I:%M %p')}"

            except Exception as e:
                print(f"Time API error for {city_name}: {e}")
                return f"Couldn't fetch time for {city_name}."
        
        elif "date" in command:
            return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}"
        
        return "Time or date command not recognized"
    
    except Exception as e:
        print(f"Error in handle_time_date: {e}")
        return "Sorry, something went wrong while fetching the time."

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
        expression = command.lower()
        expression = re.sub(r"(calculate|what is|solve|evaluate|convert|please|the|answer to)", "", expression)
        
        expression = re.sub(r"[^0-9\.\+\-\*\/\%\(\)\s]+", "", expression).strip()

        if not expression:
            return "Sorry, I couldn't find a valid math expression."

        print(f"Math expression to evaluate: '{expression}'")

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

def handle_reminder(command):
    try:
        task_match = re.search(r"remind me to (.+)", command, re.IGNORECASE)
        if not task_match:
            return "Sorry, I couldn't understand the reminder task."

        reminder_text = task_match.group(1).strip()
        reminder_text = reminder_text.replace("p.m.", "PM").replace("a.m.", "AM")

        cdt_tz = pytz.timezone('America/Chicago')

        search_result = dateparser.search.search_dates(
            reminder_text,
            settings={
                'PREFER_DATES_FROM': 'future',
                'TIMEZONE': 'America/Chicago',
                'TO_TIMEZONE': 'America/Chicago',
                'STRICT_PARSING': True
            }
        )

        reminder_time = None
        task_clean = reminder_text

        if search_result:
            first_date_text, first_date_obj = search_result[0]
            reminder_time = first_date_obj

            pattern = r"\b(?:at|on|by|around|about)?\s*" + re.escape(first_date_text) + r"\b"
            task_clean = re.sub(pattern, "", reminder_text, flags=re.IGNORECASE).strip(" ,.-")
            task_clean = re.sub(r"\b(PM|AM|tomorrow|today)\b", "", task_clean, flags=re.IGNORECASE).strip(" ,.-")

        print(f"Parsed reminder time: {reminder_time}")

        if reminder_time and not reminder_time.tzinfo:
            reminder_time = cdt_tz.localize(reminder_time)

        now = datetime.now(cdt_tz)
        if reminder_time and reminder_time > now:
            year = reminder_time.year
            month = reminder_time.strftime("%B")  
            day = reminder_time.day
            hour = reminder_time.hour
            minute = reminder_time.minute

            applescript = f'''
            set theDate to current date
            set year of theDate to {year}
            set month of theDate to {month}
            set day of theDate to {day}
            set time of theDate to (({hour} * hours) + ({minute} * minutes))
            tell application "Reminders"
                tell list "Reminders"
                    set newReminder to make new reminder with properties {{name:"{task_clean}", due date:theDate}}
                end tell
            end tell
            '''
            print("Executing AppleScript:\n", applescript)
            subprocess.run(["osascript", "-e", applescript])
            return f"Reminder set: '{task_clean}' at {reminder_time.strftime('%I:%M %p on %b %d')}"
        else:
            applescript = f'''
            tell application "Reminders"
                tell list "Reminders"
                    make new reminder with properties {{name:"{task_clean}"}}
                end tell
            end tell
            '''
            subprocess.run(["osascript", "-e", applescript])
            return f"Reminder set: '{task_clean}' without a specific time"
    except Exception as e:
        print("Reminder error:", e)
        return "Sorry, couldn't set the reminder."

    
    
def handle_joke():
    try:
        res = requests.get("https://official-joke-api.appspot.com/random_joke")
        joke = res.json()
        return f"{joke['setup']} ... {joke['punchline']}"
    except Exception as e:
        print("Joke fetch error:", e)
        return "Sorry, I couldn't fetch a joke."


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

def handle_music(command):
    command = command.lower()

    try:
        if "play" in command:
            play_match = re.search(r"play (.+)", command)
            if play_match:
                query = play_match.group(1).strip()
                if query in ["music", ""]:
                    applescript = 'tell application "Spotify" to play'
                    subprocess.run(["osascript", "-e", applescript])
                    return "Resuming Spotify playback."
                else:
                    applescript = f'''
                    tell application "Spotify"
                        set results to search "{query}"
                        if results is not {{}} then
                            play track item 1 of results
                            return "Playing {query} on Spotify."
                        else
                            return "Could not find {query} on Spotify."
                        end if
                    end tell
                    '''
                    result = subprocess.run(["osascript", "-e", applescript], capture_output=True, text=True)
                    return result.stdout.strip()
            else:
                applescript = 'tell application "Spotify" to play'
                subprocess.run(["osascript", "-e", applescript])
                return "Playing Spotify."

        elif "pause" in command or "stop" in command:
            applescript = 'tell application "Spotify" to pause'
            subprocess.run(["osascript", "-e", applescript])
            return "Spotify playback paused."

        elif "next" in command or "skip" in command:
            applescript = 'tell application "Spotify" to next track'
            subprocess.run(["osascript", "-e", applescript])
            return "Skipping to next track on Spotify."

        elif "previous" in command or "back" in command:
            applescript = 'tell application "Spotify" to previous track'
            subprocess.run(["osascript", "-e", applescript])
            return "Going back to previous track on Spotify."

        else:
            return "Spotify music command not recognized."

    except Exception as e:
        print("Spotify music command error:", e)
        return "Failed to control Spotify."

# ------------------ iMessage Utilities ------------------

def get_contact_handles(contact_name):
    try:
        contact_name_lower = contact_name.lower()

        apple_script = f'''
        set contactName to "{contact_name_lower}"

        tell application "Contacts"
            set theContacts to {{}}
            repeat with p in people
                try
                    set personName to name of p
                    if personName is not missing value then
                        set lowerName to (do shell script "echo " & quoted form of personName & " | tr '[:upper:]' '[:lower:]'")
                        if lowerName contains contactName then
                            set end of theContacts to p
                        end if
                    end if
                end try
            end repeat

            if theContacts is not {{}} then
                set handleList to {{}}
                repeat with c in theContacts
                    repeat with ph in phones of c
                        set end of handleList to value of ph
                    end repeat
                    repeat with em in emails of c
                        set end of handleList to value of em
                    end repeat
                end repeat
                if handleList is not {{}} then
                    return handleList
                else
                    return "NO_HANDLES"
                end if
            else
                return "NOT_FOUND"
            end if
        end tell
        '''

        process = subprocess.Popen(
            ['osascript', '-'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(apple_script)

        print("AppleScript output:", stdout.strip())
        if stderr.strip():
            print("AppleScript error:", stderr.strip())

        if process.returncode != 0 or "NOT_FOUND" in stdout:
            return []
        if "NO_HANDLES" in stdout:
            return []

        handles = [h.strip() for h in stdout.strip().split(",") if h.strip()]
        return handles

    except Exception as e:
        print("get_contact_handles error:", e)
        return []

def send_imessage(handle, message):
    # Sends an iMessage to an individual via AppleScript
    try:
        apple_script = f'''
        on run {{}}
            tell application "Messages"
                set targetService to 1st service whose service type = iMessage
                set targetBuddy to buddy "{handle}" of targetService
                send "{message}" to targetBuddy
            end tell
        end run
        '''
        process = subprocess.Popen(['osascript', '-'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate(apple_script)
        if process.returncode != 0:
            print("send_imessage AppleScript error:", stderr)
            return False
        return True
    except Exception as e:
        print("send_imessage error:", e)
        return False

def send_group_imessage(group_name, message):
    # Sends an iMessage to a group chat by its name via AppleScript with fuzzy matching
    try:
        # Step 1: Retrieve all group chat names
        apple_script_list_chats = '''
        tell application "Messages"
            set chatNames to {}
            repeat with c in chats
                try
                    if name of c is not missing value then
                        set end of chatNames to name of c
                    end if
                end try
            end repeat
            return chatNames
        end tell
        '''
        chat_process = subprocess.Popen(
            ['osascript', '-'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = chat_process.communicate(apple_script_list_chats)

        print("List chats AppleScript output:", stdout.strip())
        if stderr.strip():
            print("List chats AppleScript error:", stderr.strip())

        if chat_process.returncode != 0 or not stdout.strip():
            return False

        # Parse the group chat names
        group_chat_names = [name.strip() for name in stdout.strip().split(",") if name.strip()]
        if not group_chat_names:
            return False

        # Step 2: Fuzzy match the provided group name
        best_match = process.extractOne(group_name, group_chat_names, scorer=fuzz.token_sort_ratio)
        if not best_match or best_match[1] < 60:  # Threshold for match confidence
            print(f"No close match found for group '{group_name}'. Best match: {best_match}")
            return False

        matched_group_name = best_match[0]
        print(f"Matched group '{group_name}' to '{matched_group_name}' with score {best_match[1]}")

        # Step 3: Send message to the matched group
        apple_script_send = f'''
        on run {{}}
            set groupName to "{matched_group_name}"
            set messageText to "{message}"
            tell application "Messages"
                set targetService to 1st service whose service type = iMessage
                set foundChat to false
                repeat with c in chats
                    try
                        if name of c is not missing value then
                            if name of c is groupName then
                                send messageText to c
                                set foundChat to true
                                exit repeat
                            end if
                        end if
                    end try
                end repeat
                if foundChat then
                    return "SUCCESS"
                else
                    return "NOT_FOUND"
                end if
            end tell
        end run
        '''
        send_process = subprocess.Popen(
            ['osascript', '-'],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = send_process.communicate(apple_script_send)

        print("send_group_imessage AppleScript output:", stdout.strip())
        if stderr.strip():
            print("send_group_imessage AppleScript error:", stderr.strip())

        if send_process.returncode != 0 or "NOT_FOUND" in stdout:
            return False
        return True
    except Exception as e:
        print("send_group_imessage error:", e)
        return False


# -------------- Existing Functions ----------------

def handle_text_message(command):
    # Expected command: "send text to [contact_name or group_name] that [message]"
    try:
        match = re.search(r"send text to (.+?) that (.+)", command, re.IGNORECASE)
        if not match:
            return "Please say: send text to [contact or group name] that [message]."

        target_name = match.group(1).strip()
        message = match.group(2).strip()

        # Check if the command includes "group" to handle group chats
        if "group" in command.lower():
            success = send_group_imessage(target_name, message)
            if success:
                return f"Message sent to group '{target_name}'."
            else:
                return f"Couldn't find group chat '{target_name}'."
        else:
            # Handle individual contact
            handles = get_contact_handles(target_name)
            if not handles:
                return f"Couldn't find contact '{target_name}'."

            success = send_imessage(handles[0], message)
            if success:
                return f"Message sent to {target_name}."
            else:
                return "Failed to send the message."

    except Exception as e:
        print("handle_text_message error:", e)
        return "Sorry, there was an error sending the message."

def handle_group_text_message(command):
    # Expected command: "send text to [group_name] group that [message]"
    try:
        match = re.search(r"send text to (.+?) group that (.+)", command, re.IGNORECASE)
        if not match:
            return "Please say: send text to [group name] group that [message]."

        group_name = match.group(1).strip()
        message = match.group(2).strip()

        success = send_group_imessage(group_name, message)
        if success:
            return f"Message sent to group '{group_name}'."
        else:
            return f"Couldn't find group chat '{group_name}'."

    except Exception as e:
        print("handle_group_text_message error:", e)
        return "Sorry, there was an error sending the group message."
    
    
if __name__ == '__main__':
    # command2 = "send text to OG unks group that hello ouncs"
    # print(handle_group_text_message(command2))
    start_wake_word_thread()
    app.run(debug=True)