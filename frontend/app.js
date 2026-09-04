// ── Variables & DOM ──
const chatContainer = document.getElementById('chat-messages');
const welcomeScreen = document.getElementById('welcome-screen');
const userInput = document.getElementById('user-input');
const btnSend = document.getElementById('btn-send');
const btnResetChat = document.getElementById('btn-reset-chat');

// Config options (Top Bar)
const selSubj = document.getElementById('sel-subj');
const selLevel = document.getElementById('sel-level');
const selMode = document.getElementById('sel-mode');
const inpUserid = document.getElementById('inp-userid');

// Iconos Reutilizables Offline (SVG)
const botIconSVG = `<svg viewBox="0 0 24 24" fill="none" class="icon" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:20px; height:20px; color:var(--accent-color);"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>`;
const userIconSVG = `<svg viewBox="0 0 24 24" fill="none" class="icon" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:20px; height:20px;"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>`;

// Funciones Globales para Toasts Neumórficos
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

// ── Global Sidebar Toggle & Persistencia ──
document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.getElementById('btn-toggle-sidebar');
    
    // Restaurar estado guardado
    if (localStorage.getItem('sidebar-collapsed') === 'true') {
        if(sidebar) sidebar.classList.add('collapsed');
    }

    if(toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebar-collapsed', isCollapsed);
        });
    }

    // Inicializar la pantalla de bienvenida (Saludo dinámico y Píldoras Carrousel)
    initWelcomeScreen();
});

// ── Dynamic Welcome Screen Data ──
const greetings = [
    "¡Hola {name}! ¿En qué te ayudo hoy?",
    "Saludos {name}, ¿qué aprenderemos hoy?",
    "Bienvenido {name}. ¿Sobre qué tema te gustaría hablar?",
    "¡Qué gusto verte {name}! Dime tu duda de inglés.",
    "Hola {name}. Estoy listo para ser tu tutor, ¿empezamos?",
    "Hey {name}, ¿con qué te puedo asistir hoy?",
    "Buen día {name}, ¡vamos a perfeccionar ese inglés!",
    "¿Listo para estudiar, {name}? ¿Por dónde comenzamos?",
    "Hola {name}, ¡no hay preguntas tontas aquí! Dime tu duda.",
    "¡Excelente día {name}! Estoy a tu disposición."
];

const topics = [
    "Diferencias Present Perfect vs Past Simple",
    "¿Cuándo usar In, On y At?",
    "Lista de 10 Phrasal Verbs súper útiles",
    "Pronunciar sonido 'TH' suave y fuerte",
    "Vocabulario de entrevista de trabajo",
    "Explicación del Primer Condicional",
    "Qué son los falsos amigos (False Friends)?",
    "Pedir comida en un restaurante en inglés",
    "Reglas de terminación -ED (Verbos Regulares)",
    "Vocabulario para viajar en Aeropuertos",
    "Uso correcto de Some y Any",
    "Diferencia entre verbos Make y Do",
    "Idioms o modismos en inglés con colores",
    "Cómo redactar un correo formal corto",
    "Segundo Condicional con ejemplos reales",
    "Uso de Much, Many, A lot of",
    "Tips veloces para mejorar el Listening",
    "Adjetivos avanzados en lugar de 'Very'",
    "Voz Pasiva: Su estructura y utilidades",
    "Vocabulario tech para desarrolladores",
    "El verbo modal Could y sus permisos",
    "Cuándo usar As y cuándo usar Like"
];

