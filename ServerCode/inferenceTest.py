import whisper

print("loading model")
model = whisper.load_model("medium")

audio_path = "/workspace/pythonny/attacks/cw/whisper-medium/2000/save/8455-210777-0044_nat.wav"
print(f"transcribing: {audio_path}")
result = model.transcribe(audio_path)
print("result:")
print(result["text"])