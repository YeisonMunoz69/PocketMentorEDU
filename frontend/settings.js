// ── Variables & DOM ──
const slNctx = document.getElementById('sl-nctx');
const slGpu = document.getElementById('sl-gpu');
const slThr = document.getElementById('sl-thr');
const btnApplyHw = document.getElementById('btn-apply-hw');

// UI Live Updates (Hardware)
if(slNctx) slNctx.addEventListener('input', e => document.getElementById('val-nctx').innerText = e.target.value);
if(slGpu) slGpu.addEventListener('input', e => document.getElementById('val-gpu').innerText = e.target.value);
if(slThr) slThr.addEventListener('input', e => document.getElementById('val-thr').innerText = e.target.value);

// ── Parámetros LLM & RAG (Local Storage / USB) ──
const pTemp = document.getElementById('sl-temp');
const pMaxtok = document.getElementById('sl-maxtok');
const pTopp = document.getElementById('sl-topp');
const pRep = document.getElementById('sl-rep');
const pTopk = document.getElementById('sl-topk');
const pEval = document.getElementById('sel-eval');

// Toggle animado Neumórfico RAG Retry
const pRetryTrack = document.getElementById('chk-retry-track');
let isRetryEnabled = true;

function saveConfigs() {
    const payload = {};
    if(pTemp) { localStorage.setItem('pme_temp', pTemp.value); payload.temp = parseFloat(pTemp.value); }
    if(pMaxtok) { localStorage.setItem('pme_maxtok', pMaxtok.value); payload.max_tokens = parseInt(pMaxtok.value); }
    if(pTopp) { localStorage.setItem('pme_topp', pTopp.value); payload.top_p = parseFloat(pTopp.value); }
    if(pRep) { localStorage.setItem('pme_rep', pRep.value); payload.repeat_penalty = parseFloat(pRep.value); }
    if(pTopk) { localStorage.setItem('pme_topk', pTopk.value); payload.top_k_rag = parseInt(pTopk.value); }
    if(pEval) { localStorage.setItem('pme_eval', pEval.value); payload.eval_mode = pEval.value; }
    
    localStorage.setItem('pme_retry', isRetryEnabled ? '1' : '0');
    payload.auto_retry = isRetryEnabled;
    payload.theme = localStorage.getItem('pme_theme') || 'purple';
    payload.bg_theme = localStorage.getItem('pme_bg') || 'default';

    // Persistir en USB via API
    fetch('/api/settings', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload)
    }).catch(e => console.error("Error guardando settings:", e));
}

function loadConfigs() {
    if(pTemp && localStorage.getItem('pme_temp')) pTemp.value = localStorage.getItem('pme_temp');
    if(pMaxtok && localStorage.getItem('pme_maxtok')) pMaxtok.value = localStorage.getItem('pme_maxtok');
    if(pTopp && localStorage.getItem('pme_topp')) pTopp.value = localStorage.getItem('pme_topp');
    if(pRep && localStorage.getItem('pme_rep')) pRep.value = localStorage.getItem('pme_rep');
    if(pTopk && localStorage.getItem('pme_topk')) pTopk.value = localStorage.getItem('pme_topk');
    if(pEval && localStorage.getItem('pme_eval')) pEval.value = localStorage.getItem('pme_eval');
    
    if(localStorage.getItem('pme_retry')) {
        isRetryEnabled = localStorage.getItem('pme_retry') === '1';
        if(pRetryTrack) {
            if(isRetryEnabled) pRetryTrack.classList.add('active');
            else pRetryTrack.classList.remove('active');
        }
    }

    // Update val labels
    if(pTemp) document.getElementById('val-temp').innerText = pTemp.value;
    if(pMaxtok) document.getElementById('val-maxtok').innerText = pMaxtok.value;
    if(pTopp) document.getElementById('val-topp').innerText = pTopp.value;
    if(pRep) document.getElementById('val-rep').innerText = pRep.value;
    if(pTopk) document.getElementById('val-topk').innerText = pTopk.value;
}

[pTemp, pMaxtok, pTopp, pRep, pTopk].forEach(el => {
    if(el) {
        el.addEventListener('input', e => {
            const idMap = {'sl-temp':'val-temp', 'sl-maxtok':'val-maxtok', 'sl-topp':'val-topp', 'sl-rep':'val-rep', 'sl-topk':'val-topk'};
            document.getElementById(idMap[e.target.id]).innerText = e.target.value;
            saveConfigs();
        });
    }
});
if(pEval) pEval.addEventListener('change', saveConfigs);

