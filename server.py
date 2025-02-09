import streamlit as st
import base64
import io
import asyncio
from websockets import connect
from websockets.asyncio.server import serve
import os
import librosa
import soundfile as sf
import shutil
import whisper

# Global configuration:
MODEL_SIZE = "tiny"        # or "medium", "large", etc.
AUDIO_TYPE_ADV = "adv"
AUDIO_TYPE_NAT = "nat"
SAVE_DIR = f"/workspace/pythonny/attacks/cw/whisper-{MODEL_SIZE}/2000/save/"
CSV_PATH = "ServerCode/data/LibriSpeech/csv/test-clean-20.csv"

def string_to_flac(base64_string, output_filename, target_sr=16000):
    """
    Decode a base64 string, resample the audio to target_sr (if needed), and save as a FLAC file.
    """
    decoded_data = base64.b64decode(base64_string)
    wav_buffer = io.BytesIO(decoded_data)
    # Read audio and detect its original sampling rate.
    audio, orig_sr = sf.read(wav_buffer)
    if orig_sr != target_sr:
        audio = librosa.resample(audio, orig_sr, target_sr)
    sf.write(output_filename, audio, target_sr, format='FLAC')

def wav_to_string(file_path):
    """Read a WAV file and return its base64 string."""
    with open(file_path, "rb") as wav_file:
        binary_data = wav_file.read()
        return base64.b64encode(binary_data).decode('utf-8')

def update_csv(csv_path, file_id, duration, wav_abs_path, spk_id, transcript):
    """
    Replace the first two lines of the CSV file with a header and a new record.
    The record format is: ID,duration,wav,spk_id,wrd
    """
    header = "ID,duration,wav,spk_id,wrd\n"
    data_row = f"{file_id},{duration:.2f},{wav_abs_path},{spk_id},{transcript}\n"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write(header)
        f.write(data_row)

def whisper_inference(model_size, audio_type):
    """
    Run Whisper inference on the saved FLAC file and return the natural transcript.
    Assumes that the FLAC file is saved as SAVE_DIR + "audio_input.flac".
    """
    audio_path = SAVE_DIR + "audio_input.flac"
    global model
    result = model.transcribe(audio_path)
    return result["text"]

async def send_transcript(transcript):
    """
    (Optional) Forward the transcript to another websocket server (e.g., Llama server).
    Here we just print it.
    """
    print("Transcript to forward:", transcript)
    # Implement further logic here if needed.
    # For example, you could connect to another websocket and send the transcript.
    # async with connect("ws://localhost:9000") as websocket:
    #     await websocket.send(transcript)
    #     response = await websocket.recv()
    #     print("Llama server responded:", response)

async def echo(websocket):
    async for base64_string in websocket:
        try:
            print("DECODING INCOMING AUDIO")
            # Save the incoming audio (in base64) as a FLAC file at 16kHz.
            flac_path = SAVE_DIR + "audio_input.flac"
            string_to_flac(base64_string, flac_path, target_sr=16000)
            print("Saved FLAC file at:", flac_path)
            
            # Run Whisper inference to get the natural transcription.
            transcript = whisper_inference(MODEL_SIZE, AUDIO_TYPE_NAT)
            print("Transcript:", transcript)
            
            # Assuming that your Whisper (or attack pipeline) saves two WAV files:
            # - Natural audio: SAVE_DIR + "audio_input" + AUDIO_TYPE_NAT + ".wav"
            # - Adversarial audio: SAVE_DIR + "audio_input" + AUDIO_TYPE_ADV + ".wav"
            nat_wav_path = SAVE_DIR + "audio_input" + AUDIO_TYPE_NAT + ".wav"
            adv_wav_path = SAVE_DIR + "audio_input" + AUDIO_TYPE_ADV + ".wav"
            
            nat_wav_b64 = wav_to_string(nat_wav_path)
            adv_wav_b64 = wav_to_string(adv_wav_path)
            
            # Derive file_id and spk_id from the filename.
            file_id = os.path.basename(flac_path).replace('.flac', '')
            spk_id = file_id  # Assuming spk_id is the same as file_id
            
            # Define the absolute path where the file should reside in LibriSpeech.
            wav_abs_path = f"/workspace/pythonny/data/LibriSpeech/{file_id}.flac"
            # Copy the FLAC file (created above) to the target LibriSpeech directory.
            shutil.copy(flac_path, wav_abs_path)
            
            # Get the duration (in seconds) of the copied file using librosa.
            duration = librosa.get_duration(path=wav_abs_path)
            
            update_csv(CSV_PATH, file_id, duration, wav_abs_path, spk_id, transcript)
            print("CSV updated at:", CSV_PATH)
            
            # Build the response string.
            returns = f"adv:{adv_wav_b64}|nat:{nat_wav_b64}|transcript:{transcript}"
            print("Sending response back to client.")
            await websocket.send(returns)
            
            # Optionally, forward the transcript to another server.
            await send_transcript(transcript)
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(error_msg)
            await websocket.send(error_msg)

async def main():
    global model
    model = whisper.load_model(MODEL_SIZE)
    async with serve(echo, "localhost", 8765):
        await asyncio.Future()  # run forever

# Run the WebSocket server
asyncio.run(main())