function initWelcomeScreen() {
    const greetingEl = document.getElementById('dynamic-greeting');
    const carouselEl = document.getElementById('suggestion-carousel');
    if(!greetingEl || !carouselEl) return;
    
    // Greeting
    const randomG = greetings[Math.floor(Math.random() * greetings.length)];
    const username = inpUserid && inpUserid.value.trim() ? inpUserid.value : 'Estudiante';
    
    if (randomG.includes("{name}")) {
        greetingEl.innerHTML = randomG.replace("{name}", `<span>${username}</span>`);
    } else {
        greetingEl.innerHTML = randomG;
    }

    // Carousel Items
    let shuffledTopics = [...topics].sort(() => 0.5 - Math.random()).slice(0, 20); // Pick 20
    carouselEl.innerHTML = '';
    
    shuffledTopics.forEach(top => {
        let div = document.createElement('div');
        div.className = 'topic-chip neu-convex';
        div.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:16px; height:16px; min-width:16px; color:var(--accent-color);"><polyline points="9 18 15 12 9 6"></polyline></svg> ${top}`;
        div.onclick = () => {
            userInput.value = top;
            userInput.style.height = 'auto';
            userInput.style.height = userInput.scrollHeight + 'px';
            userInput.focus();
            if(userInput.value.trim()) {
                btnSend.disabled = false;
                btnSend.classList.add('primary');
            }
        };
        carouselEl.appendChild(div);
    });

    // Auto-scroll logic
    if (window.currentAutoScrollInterval) {
        clearInterval(window.currentAutoScrollInterval);
    }
    
    let isPaused = false;
    const scrollStep = 1; // pixels per step
    const scrollInterval = 30; // ms per step
    const manualScrollAmt = 250;

    const startAutoScroll = () => {
        if(window.currentAutoScrollInterval) clearInterval(window.currentAutoScrollInterval);
        window.currentAutoScrollInterval = setInterval(() => {
            if(!isPaused && carouselEl) {
                carouselEl.scrollLeft += scrollStep;
                // Bounce back or reset behavior:
                // For a simple infinite feeling without complex cloning, we reset when we hit the end
                if(carouselEl.scrollLeft >= (carouselEl.scrollWidth - carouselEl.clientWidth - 1)) {
                    carouselEl.scrollLeft = 0; // Seamless snap back to start
                }
            }
        }, scrollInterval);
    };

    const stopAutoScroll = () => {
        if(window.currentAutoScrollInterval) clearInterval(window.currentAutoScrollInterval);
    };

    // Pause on interaction
    carouselEl.addEventListener('mouseenter', () => isPaused = true);
    carouselEl.addEventListener('mouseleave', () => isPaused = false);
    carouselEl.addEventListener('touchstart', () => isPaused = true, {passive: true});
    carouselEl.addEventListener('touchend', () => { setTimeout(() => isPaused = false, 1500); }, {passive: true}); 

    startAutoScroll();

    // Navigation Buttons (using onclick to avoid duplicate listeners on re-init)
    const btnPrev = document.getElementById('btn-prev-topic');
    const btnNext = document.getElementById('btn-next-topic');
    
    if(btnPrev) {
        btnPrev.onclick = () => {
            isPaused = true;
            carouselEl.scrollBy({ left: -manualScrollAmt, behavior: 'smooth' });
            setTimeout(() => isPaused = false, 2000); // Pause briefly after click
        };
    }
    
    if(btnNext) {
        btnNext.onclick = () => {
            isPaused = true;
            carouselEl.scrollBy({ left: manualScrollAmt, behavior: 'smooth' });
            setTimeout(() => isPaused = false, 2000);
        };
    }
}

if(inpUserid) {
    inpUserid.addEventListener('input', () => {
        const greetingEl = document.getElementById('dynamic-greeting');
        if(greetingEl && greetingEl.querySelector('span')) {
            greetingEl.querySelector('span').innerText = inpUserid.value.trim() || 'Estudiante';
        }
    });
}


// ── Diálogo Modal (Clear Chat) ──
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


// ── Polling: Monitor Memoria Sistema ──
async function updateSystemStats() {
    try {
        const res = await fetch('/api/system/stats');
        const data = await res.json();
        
        let memMB = (data.ram_usage_bytes / (1024 * 1024)).toFixed(0);
        let memPct = data.ram_percent || 0;
        
        const gbLabel = (memMB / 1024).toFixed(1);
        document.getElementById('sys-ram').innerText = `${gbLabel} GB`;
        
        const memBar = document.getElementById('ram-bar');
        memBar.style.width = `${memPct}%`;
        
        // Colores heurísticos Neumórficos
        memBar.className = "progress-fill"; // reset
        if(memPct > 85) memBar.classList.add("danger");
        else if (memPct > 65) memBar.classList.add("warning");
        else memBar.classList.add("success");
    } catch(e) { /* silent fail offline / background */ }
}
// Run every 4s
setInterval(updateSystemStats, 4000);
updateSystemStats();


// ── Interacciones de la Caja de Texto ──
userInput.addEventListener('input', function() {
    this.style.height = 'auto';
    this.style.height = (this.scrollHeight) + 'px';
    btnSend.disabled = this.value.trim().length === 0;
});

// ── Lógica Central de Chat Streaming ──
let isGenerating = false;