if(pRetryTrack) {
    pRetryTrack.addEventListener('click', () => {
        // Toggle the visual state handled by HTML inline onclick natively, but we update our logic
        isRetryEnabled = pRetryTrack.classList.contains('active'); 
        saveConfigs();
    });
}

// ── Tema Visual Dinámico (Acento) ──
const themeSelector = document.getElementById('theme-selector');
if (themeSelector) {
    const swatches = themeSelector.querySelectorAll('.theme-swatch');
    swatches.forEach(sw => {
        if(sw.dataset.theme === (localStorage.getItem('pme_theme') || 'purple')) {
            sw.classList.add('active');
        }
        sw.addEventListener('click', () => {
            swatches.forEach(s => s.classList.remove('active'));
            sw.classList.add('active');
            
            const selectedTheme = sw.dataset.theme;
            localStorage.setItem('pme_theme', selectedTheme);
            
            const currentBg = localStorage.getItem('pme_bg') || 'default';
            document.body.className = `layout theme-${selectedTheme} bg-${currentBg}`;
            saveConfigs(); // Guarda a la USB
            showToast('Tema visual actualizado', 'success');
        });
    });
}

// ── Tema de Fondo Dinámico ──
const bgSelector = document.getElementById('bg-selector');
if (bgSelector) {
    const bgSwatches = bgSelector.querySelectorAll('.bg-swatch');
    bgSwatches.forEach(sw => {
        if(sw.dataset.bg === (localStorage.getItem('pme_bg') || 'default')) {
            sw.classList.add('active');
        }
        sw.addEventListener('click', () => {
            bgSwatches.forEach(s => s.classList.remove('active'));
            sw.classList.add('active');
            
            const selectedBg = sw.dataset.bg;
            localStorage.setItem('pme_bg', selectedBg);
            
            const currentTheme = localStorage.getItem('pme_theme') || 'purple';
            document.body.className = `layout theme-${currentTheme} bg-${selectedBg}`;
            saveConfigs(); // Guarda a la USB
            showToast('Fondo actualizado', 'success');
        });
    });
}

// ── Inicialización Global ──
window.addEventListener('DOMContentLoaded', async () => {
    // Sincronización transparente de settings desde la memoria USB (API)
    try {
        const res = await fetch('/api/settings');
        if(res.ok) {
            const data = await res.json();
            if(data.theme) localStorage.setItem('pme_theme', data.theme);
            if(data.bg_theme) localStorage.setItem('pme_bg', data.bg_theme);
            if(data.temp !== undefined) localStorage.setItem('pme_temp', data.temp);
            if(data.max_tokens !== undefined) localStorage.setItem('pme_maxtok', data.max_tokens);
            if(data.top_p !== undefined) localStorage.setItem('pme_topp', data.top_p);
            if(data.repeat_penalty !== undefined) localStorage.setItem('pme_rep', data.repeat_penalty);
            if(data.top_k_rag !== undefined) localStorage.setItem('pme_topk', data.top_k_rag);
            if(data.eval_mode) localStorage.setItem('pme_eval', data.eval_mode);
            if(data.auto_retry !== undefined) localStorage.setItem('pme_retry', data.auto_retry ? '1' : '0');
        }
    } catch(e) { }

    loadConfigs();
    
    // Aplicamos estilos persistentes
    const _savedTheme = localStorage.getItem('pme_theme') || 'purple';
    const _savedBg = localStorage.getItem('pme_bg') || 'default';
    document.body.className = `layout theme-${_savedTheme} bg-${_savedBg}`;
    
    // Sincroniza swatches 
    if(themeSelector) {
        themeSelector.querySelectorAll('.theme-swatch').forEach(s => {
            s.classList.toggle('active', s.dataset.theme === _savedTheme);
        });
    }
    if(bgSelector) {
        bgSelector.querySelectorAll('.bg-swatch').forEach(s => {
            s.classList.toggle('active', s.dataset.bg === _savedBg);
        });
    }
});


