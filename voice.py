import vosk
import sounddevice as sd
import queue
import json
import pyttsx3
import os
from gtts import gTTS
import time

# 🌐 Supported languages
LANGUAGES = {
    "hindi": {
        "model": "vosk-model-hi",
        "lang_code": "hi"
    },
    "english": {
        "model": "vosk-model-en",
        "lang_code": "en"
    },
    "bengali": {
        "model": "vosk-model-bn",
        "lang_code": "bn"
    },
    "tamil": {
        "model": "vosk-model-ta",
        "lang_code": "ta"
    }
}

# 🔊 Global engine setup
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 1.0)

# 🔄 Try setting Indian English or regional voice
def set_voice(lang_code):
    voices = engine.getProperty('voices')
    for voice in voices:
        if lang_code in voice.id.lower() or lang_code in voice.name.lower():
            engine.setProperty('voice', voice.id)
            return True
    return False  # Voice not found

# 🗣 Universal Speak Function (Offline/Online fallback)
def speak(text, lang_code='en'):
    if set_voice(lang_code):
        engine.say(text)
        engine.runAndWait()
    else:
        print(f"⚠ Voice not found for '{lang_code}', using gTTS")
        tld = 'co.in' if lang_code == 'en' else 'com'
        tts = gTTS(text=text, lang=lang_code, tld=tld)
        tts.save("temp.mp3")
        os.system("start /min temp.mp3")
        time.sleep(4)  # Wait enough for voice to finish
        os.remove("temp.mp3")

# 🔈 Load Vosk Model
def load_model(lang_model_folder):
    if not os.path.exists(lang_model_folder):
        print(f"❌ Model not found: {lang_model_folder}")
        exit()
    try:
        return vosk.Model(lang_model_folder)
    except Exception as e:
        print("❌ Model failed to load:", e)
        exit()

# 🎧 Audio Callback
q = queue.Queue()
def callback(indata, frames, time, status):
    q.put(bytes(indata))

# 🎙 Listen in selected language
def listen(vosk_model):
    with sd.RawInputStream(samplerate=16000, blocksize=8000,
                           dtype='int16', channels=1, callback=callback):
        rec = vosk.KaldiRecognizer(vosk_model, 16000)
        print("🎙 Bolna shuru karo...")
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = json.loads(rec.Result())
                return result.get("text", "")

# 🔁 Main Loop
def main_loop(model, lang_code):
    speak("Kya aap bolna chahenge ya exit?", lang_code)
    while True:
        choice = listen(model).lower()
        if "exit" in choice:
            speak("Main band ho raha hoon. Dhanyavaad!", lang_code)
            break
        speak("Bolna shuru kijiye...", lang_code)
        text = listen(model)
        print("📝 Recognized:", text)
        speak(f"Aapne kaha: {text}", lang_code)

# 🚀 Start Program
if __name__ == "__main__":
    speak("Apni language ka naam boliye: jaise hindi, english, bengali ya tamil", "en")

    # Temporarily use English model to capture the spoken language name
    temp_model = load_model("vosk-model-en")
    user_said = listen(temp_model).lower()
    print(f"🎧 Aapne kaha: {user_said}")

    # Match spoken language with keys
    matched_lang = None
    for lang in LANGUAGES.keys():
        if lang in user_said:
            matched_lang = lang
            break

    if not matched_lang:
        speak("Maaf kijiye, aapki language samajh nahi aayi.", "en")
        exit()

    # Load selected language model
    lang_model_path = LANGUAGES[matched_lang]["model"]
    lang_code = LANGUAGES[matched_lang]["lang_code"]
    model = load_model(lang_model_path)

    speak(f"{matched_lang} bhasha select ki gayi hai. Aap shuru kar sakte hain.", lang_code)
    main_loop(model, lang_code)
