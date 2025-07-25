# 🎙️ Nova - AI Voice Assistant

**Nova** is a cross-platform AI voice assistant built with Python (Flask backend), React (frontend), and Porcupine wake-word detection. It allows natural language voice interaction for tasks like opening apps, controlling Spotify, managing reminders, sending messages, and much more.

---

## 🚀 Features

- ✅ Wake word activation via **"Hey Nova"**
- 🎧 Voice input and output (Google Speech Recognition + pyttsx3)
- 🔊 App launching (VS Code, Spotify, Notion, Slack, etc.)
- 🗓️ Smart reminders (with natural date parsing + AppleScript)
- 🧠 ChatGPT integration
- 🔢 Math evaluation
- 🌐 Google search & Wikipedia answers
- 🌤️ Weather info (OpenWeatherMap API)
- 🕒 Time & date for any city
- 📢 Volume controls (mute, unmute, increase, decrease)
- 🧾 Jokes & news headlines (Reddit RSS)
- 🎵 Spotify control via AppleScript
- 💬 iMessage support (individual & group)
- 🌐 React frontend to interact via button or poll for wake-word triggers

---

## 🛠️ Stack

| Layer        | Tech                          |
|--------------|-------------------------------|
| Frontend     | React (with localStorage sync)|
| Backend      | Flask, Python                 |
| Wake Word    | Porcupine (via `pvporcupine`) |
| TTS / STT    | `pyttsx3`, `speech_recognition` |
| NLP / AI     | OpenAI GPT (via API)          |
| Others       | AppleScript, dateparser, Wikipedia, Spotify, etc. |

---

## 📦 Setup Instructions

### 1. Clone the Repo

```bash
git clone https://github.com/yourusername/nova-voice-assistant.git
cd nova-voice-assistant
```

### 2. Backend
Virtual Env
```bash
python3 -m venv venv
source venv/bin/activate
```
Dependencies
```bash
pip install -r requirements.txt
```
Run backend at
```bash
python3 app.py
```

### 3. Frontend
```bash
cd frontend
npm install
npm start
```

## 🧠 Architecture Overview

- app.py: Main Flask server and command routing
- wake_word_listener.py: Listens for "Hey Nova" using Porcupine
- frontend/: React UI with toggle and mic input button
- AppleScript: Used for Spotify and iMessage control
- TTS/STT: Via pyttsx3 and Google STT through speech_recognition

## 📷 UI Snapshot
<img width="599" height="813" alt="Screenshot 2025-07-25 at 1 41 49 PM" src="https://github.com/user-attachments/assets/86f1e1d8-d652-4d1b-aaf8-fa61a9e1fbd5" />