function appendMessage(role, text, isStream = false) {
    if (welcomeScreen && welcomeScreen.parentNode) welcomeScreen.remove();

    let row = document.createElement('div');
    row.className = `message-row ${role}`;
    
    let avatar = document.createElement('div');
    avatar.className = 'btn-circle neu-concave icon';
    avatar.style.width = '45px'; avatar.style.height = '45px';
    avatar.innerHTML = role === 'bot' ? botIconSVG : userIconSVG;
    
    let bubble = document.createElement('div');
    bubble.className = 'msg-bubble neu-convex';
    if(role === 'user') bubble.style.color = 'var(--accent-color)';
    
    if (isStream) {
        bubble.innerHTML = `<div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>`;
    } else {
        bubble.innerHTML = `<p>${text.replace(/\\n/g, '<br>')}</p>`;
    }

    row.appendChild(bubble);
    row.appendChild(avatar);
    chatContainer.appendChild(row);
    chatContainer.scrollTo({ top: chatContainer.scrollHeight, behavior: 'smooth' });
    return bubble;
}

async function sendMessage() {
    if (isGenerating) return;
    const text = userInput.value.trim();
    if (!text) return;

    userInput.value = '';
    userInput.style.height = 'auto';
    btnSend.disabled = true;
    isGenerating = true;

    // Transition button safely
    btnSend.classList.add('neu-concave');
    btnSend.classList.remove('neu-convex');

    appendMessage('user', text);
    const streamBubble = appendMessage('bot', '', true);

    try {
        const payload = {
            message: text,
            subject: selSubj ? selSubj.value : "general_english",
            level: selLevel ? selLevel.value : "intermediate",
            mode: selMode ? selMode.value : "normal",
            user_id: inpUserid ? inpUserid.value : "estudiante_1",
            max_tokens: parseInt(localStorage.getItem('pme_maxtok') || '512'),
            temperature: parseFloat(localStorage.getItem('pme_temp') || '0.4'),
            top_p: parseFloat(localStorage.getItem('pme_topp') || '0.9'),
            repeat_penalty: parseFloat(localStorage.getItem('pme_rep') || '1.1'),
            top_k_rag: parseInt(localStorage.getItem('pme_topk') || '4'),
            eval_mode: localStorage.getItem('pme_eval') || 'fast',
            auto_retry: (localStorage.getItem('pme_retry') || '1') === '1'
        };

        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let fullText = "";
        let firstTokenReceived = false;

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            const chunkInfo = decoder.decode(value);
            const lines = chunkInfo.split('\n');
            
            for (let line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        if (data.type === "context") {
                            if (data.sources && data.sources.length > 0) {
                                window.currentSources = data.sources;
                            } else {
                                window.currentSources = [];
                            }
                        } 
                        else if (data.type === "token") {
                            if (!firstTokenReceived) {
                                streamBubble.innerHTML = ""; 
                                firstTokenReceived = true;
                            }
                            fullText += data.text;
                            streamBubble.innerHTML = `<p>${fullText.replace(/\\n/g, '<br>')}</p>`;
                            chatContainer.scrollTo(0, chatContainer.scrollHeight);
                        }
                        else if (data.type === "metrics") {
                            const ev = data.data;
                            const ov = ev.overall_score || 0;
                            const gr = ev.grounding_score || 0;
                            const re = ev.relevance_score || 0;
                            const ok = ev.pass || false;
                            const fb = ev.is_fallback || false;
                            
                            const clsQual = ok ? "ok" : (fb ? "fallback" : "bad");
                            const txtQual = ok ? "VERIFICADO" : (fb ? "FALLBACK" : "ALERTA");
                            
                            const buildBar = (label, pct) => {
                                const fillColor = pct >= 0.65 ? "#34d399" : (pct >= 0.35 ? "#fbbf24" : "#fb7185");
                                return `<div class="q-row" style="display:flex; align-items:center; gap:10px; font-size:12px; font-weight:600; color:var(--text-muted); margin-bottom: 8px;">
                                    <span style="width: 80px; font-size:10px; text-transform:uppercase;">${label}</span>
                                    <div class="progress-container neu-concave" style="flex:1; height:12px; padding:2px;">
                                        <div class="progress-fill" style="width:${Math.round(pct*100)}%; background:${fillColor}; border-radius:4px; height:100%; box-shadow: 2px 2px 4px var(--shadow-dark);"></div>
                                    </div>
                                    <span style="width:30px; text-align:right;">${Math.round(pct*100)}%</span>
                                </div>`;
                            };

                            let metricsHtml = `
                                <div class="q-card neu-concave" style="padding: 20px; border-radius: 20px; margin-top: 25px;">
                                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 15px;">
                                        <span style="font-size:11px; font-weight:700; color:var(--text-dark);">CALIDAD IA EVALUADOR</span>
                                        <span class="q-status ${clsQual}">${txtQual}</span>
                                    </div>
                                    ${buildBar('Confianza', ov)}
                                    ${buildBar('Fundam.', gr)}
                                    ${buildBar('Impacto', re)}
                                    <div style="display:flex; gap:10px; margin-top:10px; flex-wrap:wrap;">
                                        <span class="neu-convex" style="padding:4px 10px; border-radius:10px; font-size:10px; color:var(--text-muted);">T: ${data.gen_time.toFixed(1)}s</span>
                                    </div>
                                </div>
                            `;
                            streamBubble.innerHTML += metricsHtml;
                        }
                        else if (data.type === "done") {
                            isGenerating = false;
                            btnSend.disabled = false;
                            btnSend.classList.add('neu-convex');
                            btnSend.classList.remove('neu-concave');
                            
                            // Widgets RAG
                            if (window.currentSources && window.currentSources.length > 0) {
                                let sourcesHtml = `<div class="rag-meta" style="margin-top: 20px; border-top: 2px dashed var(--shadow-dark); padding-top: 15px;">`;
                                sourcesHtml += `<button class="btn-text neu-convex" onclick="this.nextElementSibling.classList.toggle('open')" style="font-size:11px; display:inline-flex; align-items:center; gap:5px;"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg> Fuentes Doc. (${window.currentSources.length})</button>`;
                                sourcesHtml += `<div class="rag-sources" style="margin-top: 15px;">`;
                                window.currentSources.forEach(src => {
                                    sourcesHtml += `<div class="src-item neu-concave" style="padding: 10px 15px; border-radius: 12px; margin-bottom: 10px;">
                                    <span style="color:var(--accent-color); font-weight:bold; margin-right:5px;">›</span> ${src}</div>`;
                                });
                                sourcesHtml += `</div></div>`;
                                streamBubble.innerHTML += sourcesHtml;
                                window.currentSources = [];
                            }
                            
                            chatContainer.scrollTo(0, chatContainer.scrollHeight);
                        }
                        else if (data.type === "error") {
                            showToast("Error Interno de la IA", "error");
                            isGenerating = false;
                        }
                    } catch (e) {
                         // stream boundary parsing skips
                    }
                }
            }
        }
    } catch (err) {
        showToast("Se perdió la conexión offline con la API", "error");
        isGenerating = false;
        btnSend.disabled = false;
        btnSend.classList.add('neu-convex');
        btnSend.classList.remove('neu-concave');
        streamBubble.innerHTML = "<p><i>(No se pudo conectar al cerebro AI en este momento)</i></p>";
    }
}

