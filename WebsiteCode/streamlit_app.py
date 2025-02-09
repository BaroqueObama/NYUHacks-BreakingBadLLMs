import streamlit as st
import  streamlit_toggle as tog

import base64
import io
import asyncio
from websockets import connect
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
    
    # Write the resampled audio to the final output path as WAV
    sf.write(output_path, audio_resampled, target_sr)
    
    # Remove the temporary file
    os.remove(temp_path)

async def send_audio_and_target(audiofile, prompt, web_url):
    # Read the audio file provided by Streamlit's audio_input
    audio_file = audiofile.read()
    audio_b64 = base64.b64encode(audio_file).decode()
    
    combined = prompt + "|SPLTI|" + audio_b64
    async with connect(web_url) as websocket:
        await websocket.send(combined)
        st.write("File sent to server")
        response = await websocket.recv()
    
    st.write("Response received from server")
    return response

st.title("📄 Breaking Bad LLMs")
st.write("Record a regular piece of audio!")

# Let the user record an audio message.
uploaded_audio = st.audio_input("Record message (recommended over 6 seconds):")

# Input target transcript for cw attack.
target_prompt = st.text_input("Enter target prompt (the actual question the model will answer):")

jailbreak = st.toggle("Activate Jailbreak mode (for malicious prompts)")

defense = st.toggle("Activate sandwich LLM defenses")

if 'responsed' not in st.session_state:
    st.session_state.responsed = False

if st.button("Generate Adversarial Attack"):
    # cw_response = asyncio.run(target_prompt+"|"+)
    if uploaded_audio is None:
        st.error("Please upload an audio file first.")
    elif target_prompt is None or target_prompt == "":
        st.error("Please enter a target prompt for the CW attack.")
    else:
        st.success("CW attack prompt sent to server!")
        global cw_response
        cw_response = send_audio_and_target(uploaded_audio, target_prompt, "ws://IPADDR2:4242")
        st.session_state.responsed = True

# Set the websocket URL for the Llama server.
ws_url = "ws://IPADDR1:9000"

if st.session_state.responsed:
    part = cw_response.split("|SPLTI|")
    adv_wav_b64 = part[0]
    nat_wav_b64 = part[1]
    adv_transcript = part[2]
    nat_transcript = part[3]
    adv_response = part[4]
    nat_response = part[5]
    # Convert both base64 audio strings into WAV files (resampled at 16000 Hz).
    string_to_wav(adv_wav_b64, "adv_audio.wav", target_sr=16000)
    string_to_wav(nat_wav_b64, "nat_audio.wav", target_sr=16000)
    
    # Display the natural audio.
    st.subheader("Natural Audio")
    with open("nat_audio.wav", "rb") as nat_file:
        st.audio(nat_file, format="audio/wav", start_time=0)
    st.write(f"Model Interpretation: {nat_transcript}")
    st.write(f"Model Response: {nat_response}")
    # Display the adversarial audio.
    st.subheader("Adversarial Audio")
    with open("adv_audio.wav", "rb") as adv_file:
        st.audio(adv_file, format="audio/wav", start_time=0)
    st.write(f"Model Interpretation: {adv_transcript}")
    st.write(f"Model Response: {adv_response}")
