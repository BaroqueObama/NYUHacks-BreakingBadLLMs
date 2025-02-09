import streamlit as st
from openai import OpenAI
import base64
import io
import asyncio
from websockets.asyncio.server import serve
from websockets import connect
from langchain_openai import ChatOpenAI
import wave

def wav_to_string(file_path):
    # Open the .wav file in binary mode
    with open(file_path, "rb") as wav_file:
        # Read the binary data from the file
        binary_data = wav_file.read()
        
        # Encode the binary data as a base64 string
        base64_string = base64.b64encode(binary_data).decode('utf-8')
        
    return base64_string

        
async def echo(websocket):
    async for base64_string in websocket:
        try:
            # Decode the base64-encoded string
            print("DECODING STRING")
            binary_data = base64.b64decode(base64_string)
            print("Received binary data")

            w = wav_to_string("gpt2.wav")

            # Send back a simple response
            returns = "audio:" + w + "response:" + "received" # replace received later with the actual text
            print("CONCATENATED", returns[0:20])

            # need to transform this into a string 

            await websocket.send(returns)
        except Exception as e:
            await websocket.send(f"Error: {str(e)}")

async def main():
    async with serve(echo, "localhost", 8765):
        await asyncio.Future() 

# Run the WebSocket server
asyncio.run(main())
