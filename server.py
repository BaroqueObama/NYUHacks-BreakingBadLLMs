import streamlit as st
from openai import OpenAI
import base64
import io
import asyncio
from websockets.asyncio.server import serve
from websockets import connect
from langchain_openai import ChatOpenAI
import wave
import whisper
import audiotools
import soundfile as sf
import librosa

# Global configuration:
MODEL_SIZE = "tiny"        # or "medium", "large", etc.
AUDIO_TYPE_ADV = "adv"
AUDIO_TYPE_NAT = "nat"
SAVE_DIR = f"/workspace/pythonny/attacks/cw/whisper-{MODEL_SIZE}/2000/save/"
LLAMA_WS_URL = "ws://localhost:9000"  # The websocket URL for the Llama server

def wav_to_string(file_path):
    """Read a wav file and return its base64 string."""
    with open(file_path, "rb") as wav_file:
        binary_data = wav_file.read()
        base64_string = base64.b64encode(binary_data).decode('utf-8')
    return base64_string

def string_to_flac(base64_string, output_filename, target_sr=16000):
    """Decode a base64 string, resample the audio if necessary, and save as FLAC."""
    decoded_data = base64.b64decode(base64_string)
    wav_buffer = io.BytesIO(decoded_data)
    # sf.read will automatically detect sample rate from the header
    audio, orig_sr = sf.read(wav_buffer)
    if orig_sr != target_sr:
        audio = librosa.resample(audio, orig_sr, target_sr)
    sf.write(output_filename, audio, target_sr, format='FLAC')

def whisper_inference(model_size, audio_type):
    """Load a Whisper model, transcribe the audio, and return the transcript.
       (Assumes that Whisper saves two WAV files:
         - natural: SAVE_DIR + "audio_input" + AUDIO_TYPE_NAT + ".wav"
         - adversarial: SAVE_DIR + "audio_input" + AUDIO_TYPE_ADV + ".wav"
       and that model.transcribe() returns the transcript from the original audio.)
    """
    # Assume the model transcribes the original file; adjust the filename as needed.
    # For example, if Whisper transcribes the FLAC file you saved and then writes its outputs as WAV:
    audio_path = SAVE_DIR + "audio_input.flac"
    global model
    result = model.transcribe(audio_path)
    return result["text"]

async def send_transcript(transcript):
    """Send the transcript to the Llama server via its websocket."""
    try:
        async with connect(LLAMA_WS_URL) as websocket:
            # You can prepend labels such as "adv:" and "nat:" if needed.
            # Here we send a combined message; adjust as necessary.
            await websocket.send(transcript)
            response = await websocket.recv()
            print("Transcript forwarded; response:", response)
    except Exception as e:
        print("Error sending transcript to Llama server:", e)

async def echo(websocket):
    async for base64_string in websocket:
        try:
            print("DECODING INCOMING AUDIO")
            # Here base64_string is expected to contain the binary data for one audio file.
            # Convert incoming audio to a FLAC file at 16kHz.
            flac_path = SAVE_DIR + "audio_input.flac"
            string_to_flac(base64_string, flac_path, target_sr=16000)
            print("Saved FLAC file at:", flac_path)

            # Run Whisper inference on the saved FLAC file.
            transcript = whisper_inference(MODEL_SIZE, AUDIO_TYPE_NAT)
            print("Transcript:", transcript)

            # Assuming that Whisper (or your attack procedure) saves two WAV files:
            nat_wav_path = SAVE_DIR + "audio_input" + AUDIO_TYPE_NAT + ".wav"
            adv_wav_path = SAVE_DIR + "audio_input" + AUDIO_TYPE_ADV + ".wav"

            # Convert both WAV files to base64 strings.
            nat_wav_b64 = wav_to_string(nat_wav_path)
            adv_wav_b64 = wav_to_string(adv_wav_path)

            # Concatenate the data into one string.
            # For example, you might use a delimiter such as "|" to separate parts.
            returns = f"adv:{adv_wav_b64}|nat:{nat_wav_b64}|transcript:{transcript}"
            print("Sending response back to client.")
            await websocket.send(returns)

            await send_transcript(transcript)
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(error_msg)
            await websocket.send(error_msg)

async def main():
    global model
    model = whisper.load_model(model_size)
    async with serve(echo, "localhost", 8765):
        await asyncio.Future() 

# Run the WebSocket server
asyncio.run(main())
