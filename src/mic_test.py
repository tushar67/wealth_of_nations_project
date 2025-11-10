import io
import tempfile

import speech_recognition as sr
import streamlit as st
from pydub import AudioSegment
from streamlit_mic_recorder import mic_recorder

st.set_page_config(page_title="🎤 Voice to Text (Fixed)", layout="centered")

st.title("🎙️ Voice Recorder + Speech Recognition Test")
st.write("Click below, speak something, and watch your words appear as text!")

# Record voice
audio = mic_recorder(
    start_prompt="🎤 Start Recording",
    stop_prompt="🛑 Stop Recording",
    just_once=True,
    use_container_width=True,
    key="recorder_test",
)

if audio:
    st.info("🎧 Processing your voice...")

    try:
        # Convert WebM bytes → WAV bytes using pydub
        audio_bytes = io.BytesIO(audio["bytes"])
        sound = AudioSegment.from_file(audio_bytes, format="webm")

        # Save as temporary WAV
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
            sound.export(temp_wav.name, format="wav")
            wav_path = temp_wav.name

        # Recognize speech from WAV
        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data)

        st.success(f"🧠 Recognized Speech: {text}")

    except Exception as e:
        st.error(f"⚠️ Could not transcribe audio: {e}")

else:
    st.info("🎙️ Click 'Start Recording' and speak clearly.")
