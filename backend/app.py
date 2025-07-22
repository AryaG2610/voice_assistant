import speech_recognition as sr
import pyttsx3
import webbrowser
import subprocess
import os
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3001"}})

recognizer = sr.Recognizer()
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

@app.route("/listen", methods=["GET"])
def listen():
    try:
        with sr.Microphone() as source:
            print("Listening (from API)...")
            audio = recognizer.listen(source)
            command = recognizer.recognize_google(audio)
            print(f"Recognized: {command}")

            command = command.lower()
            response = handle_command(command)

            speak(response)
            return jsonify({"command": command, "response": response})
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"command": "", "response": "Failed to listen or recognize."})

def handle_command(command):
    if "google" in command:
        webbrowser.open("https://www.google.com")
        return "Opening Google"
    elif "youtube" in command:
        webbrowser.open("https://www.youtube.com")
        return "Opening YouTube"
    elif "github" in command:
        webbrowser.open("https://github.com")
        return "Opening GitHub"
    elif "spotify" in command:
        webbrowser.open("https://open.spotify.com")
        return "Opening Spotify"
    elif "your name" in command:
        return "I am your Python assistant"
    elif "time" in command:
        now = datetime.now().strftime("%I:%M %p")
        return f"The time is {now}"
    elif "joke" in command:
        return "Why do programmers prefer dark mode? Because the light attracts bugs!"
    elif "search for" in command:
        query = command.split("search for")[-1].strip()
        webbrowser.open(f"https://www.google.com/search?q={query}")
        return f"Searching Google for {query}"
    elif "shutdown" in command:
        return "Sorry, I won't shut down your system."
    else:
        return "Sorry, I don't understand that."

if __name__ == "__main__":
    app.run(debug=True)
