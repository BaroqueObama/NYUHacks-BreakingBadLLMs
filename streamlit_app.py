import streamlit as st
from openai import OpenAI
import base64
import io
import asyncio
from websockets.asyncio.server import serve
from websockets import connect
from langchain_openai import ChatOpenAI

def string_to_wav(base64_string, output_path):
    # Decode the base64 string back into binary data
    binary_data = base64.b64decode(base64_string)
    
    # Write the binary data to a new .wav file
    with open(output_path, "wb") as wav_file:
        wav_file.write(binary_data)

async def send_audio(audiofile, web_url):
    audio_file = audiofile.read()

    audio_b64 = base64.b64encode(audio_file).decode()
  
    async with connect(web_url) as websocket:
        # sends in b64
        await websocket.send(audio_b64)
        print("File sent to server")

        response = await websocket.recv()
    
    print(type(response))
    return response


st.title("📄 Breaking Bad LLMs")
st.write(
    "Record an audio!"
    "To use this app, you need to provide an OpenAI API key, which you can get [here](https://platform.openai.com/account/api-keys). "
)

# Ask user for their OpenAI API key via `st.text_input`.

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

        audio = results[6:results.find("response:")]
        print("RESULTS", results[0:30])
        print("AUDIO", audio[0:30])
        string_to_wav(audio, "audio.wav")
        with open("audio.wav", "rb") as wav_file:
            st.audio(wav_file)

        text = results[results.find("response:")+9:-1]
        st.write(text)
