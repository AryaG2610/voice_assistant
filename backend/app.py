import speech_recognition as sr
import pyttsx3
import webbrowser
import subprocess
import os
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3001"}})

# Initialize recognizer and TTS engine
recognizer = sr.Recognizer()
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def take_command():
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
        try:
            command = recognizer.recognize_google(audio)
            print(f"You said: {command}")
            return command.lower()
        except sr.UnknownValueError:
            speak("Sorry, I didn't catch that.")
            return ""
        except sr.RequestError:
            speak("Service is down.")
            return ""

@app.route("/listen", methods=["GET"])
def listen():
    try:
        with sr.Microphone() as source:
            print("Listening (from API)...")
            audio = recognizer.listen(source)
            command = recognizer.recognize_google(audio)
            print(f"Recognized: {command}")

            # Command handling
            if "google" in command:
                response = "Opening Google"
                webbrowser.open("https://www.google.com")
            elif "youtube" in command:
                response = "Opening YouTube"
                webbrowser.open("https://www.youtube.com")
            elif "your name" in command:
                response = "I am your Python assistant"
            else:
                response = "Sorry, I don't understand that."

            speak(response)

            return jsonify({"command": command, "response": response})
    except Exception as e:
        print("Error:", str(e))
        return jsonify({"command": "", "response": "Failed to listen or recognize."})

@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"message": "pong from Flask"})

if __name__ == "__main__":
    app.run(debug=True)
