const recBtn = document.getElementById('recBtn');
const stopBtn = document.getElementById('stopBtn');
const status = document.getElementById('status');
const out = document.getElementById('transcript');
const langSel = document.getElementById('lang');
const historyList = document.getElementById('historyList');
const downloadBtn = document.getElementById('downloadBtn');

let mediaRecorder = null, chunks = [];
let lastTranscriptId = null;

function setStatus(t){ status.textContent = t || ""; }

// Escape HTML
function esc(s) {
    return String(s || "")
        .replace(/&/g,"&amp;")
        .replace(/</g,"&lt;")
        .replace(/>/g,"&gt;");
}

// Load history
async function loadHistory() {
    historyList.innerHTML = "Loading...";
    const resp = await fetch("/history/");
    const items = await resp.json();

    historyList.innerHTML = "";
    items.forEach(t => {
        const div = document.createElement("div");
        div.className = "history-item";

        div.innerHTML = `<strong>${esc(t.filename)}</strong><br>
                         <span class="small">${esc(t.created_at.slice(0,16))}</span>`;

        div.onclick = () => {
            out.textContent = t.transcript || "[empty]";
            lastTranscriptId = t.id;
            downloadBtn.disabled = false;
        };
        historyList.appendChild(div);
    });
}

// Download
downloadBtn.onclick = () => {
    if (lastTranscriptId)
        window.location = `/download/${lastTranscriptId}/`;
};

// Start recording
recBtn.onclick = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio:true });
    mediaRecorder = new MediaRecorder(stream);
    chunks = [];

    mediaRecorder.ondataavailable = e => chunks.push(e.data);

    mediaRecorder.onstop = async () => {
        const blob = new Blob(chunks, { type:"audio/webm" });

        const form = new FormData();
        form.append("audio", blob, "recording.webm");
        form.append("language", langSel.value);

        setStatus("Uploading...");
        const resp = await fetch("/upload-audio/", { method:"POST", body:form });
        const data = await resp.json();

        out.textContent = data.transcript || "[No transcript]";
        lastTranscriptId = data.id;
        downloadBtn.disabled = false;

        setStatus("");
        loadHistory();
    };

    mediaRecorder.start();
    setStatus("Recording...");
    recBtn.disabled = true;
    stopBtn.disabled = false;
};

// Stop recording
stopBtn.onclick = () => {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
    }
    recBtn.disabled = false;
    stopBtn.disabled = true;
    setStatus("");
};

loadHistory();
