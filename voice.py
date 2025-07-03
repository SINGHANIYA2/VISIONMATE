import vosk
import sounddevice as sd
import queue
import json
import pyttsx3
import os
import time
from gtts import gTTS
from playsound import playsound
import noisereduce as nr
import numpy as np
import cv2

# ============================
# 👤 MEMBER 1: Dummy Caption
# ============================

def capture_frame(filename="dummy.jpg"):
    print("📸 Capturing image...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise Exception("Camera not working!")
    ret, frame = cap.read()
    if ret:
        cv2.imwrite(filename, frame)
        cap.release()
        return filename
    else:
        cap.release()
        raise Exception("Failed to capture image")

def get_scene_description(image_path):
    print("🖼️ Fake caption generated")
    return "A man is standing in front of a tree"

# ============================
# 👤 MEMBER 2: Dummy Hindi
# ============================

def generate_hindi_description(text):
    return "Ek aadmi ped ke saamne khada hai"
def generate_bengali_description(text):
    return "Ek aadmi ped ke saamne khada hai"
def generate_tamil_description(text):
    return "Ek aadmi ped ke saamne khada hai"

# ============================
# 👤 MEMBER 3: Speech I/O
# ============================

LANGUAGES = {
    "hindi": {"model": "vosk-model-hi", "lang_code": "hi"},
    "english": {"model": "vosk-model-en", "lang_code": "en"},
    # "bengali": {"model": "vosk-model-bn", "lang_code": "bn"},
    # "tamil": {"model": "vosk-model-ta", "lang_code": "ta"}
}
START = {
    "hi" : {"Mai taiyaar hoon aapko rasta dikhane ke liye"},
    "en" : {"I am ready to guide you"}
}


engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 4.0)

# using indian accent for better performance
def set_indian_voice():
    for voice in engine.getProperty('voices'):
        if "india" in voice.name.lower() or "heera" in voice.id.lower():
            engine.setProperty('voice', voice.id)
            return True
    return False

# speaking function

def speak(text, lang_code='en'):
    try:
        tld = 'co.in' if lang_code == 'en' else 'com'
        tts = gTTS(text=text, lang=lang_code, tld=tld)
        tts.save("temp.mp3")
        playsound("temp.mp3")
        os.remove("temp.mp3")
    except:
        if set_indian_voice():
            engine.say(text)
            engine.runAndWait()
        else:
            engine.say(text)
            engine.runAndWait()

#storing the voice in queue (row)
q = queue.Queue()

def callback(indata, frames, time_info, status):
    q.put(indata.copy())

# loading model and checking wheather it exists or not

def load_model(model_path):
    print(f"🔍 Checking model path: {model_path}")
    if not os.path.exists(model_path):
        print(" Model not found at:", model_path)
        exit()
    return vosk.Model(model_path)

# listening function

def listen(vosk_model):
    with sd.InputStream(samplerate=16000, blocksize=8000, dtype='int16',
                        channels=1, callback=callback):
        rec = vosk.KaldiRecognizer(vosk_model, 16000)
        print("🎙️ Listening...")
        audio_data = []

        start_time = time.time()
        while time.time() - start_time < 5:  # Record 5 seconds
            data = q.get()
            audio_data.append(data)

        full_audio = np.concatenate(audio_data, axis=0).flatten()

        #  Noise Reduction to hear input clearly

        reduced_audio = nr.reduce_noise(y=full_audio.astype(np.float32), sr=16000)

        # Convert reduced audio to int16 for Vosk
        reduced_audio = reduced_audio.astype(np.int16).tobytes()

        if rec.AcceptWaveform(reduced_audio):
            result = json.loads(rec.Result())
            return result.get("text", "")
        else:
            return ""
        
def main_loop(model, lang_code):
    text = None
    for word in START:
        if word == lang_code:
            text = word
            break
    
    speak(text)

    while True:
        try:
            image_path = capture_frame()
            english_caption = get_scene_description(image_path)

            if lang_code == "hi":
                final_output = generate_hindi_description(english_caption) #member 2 function call
            # 
            # bengali and tamil language model is not available now
            
            elif lang_code == "bn":
                final_output = generate_bengali_description(english_caption) #member 2 function call
            elif lang_code == "ta":
                final_output = generate_tamil_description(english_caption) #member 2 function call

            else:
                # no need to call the function 
                final_output = english_caption 

            speak(final_output, lang_code)

            stop_command = listen(model).lower()
            if any(word in stop_command for word in ["stop", "band kro", "ruk jaao", "exit"]):
                speak("Main ruk gaya hoon. Dhanyavaad!", lang_code)
                break

            time.sleep(5)

        except Exception as e:
            print(" Error:", e)
            speak("Scene is not clear.", lang_code)


if __name__ == "__main__":
    base_path = r"D:\GITDEMO\VISIONMATE"
    temp_model_path = os.path.join(base_path, LANGUAGES["english"]["model"])
    temp_model = load_model(temp_model_path)

    matched_lang = None
    while not matched_lang:
        speak("Apna language batayiye ")
        lang_input = listen(temp_model).lower()
        for lang in LANGUAGES:
            if lang in lang_input:
                matched_lang = lang
                break
        if not matched_lang:
            speak("Language nahi samajh aayi", "en")

    selected_model_path = os.path.join(base_path, LANGUAGES[matched_lang]["model"])
    lang_model = load_model(selected_model_path)
    lang_code = LANGUAGES[matched_lang]["lang_code"]

    speak(f"{matched_lang} select ki gayi hai.", lang_code)
    main_loop(lang_model, lang_code)
