// تخزين معرف المحادثة
let conversationId = localStorage.getItem('conversationId') || Date.now().toString();
localStorage.setItem('conversationId', conversationId);

// Loader
function showLoader() {
  const box = document.getElementById("chat-box");
  let loader = document.createElement("div");
  loader.className = "message teacher";
  loader.id = "loader-message";
  loader.innerHTML = '<span class="loader"></span> جاري المعالجة ...';
  box.appendChild(loader);
  box.scrollTop = box.scrollHeight;
}
function removeLoader() {
  let loader = document.getElementById("loader-message");
  if (loader) loader.remove();
}

// إرسال الأسئلة النصية
document.getElementById("chat-form").addEventListener("submit", async function(e) {
  e.preventDefault();
  const input = document.getElementById("question");
  const question = input.value.trim();
  if (!question) return;

  addToChat("أنت", question);
  input.value = "";

  showLoader();
  const response = await fetch("/ask", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-Conversation-ID": conversationId
    },
    body: `question=${encodeURIComponent(question)}`
  });
  const data = await response.json();
  removeLoader();
  if (data.error) {
    addToChat("المعلم", "حدث خطأ: " + data.error);
  } else {
    addToChat("المعلم", data.answer);
  }
});

// تسجيل الصوت
document.getElementById("voice-btn").addEventListener("click", async function() {
  const button = this;
  button.disabled = true;
  button.textContent = "● التسجيل...";
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRecorder = new MediaRecorder(stream);
    const audioChunks = [];
    mediaRecorder.ondataavailable = (event) => audioChunks.push(event.data);
    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.wav");

      showLoader();
      const response = await fetch("/record", {
        method: "POST",
        headers: {
          "X-Conversation-ID": conversationId
        },
        body: formData
      });
      const data = await response.json();
      removeLoader();

      if (data.transcript) addToChat("أنت", data.transcript);
      if (data.error) {
        addToChat("المعلم", "حدث خطأ: " + data.error);
      } else {
        addToChat("المعلم", data.answer);
      }
    };
    mediaRecorder.start();
    setTimeout(() => mediaRecorder.stop(), 5000); // تسجيل لمدة 5 ثواني
  } catch (error) {
    console.error("Error:", error);
    alert("خطأ في التسجيل!");
  } finally {
    button.disabled = false;
    button.textContent = "🎤";
  }
});

// إعادة التعيين
document.getElementById("reset-btn").addEventListener("click", async function() {
  conversationId = Date.now().toString();  // إنشاء معرف جديد
  localStorage.setItem('conversationId', conversationId);

  await fetch("/reset", {
    method: "POST",
    headers: {
      "X-Conversation-ID": conversationId
    }
  });
  document.getElementById("chat-box").innerHTML = "";
});

// دالة مساعدة لعرض الرسائل
function addToChat(sender, message) {
  const box = document.getElementById("chat-box");
  const msg = document.createElement("div");
  msg.className = sender === "أنت" ? "message user" : "message teacher";
  msg.textContent = message;
  box.appendChild(msg);
  box.scrollTop = box.scrollHeight;
}


document.getElementById("download-btn").addEventListener("click", async () => {
    try {
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF({ orientation: 'p', unit: 'pt', format: 'a4' });

        doc.setFontSize(20);
        doc.text("سجل المحادثة - مجلس المعلمين", 300, 40, { align: 'center' });

        const chatBox = document.getElementById("chat-box");
        const messages = chatBox.querySelectorAll('.message');
        let yPosition = 70;
        doc.setFontSize(12);

        messages.forEach(msg => {
            const sender = msg.classList.contains('user') ? "أنت" : "المعلم";
            const text = msg.textContent;
            // تقسيم النص الطويل لأسطر
            const lines = doc.splitTextToSize(`${sender}: ${text}`, 480);
            lines.forEach(line => {
                doc.text(line, 540, yPosition, { align: 'right' });
                yPosition += 18;
            });
            yPosition += 8;
            if (yPosition > 800) {
                doc.addPage();
                yPosition = 40;
            }
        });

        doc.save("محادثة_مجلس_المعلمين.pdf");
    } catch (error) {
        console.error("فشل التصدير:", error);
        alert("حدث خطأ أثناء تصدير المحادثة!");
    }
});
