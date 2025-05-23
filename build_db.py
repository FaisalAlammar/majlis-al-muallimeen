from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter

subject_files = [
    ("معلم الفيزياء", "book-alfizya-1.pdf"),
    ("معلم الكيمياء", "book-kimya2-1.pdf"),
    ("معلم الأحياء", "book-alahya-1.pdf"),
]

all_chunks = []

for subject, pdf_path in subject_files:
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()
    for doc in documents:
        doc.metadata["subject"] = subject
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(documents)
    for chunk in chunks:
        chunk.metadata["subject"] = subject
    all_chunks.extend(chunks)

embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/distiluse-base-multilingual-cased-v1")
db = FAISS.from_documents(all_chunks, embedding_model)
# Save the FAISS database (it creates two files: index and metadata)
db.save_local("subjects_faiss_db")

print("Vector DB built and saved to ./subjects_faiss_db")