btnSend.addEventListener('click', sendMessage);
userInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

if(btnResetChat) {
    btnResetChat.addEventListener('click', () => {
        openDialog('Comenzar de Nuevo', '¿Confirmas limpiar el historial visual de esta conversación?', () => {
            Array.from(chatContainer.children).forEach((node) => {
                if(node.id !== 'welcome-screen') node.remove();
            });
            showToast("Conversación y contexto visual limpiados", "success");
            // Reactivar welcome message
            if (welcomeScreen && !document.getElementById('welcome-screen')) {
                chatContainer.appendChild(welcomeScreen);
                initWelcomeScreen();
            }
            userInput.focus();
        });
    });
}

// ── Inicialización: Sincronizar UI y motor desde USB ──
window.addEventListener('DOMContentLoaded', async () => {
    initWelcomeScreen();
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
            
            const _the = localStorage.getItem('pme_theme') || 'purple';
            const _bg = localStorage.getItem('pme_bg') || 'default';
            document.body.className = `layout theme-${_the} bg-${_bg}`;
        }
    } catch(e) { }
});

// ── Historial de USB ──
const historyDialog = document.getElementById('historyDialog');
const btnHistory = document.getElementById('btn-history');
const btnCloseHistory = document.getElementById('btnCloseHistory');
const historyList = document.getElementById('history-list');

if(btnHistory) {
    btnHistory.addEventListener('click', () => {
        historyDialog.classList.add('active');
        loadHistoryList();
    });
}
if(btnCloseHistory) {
    btnCloseHistory.addEventListener('click', () => {
        historyDialog.classList.remove('active');
    });
}

