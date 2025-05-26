from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import Ollama
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

import whisper
import tempfile
import os
from concurrent.futures import ThreadPoolExecutor
import asyncio
import aiofiles
from uuid import uuid4
from typing import Dict, List
import time

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/distiluse-base-multilingual-cased-v1"
)
db = FAISS.load_local(
    "subjects_faiss_db",
    embedding_model,
    allow_dangerous_deserialization=True
)
retriever = db.as_retriever()

llm = Ollama(
    model="command-r7b-arabic",
    temperature=0.3,
    num_ctx=2048,
    num_thread=4
)

conversation_memories: Dict[str, ConversationBufferMemory] = {}
chat_histories: Dict[str, List[Dict]] = {}
executor = ThreadPoolExecutor(max_workers=2)

def get_memory(conversation_id: str) -> ConversationBufferMemory:
    if conversation_id not in conversation_memories:
        conversation_memories[conversation_id] = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            output_key='answer'
        )
    return conversation_memories[conversation_id]

@app.on_event("startup")
async def startup_event():
    # تنظيف ملفات الصوت المؤقتة عند بدء التشغيل
    temp_dir = tempfile.gettempdir()
    for filename in os.listdir(temp_dir):
        if filename.endswith(".wav"):
            try:
                os.remove(os.path.join(temp_dir, filename))
            except Exception:
                pass

@app.on_event("shutdown")
def shutdown_event():
    executor.shutdown()

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

async def process_question(question: str, conversation_id: str) -> Dict:
    memory = get_memory(conversation_id)
    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        return_source_documents=False
    )
    loop = asyncio.get_event_loop()
    retrieved_docs = await loop.run_in_executor(
        executor,
        lambda: retriever.get_relevant_documents(question)
    )
    top_doc = retrieved_docs[0] if retrieved_docs else None
    subject = top_doc.metadata.get("subject", "المعلم") if top_doc else "المعلم"
    result = await loop.run_in_executor(
        executor,
        lambda: qa_chain({"question": question})
    )
    answer = result["answer"]
    response = f"{subject} يرد:\n{answer}"
    if conversation_id not in chat_histories:
        chat_histories[conversation_id] = []
    chat_histories[conversation_id].append({
        "question": question,
        "answer": response
    })
    return {"answer": response, "conversation_id": conversation_id}

@app.post("/ask")
async def ask_question(request: Request, question: str = Form(...)):
    conversation_id = request.headers.get("X-Conversation-ID", str(uuid4()))
    try:
        result = await process_question(question, conversation_id)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/record")
async def record_voice(request: Request, audio: UploadFile = File(...)):
    conversation_id = request.headers.get("X-Conversation-ID", str(uuid4()))
    try:
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, audio.filename)
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await audio.read()
            await out_file.write(content)
        loop = asyncio.get_event_loop()
        model = whisper.load_model("small")
        result = await loop.run_in_executor(
            executor,
            lambda: model.transcribe(file_path, language="ar")
        )
        transcript = result["text"].strip()
        if not transcript:
            return JSONResponse({"error": "لم يتم التعرف على كلام"}, status_code=400)
        # استخدم نفس دالة معالجة السؤال النصي
        qa_result = await process_question(transcript, conversation_id)
        qa_result["transcript"] = transcript
        # حذف الملف المؤقت
        try:
            os.remove(file_path)
        except Exception:
            pass
        return JSONResponse(qa_result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/history")
async def get_history(request: Request):
    conversation_id = request.headers.get("X-Conversation-ID")
    if not conversation_id or conversation_id not in chat_histories:
        return JSONResponse({"history": []})
    return JSONResponse({"history": chat_histories[conversation_id]})

@app.post("/reset")
async def reset_chat(request: Request):
    conversation_id = request.headers.get("X-Conversation-ID")
    if conversation_id in conversation_memories:
        del conversation_memories[conversation_id]
    if conversation_id in chat_histories:
        del chat_histories[conversation_id]
    return JSONResponse({"status": "تم مسح المحادثة والتخزين المؤقت"})
