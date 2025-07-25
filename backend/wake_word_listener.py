import threading
import requests
import pvporcupine
import sounddevice as sd
import struct
import queue
import time
import os

ACCESS_KEY = "KEY HERE"
KEYWORD_PATH = os.path.join(os.path.dirname(__file__), "Hey-Nova_en_mac_v3_0_0.ppn")
LISTEN_ENDPOINT = "http://127.0.0.1:5000/listenNova"
COOLDOWN_SECONDS = 5

q = queue.Queue()
last_trigger_time = 0

def audio_callback(indata, frames, time_info, status):
    if status:
        print("Audio Status:", status)
    q.put(bytes(indata))

def trigger_listen():
    try:
        print("🎤 Triggering assistant...")
        response = requests.post(LISTEN_ENDPOINT)
        print("✅ Assistant responded:", response.text)
    except Exception as e:
        print("❌ Error calling /listen:", e)

def wake_word_listener():
    global last_trigger_time

    # 🔧 Create the Porcupine wake word engine
    porcupine = pvporcupine.create(
        access_key=ACCESS_KEY,
        keyword_paths=[KEYWORD_PATH]
    )

    with sd.RawInputStream(
        samplerate=porcupine.sample_rate,
        blocksize=porcupine.frame_length,
        channels=1,
        dtype='int16',
        callback=audio_callback
    ):
        print("🟢 Wake word listener running... Say 'Hey Nova'")
        while True:
            pcm = q.get()
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            keyword_index = porcupine.process(pcm)

            if keyword_index >= 0:
                now = time.time()
                if now - last_trigger_time > COOLDOWN_SECONDS:
                    print("👂 Wake word 'Hey Nova' detected!")
                    last_trigger_time = now
                    threading.Thread(target=trigger_listen, daemon=True).start()
                else:
                    print("⏱ Cooldown active, ignoring repeated trigger.")

def start_wake_word_thread():
    threading.Thread(target=wake_word_listener, daemon=True).start()