async function loadHistoryList() {
    if(!historyList) return;
    historyList.innerHTML = '<p style="text-align: center; color: var(--text-muted); padding: 20px;">Cargando desde USB...</p>';
    try {
        const res = await fetch('/api/history');
        const data = await res.json();
        
        if(!data.history || data.history.length === 0) {
            historyList.innerHTML = '<p style="text-align: center; color: var(--text-placeholder); padding: 20px;">No hay conversaciones guardadas en la USB.</p>';
            return;
        }
        
        historyList.innerHTML = '';
        data.history.forEach(item => {
            const dateStr = item.start_time.split('.')[0].replace('T', ' ');
            const div = document.createElement('div');
            div.className = 'history-item neu-concave';
            div.style.cssText = 'padding: 15px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; border: 1px solid transparent; transition: all 0.3s ease;';
            div.onmouseover = () => { div.style.borderColor = 'var(--accent-color)'; };
            div.onmouseout = () => { div.style.borderColor = 'transparent'; };
            
            div.innerHTML = `
                <div style="flex:1; cursor:pointer;" onclick="loadHistorySession('${item.file_id}')">
                    <strong style="color:var(--text-dark); display:block; margin-bottom:5px; font-family: var(--font-base);">ID Alumno: ${item.user_id}</strong>
                    <div style="font-size:12px; color:var(--text-muted); display:flex; align-items:center; gap:5px; flex-wrap:wrap;">
                        <span style="display:inline-flex; align-items:center; gap:4px; margin-bottom:4px;"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg> ${dateStr}</span> &nbsp;|&nbsp; <span style="display:inline-flex; align-items:center; gap:4px;"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg> ${item.turns_count} turnos</span><br>
                        <span style="text-transform: capitalize; color:var(--accent-color); font-weight:600;">Tema: ${item.subject.replace('_',' ')} (${item.level})</span>
                    </div>
                </div>
                <button class="btn-circle neu-convex icon" onclick="deleteHistorySession('${item.file_id}')" style="width:40px; height:40px; color:#fb7185; flex-shrink:0;" title="Eliminar Permanentemente">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:16px; height:16px;"><path d="M3 6h18"></path><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>
                </button>
            `;
            historyList.appendChild(div);
        });
    } catch(e) {
        historyList.innerHTML = '<p style="text-align: center; color: #fb7185; padding: 20px;">Error al leer la base de datos USB.</p>';
    }
}

async function deleteHistorySession(fileId) {
    if (typeof openDialog === 'function') {
        openDialog('Eliminar Sesión', '¿Estás seguro de eliminar el registro de esta sesión permanentemente de la USB?', async () => {
            try {
                const res = await fetch(`/api/history/${fileId}`, { method: 'DELETE' });
                if(res.ok) {
                    showToast("Sesión eliminada de la USB", "success");
                    loadHistoryList();
                } else {
                    showToast("Fallo al eliminar archivo", "error");
                }
            } catch(e) {
                showToast("Error de conexión eliminando sesión", "error");
            }
        });
    }
}

async function loadHistorySession(fileId) {
    try {
        const res = await fetch(`/api/history/${fileId}`);
        const data = await res.json();
        
        // Restaurar top bar
        if(inpUserid) inpUserid.value = data.user_id;
        if(selSubj) selSubj.value = data.subject || "general_english";
        if(selLevel) selLevel.value = data.level || "intermediate";
        
        // Limpiar contenedor de chat visual (sin triggerar endpoint o modal)
        Array.from(chatContainer.children).forEach((node) => {
            if(node.id !== 'welcome-screen') node.remove();
        });
        if (welcomeScreen && welcomeScreen.parentNode) welcomeScreen.remove();
        
        // Renderizar turnos historicos
        if(data.turns && data.turns.length > 0) {
            data.turns.forEach(turn => {
                if(turn.user_msg) appendMessage('user', turn.user_msg);
                if(turn.agent_response) appendMessage('bot', turn.agent_response);
            });
        }
        
        // Forzar al backend a cargar la memoria desde este archivo exacto
        await fetch(`/api/history/${fileId}/resume`, { method: 'POST' });
        
        // Close modal
        historyDialog.classList.remove('active');
        showToast(`Memoria de session cargada y reanudada`, "success");
        
        // Scroll al final
        setTimeout(() => chatContainer.scrollTo(0, chatContainer.scrollHeight), 100);
        
    } catch(e) {
        showToast("Error recuperando o reanudando el historial", "error");
    }
}
