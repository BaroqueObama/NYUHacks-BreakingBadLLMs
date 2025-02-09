import asyncio
from websockets.asyncio.server import serve

async def llama_handler(websocket, path):
    async for message in websocket:
        try:
            # Expected format: "adv:<adv_audio_b64>|nat:<nat_audio_b64>|transcript:<transcript_text>"
            print("Received message from client:")
            print(message)
            parts = message.split("|")
            transcript = None
            adv_audio = None
            nat_audio = None
            for part in parts:
                if part.startswith("transcript:"):
                    transcript = part[len("transcript:"):].strip()
                elif part.startswith("adv:"):
                    adv_audio = part[len("adv:"):].strip()
                elif part.startswith("nat:"):
                    nat_audio = part[len("nat:"):].strip()

            if transcript is None:
                raise ValueError("Transcript not found in the message.")

            # Process the transcript as needed (for example, call your Llama parser).
            print("Parsed Transcript:", transcript)
            # Optionally, if you want to further process the transcript with a ChatOpenAI or other model:
            # parsed_result = your_llama_processing_function(transcript)
            # For now, we simply echo back a confirmation message.
            response = f"Parsed transcript: {transcript}"
            await websocket.send(response)
        except Exception as e:
            error_msg = f"Error parsing message: {str(e)}"
            print(error_msg)
            await websocket.send(error_msg)

async def main():
    # Start a websocket server listening on localhost:9000
    async with serve(llama_handler, "localhost", 9000):
        print("Llama WebSocket server is running on ws://localhost:9000")
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())
