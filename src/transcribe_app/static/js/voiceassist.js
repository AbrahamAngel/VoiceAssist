document.addEventListener("DOMContentLoaded", function () {

    const recBtn = document.getElementById('recBtn');
    const stopBtn = document.getElementById('stopBtn');
    const status = document.getElementById('status');
    const transcriptDiv = document.getElementById('transcript');
    const langSel = document.getElementById('lang');
    const historyList = document.getElementById('historyList');
    const downloadBtn = document.getElementById('downloadBtn');

    const riskAlert = document.getElementById("riskAlert");
    const instructionBox = document.getElementById("instructionBox");
    const dosagesSpan = document.getElementById("dosages");
    const durationsSpan = document.getElementById("durations");

    let mediaRecorder = null;
    let chunks = [];
    let lastTranscriptId = null;

    function setStatus(text) {
        status.textContent = text || "";
    }

    // ================= RECORDING =================
    recBtn.addEventListener("click", async () => {

        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        chunks = [];

        mediaRecorder.ondataavailable = e => chunks.push(e.data);

        mediaRecorder.onstop = async () => {

            const blob = new Blob(chunks, { type: "audio/webm" });

            const form = new FormData();
            form.append("audio", blob, "recording.webm");
            form.append("language", langSel.value);

            setStatus("Uploading...");

            const resp = await fetch("/upload-audio/", {
                method: "POST",
                body: form
            });

            const data = await resp.json();
            console.log("SERVER RESPONSE:", data);

            // === TRANSCRIPT ===
            transcriptDiv.textContent = data.transcript || "[No transcript]";
            lastTranscriptId = data.id;
            downloadBtn.disabled = false;

            // === RISK ALERT ===
            if (data.risk === true) {
                riskAlert.style.display = "block";
            } else {
                riskAlert.style.display = "none";
            }

            // === INSTRUCTION BOX ===
            if (data.instructions &&
                (data.instructions.dosages.length > 0 ||
                 data.instructions.durations.length > 0)) {

                instructionBox.style.display = "block";

                dosagesSpan.textContent =
                    data.instructions.dosages.length > 0
                        ? data.instructions.dosages.join(", ")
                        : "None";

                durationsSpan.textContent =
                    data.instructions.durations.length > 0
                        ? data.instructions.durations.join(", ")
                        : "None";

            } else {
                instructionBox.style.display = "none";
            }

            setStatus("");
            loadHistory();
        };

        mediaRecorder.start();
        recBtn.disabled = true;
        stopBtn.disabled = false;
        setStatus("Recording...");
    });

    stopBtn.addEventListener("click", () => {
        if (mediaRecorder && mediaRecorder.state !== "inactive") {
            mediaRecorder.stop();
        }
        recBtn.disabled = false;
        stopBtn.disabled = true;
    });

    // ================= DOWNLOAD =================
    downloadBtn.addEventListener("click", () => {
        if (lastTranscriptId) {
            window.location.href = `/download/${lastTranscriptId}/`;
        }
    });

    // ================= HISTORY =================
    async function loadHistory() {
        const resp = await fetch("/history/");
        const items = await resp.json();

        historyList.innerHTML = "";

        items.forEach(item => {
            const div = document.createElement("div");
            div.className = "history-item";

            div.innerHTML = `
                <strong>${item.filename}</strong><br>
                <span class="small">${item.created_at.slice(0,16)}</span>
            `;

            div.onclick = () => {
                transcriptDiv.textContent = item.transcript || "[empty]";
                riskAlert.style.display = "none";
                instructionBox.style.display = "none";
            };

            historyList.appendChild(div);
        });
    }

    loadHistory();
});