import whisper

model = whisper.load_model("base")

result = model.transcribe("sample.m4a", language="en")

print("Transcript:")
print(result["text"])
