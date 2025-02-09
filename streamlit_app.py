import streamlit as st
from openai import OpenAI
import base64
import io
import asyncio
from websockets.asyncio.server import serve
from websockets import connect
from langchain_openai import ChatOpenAI
import os
import librosa
import soundfile as sf

def string_to_wav(base64_string, output_path, target_sr=16000):
    # Decode the base64 string back into binary data
    binary_data = base64.b64decode(base64_string)
    
    # Write the binary data to a temporary file
    temp_path = output_path + ".tmp"
    with open(temp_path, "wb") as wav_file:
        wav_file.write(binary_data)
    
    # Load the audio using its original sampling rate (sr=None)
    audio, orig_sr = librosa.load(temp_path, sr=None)
    
    # Resample if the original sampling rate is different from target_sr
    if orig_sr != target_sr:
        audio_resampled = librosa.resample(audio, orig_sr, target_sr)
    else:
        audio_resampled = audio
    
    # Write the resampled audio to the final output path
    sf.write(output_path, audio_resampled, target_sr)
    
    # Remove the temporary file
    os.remove(temp_path)

async def send_audio(audiofile, web_url):
    audio_file = audiofile.read()
    audio_b64 = base64.b64encode(audio_file).decode()
  
    async with connect(web_url) as websocket:
        # Send the audio in base64 format
        await websocket.send(audio_b64)
        st.write("File sent to server")
        response = await websocket.recv()
    
    st.write("Response received from server")
    return response

st.title("📄 Breaking Bad LLMs")
st.write(
    "Record an audio! "
    "To use this app, you need to provide an OpenAI API key, which you can get [here](https://platform.openai.com/account/api-keys)."
)

# Ask user for their OpenAI API key via st.text_input.
openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
else:
    # Create an OpenAI client.
    client = OpenAI(api_key=openai_api_key)

    # Let the user record audio.
    uploaded_audio = st.audio_input("Record message:")

    ws_url = "ws://localhost:8765"

    if uploaded_audio is not None:
        # Use asyncio to run the WebSocket function and wait for the response
        results = asyncio.run(send_audio(uploaded_audio, ws_url))
        
        # Expected results format:
        # "adv:<base64_adv_audio>|nat:<base64_nat_audio>|transcript:<transcript_text>"
        parts = results.split("|")
        adv_audio_b64 = ""
        nat_audio_b64 = ""
        transcript = ""
        for part in parts:
            if part.startswith("adv:"):
                adv_audio_b64 = part[len("adv:"):].strip()
            elif part.startswith("nat:"):
                nat_audio_b64 = part[len("nat:"):].strip()
            elif part.startswith("transcript:"):
                transcript = part[len("transcript:"):].strip()
        
        # Save both audio files (resampled at 16kHz)
        string_to_wav(adv_audio_b64, "adv_audio.wav", target_sr=16000)
        string_to_wav(nat_audio_b64, "nat_audio.wav", target_sr=16000)
        
        # Display both audio files on the webpage
        st.subheader("Adversarial Audio")
        with open("adv_audio.wav", "rb") as adv_file:
            st.audio(adv_file, format="audio/wav", start_time=0)
            
        st.subheader("Natural Audio")
        with open("nat_audio.wav", "rb") as nat_file:
            st.audio(nat_file, format="audio/wav", start_time=0)
        
        # Display the transcript text
        st.subheader("Transcript")
        st.write(transcript)
