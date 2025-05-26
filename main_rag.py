from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
import whisper
import sounddevice as sd
import scipy.io.wavfile
import tempfile
import json
import os
import atexit

# عند الخروج، تحرير الذاكرة
def cleanup():
    global llm, qa, db
    del llm, qa, db

atexit.register(cleanup)

# Load the vector DB
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/distiluse-base-multilingual-cased-v1")
db = FAISS.load_local("subjects_faiss_db", embedding_model, allow_dangerous_deserialization=True)
retriever = db.as_retriever()

llm = Ollama(model="command-r7b-arabic")
qa = RetrievalQA.from_ain_type(llm=llm, retriever=retriever, chain_type="stuff")

print("How would you like to enter your question?")
print("1 - Typing")
print("2 - Voice recording")
choice = input("Choose (1 or 2): ").strip()

query = ""

if choice == "1":
    query = input("Type your question: ").strip()

elif choice == "2":
    duration = 5
    samplerate = 16000
    print("Recording for 5 seconds...")
    recording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1)
    sd.wait()

    wav_path = os.path.join(tempfile.gettempdir(), "audio.wav")
    scipy.io.wavfile.write(wav_path, samplerate, recording)
    print("Audio saved")

    model = whisper.load_model("base")
    result = model.transcribe(wav_path, language="ar")
    query = result["text"]
    print(f"Transcribed text: {query.strip()}")

else:
    print("Invalid choice. Please select 1 or 2.")
    exit()

print("\nGenerating answer...\n")

retrieved_docs = retriever.get_relevant_documents(query)
top_doc = retrieved_docs[0] if retrieved_docs else None
subject = top_doc.metadata.get("subject", "المعلم") if top_doc else "المعلم"

answer = qa.invoke(query)

# Print answer with the correct teacher
print("Answer:\n")
final_answer = f"{subject} يرد:\n{answer['result']}\n"
print(final_answer)

# Append the answer to the file (don't overwrite previous answers)
with open("output_result.txt", "a", encoding="utf-8") as f:  # "a" means append
    f.write(final_answer)
    f.write("\n" + "-"*40 + "\n")  # Add a separator for clarity

