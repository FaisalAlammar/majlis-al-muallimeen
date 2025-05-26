
## Requirements

- **Python 3.10.x** (do NOT use Python 3.13+)
- All dependencies listed in requirements.txt

## Setup Instructions

1. Make sure you have Python 3.10 installed.
    - You can download it from [python.org/downloads](https://www.python.org/downloads/release/python-3100/)
    - To check your Python version, run:
      ```
      python --version
      ```
      or
      ```
      py --version
      ```
      You should see something like: `Python 3.10.11`
2. (Optional) Create a virtual environment:
    ```
    python -m venv venv
    ```
    Then activate it:
    - On Windows: `venv\Scripts\activate`
    - On macOS/Linux: `source venv/bin/activate`
3. Install dependencies:
    ```
    pip install -r requirements.txt
    ```

## Notes

- **This project is not guaranteed to work on Python 3.11+ or 3.13+**.
- If you get errors about missing packages or incompatibility, check your Python version!



# 🏫 Teachers’ Majlis

**An interactive AI-powered platform for asking educational questions and getting instant answers in Arabic, with support for both text and audio.**

---

## 📖 Project Description

Teachers’ Majlis is a smart web application that allows users to ask educational questions and receive instant, specialized answers powered by AI.  
Key features include:
- Text or voice (speech-to-text) question input.
- Answer retrieval using a vector database (FAISS).
- Conversational memory for each chat session.
- Text-to-speech answer generation (with a button to play the answer in the chat).
- PDF export for the chat conversation.
- Modern, responsive UI for all devices.

---

## 🚀 Getting Started

1. **Install Requirements:**
   ```bash
   pip install -r requirements.txt