// ── Toasts Neumórficos (Android Style) ──
let toastTimeout;
function showToast(message, type="info") {
    const toast = document.getElementById('toast-container');
    const toastMsg = document.getElementById('toast-msg-text');
    const toastIcon = toast.querySelector('.toast-icon');
    
    // Config icon and colors logic
    toast.className = `toast-container neu-convex toast-${type}`;
    if (type === 'success') {
        toastIcon.innerHTML = `<polyline points="20 6 9 17 4 12"></polyline>`;
    } else if (type === 'error') {
        toastIcon.innerHTML = `<line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line>`;
    } else {
        toastIcon.innerHTML = `<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline>`;
    }
    
    toastMsg.innerText = message;
    toast.classList.add('active');
    
    clearTimeout(toastTimeout);
    toastTimeout = setTimeout(() => {
        toast.classList.remove('active');
    }, 4000);
}

// ── Diálogo Sistema (Modales) ──
const systemDialog = document.getElementById('systemDialog');
const dialogCancelBtn = document.getElementById('dialogCancelBtn');
const dialogAcceptBtn = document.getElementById('dialogAcceptBtn');
let currentDialogConfirmCallback = null;

function openDialog(title, message, confirmCallback) {
    document.getElementById('dialog-title').innerText = title;
    document.getElementById('dialog-message').innerText = message;
    currentDialogConfirmCallback = confirmCallback;
    systemDialog.classList.add('active');
}

if(dialogCancelBtn) {
    dialogCancelBtn.addEventListener('click', () => {
        systemDialog.classList.remove('active');
        currentDialogConfirmCallback = null;
    });
}

if(dialogAcceptBtn) {
    dialogAcceptBtn.addEventListener('click', () => {
        systemDialog.classList.remove('active');
        if(currentDialogConfirmCallback) {
            currentDialogConfirmCallback();
            currentDialogConfirmCallback = null;
        }
    });
}

// ── Lógica de Hardware Apply ──
async function applyHardwareChanges() {
    const payload = {
        n_ctx: parseInt(slNctx.value),
        gpu_layers: parseInt(slGpu.value),
        cpu_threads: parseInt(slThr.value)
    };
    
    btnApplyHw.disabled = true;
    const oldHtml = btnApplyHw.innerHTML;
    btnApplyHw.innerHTML = "Recargando. Espera...";
    
    try {
        const res = await fetch('/api/hardware/reload', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        if (res.ok) {
            showToast(`Modelo recargado exitosamente.`, "success");
        } else {
            showToast("Fallo al recargar modelo de IA", "error");
        }
    } catch(err) {
        showToast("Error interno del servidor local", "error");
    } finally {
        btnApplyHw.disabled = false;
        btnApplyHw.innerHTML = oldHtml;
    }
}

if(btnApplyHw) {
    btnApplyHw.addEventListener('click', () => {
        openDialog('Aplicar Cambios', 'El modelo se recargará de memoria para aplicar tu configuración de hardware. ¿Proceder?', applyHardwareChanges);
    });
}

const btnResetHw = document.getElementById('btn-reset-hw');
if(btnResetHw) {
    btnResetHw.addEventListener('click', () => {
        if(slGpu) {
            slGpu.value = 99;
            document.getElementById('val-gpu').innerText = "99";
            showToast("GPU Máxima seleccionada. Presiona 'Aplicar Hardware'.", "info");
        }
    });
}

// ── RAG File Upload Logic ──
const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-upload');

function handleFiles(files) {
    if (files.length === 0) return;
    
    const formData = new FormData();
    for (let f of files) {
        formData.append('files', f);
    }
    
    // Animate dropZone
    dropZone.classList.add('neu-concave');
    showToast("Subiendo e indexando... (Un momento)", "info");
    
    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'ok') {
            showToast("Documentos listos en la Base de Conocimientos", "success");
        } else {
            showToast("Error al indexar documentos", "error");
        }
    })
    .catch(err => {
        showToast("Error de conexión al subir", "error");
    })
    .finally(() => {
        dropZone.classList.remove('neu-concave');
        if(fileInput) fileInput.value = ''; 
    });
}

if(fileInput) {
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });
}

if(dropZone) {
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.opacity = "0.7";
    });

    dropZone.addEventListener('dragleave', (e) => {
        e.preventDefault();
        dropZone.style.opacity = "1";
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.style.opacity = "1";
        handleFiles(e.dataTransfer.files);
    });
}
