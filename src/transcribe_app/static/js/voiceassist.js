// ------------------------------
// ELEMENT REFERENCES
// ------------------------------
const recBtn = document.getElementById('recBtn');
const stopBtn = document.getElementById('stopBtn');
const status = document.getElementById('status');
const out = document.getElementById('transcript');
const langSel = document.getElementById('lang');
const historyList = document.getElementById('historyList');
const downloadBtn = document.getElementById('downloadBtn');

// Modal Elements
const loginModal = document.getElementById("loginModal");
const logoutModal = document.getElementById("logoutModal");

const loginForm = document.getElementById("loginForm");
const loginError = document.getElementById("loginError");

const closeLoginBtn = document.getElementById("closeLogin");
const confirmLogoutBtn = document.getElementById("confirmLogout");
const cancelLogoutBtn = document.getElementById("cancelLogout");

const loginBtn = document.getElementById("loginBtn");
const logoutBtn = document.getElementById("logoutBtn");

// ------------------------------
// CSRF TOKEN HANDLER
// ------------------------------
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie) {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = cookie.slice(name.length + 1);
                break;
            }
        }
    }
    return cookieValue;
}
const csrftoken = getCookie("csrftoken");

// ------------------------------
// STATUS HANDLER
// ------------------------------
function setStatus(t){ status.textContent = t || ""; }

// Escape HTML
function esc(s) {
    return String(s || "")
        .replace(/&/g,"&amp;")
        .replace(/</g,"&lt;")
        .replace(/>/g,"&gt;");
}

// ------------------------------
// HISTORY LOADING
// ------------------------------
async function loadHistory() {
    historyList.innerHTML = "Loading...";
    const resp = await fetch("/history/");
    const items = await resp.json();

    historyList.innerHTML = "";
    items.forEach(t => {
        const div = document.createElement("div");
        div.className = "history-item";

        div.innerHTML = `
            <strong>${esc(t.filename)}</strong><br>
            <span class="small">${esc(t.created_at.slice(0,16))}</span>
        `;

        div.onclick = () => {
            out.textContent = t.transcript || "[empty]";
            lastTranscriptId = t.id;
            downloadBtn.disabled = false;
        };

        historyList.appendChild(div);
    });
}

// ------------------------------
// DOWNLOAD
// ------------------------------
downloadBtn.onclick = () => {
    if (lastTranscriptId)
        window.location = `/download/${lastTranscriptId}/`;
};

// ------------------------------
// RECORDING
// ------------------------------
let mediaRecorder = null;
let chunks = [];
let lastTranscriptId = null;

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

        const resp = await fetch("/upload-audio/", { 
            method:"POST", 
            headers: { "X-CSRFToken": csrftoken },
            body:form 
        });

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

stopBtn.onclick = () => {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        mediaRecorder.stop();
    }
    recBtn.disabled = false;
    stopBtn.disabled = true;
    setStatus("");
};

loadHistory();

// ------------------------------
// LOGIN MODAL
// ------------------------------
loginBtn?.addEventListener("click", () => {
    loginModal.style.display = "flex";
});

closeLoginBtn?.addEventListener("click", () => {
    loginModal.style.display = "none";
});

// LOGIN (AJAX)
loginForm?.addEventListener("submit", async (e) => {
    e.preventDefault();

    const username = document.getElementById("loginUsername").value;
    const password = document.getElementById("loginPassword").value;

    const resp = await fetch("/auth/login/", {
        method: "POST",
        headers: {
            "X-CSRFToken": csrftoken,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: `username=${username}&password=${password}`
    });

    if (resp.redirected || resp.status === 200) {
        location.reload();
    } else {
        loginError.textContent = "Invalid username or password.";
        loginError.style.display = "block";
    }
});

// ------------------------------
// LOGOUT MODAL
// ------------------------------
logoutBtn?.addEventListener("click", () => {
    logoutModal.style.display = "flex";
});

cancelLogoutBtn?.addEventListener("click", () => {
    logoutModal.style.display = "none";
});

confirmLogoutBtn?.addEventListener("click", async () => {
    const resp = await fetch("/auth/logout/", {
        method: "POST",
        headers: { "X-CSRFToken": csrftoken }
    });
    location.reload();
});
