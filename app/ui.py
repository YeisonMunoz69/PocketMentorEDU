"""
ui.py — Pocket Mentor EDU
Rediseño completo: estética editorial científica de lujo.
Tipografía serif + terminal, capas de luz ambiental, layout asimétrico.
Compatible Gradio 6.6.0
"""

import logging
import time
from pathlib import Path
from typing import List, Dict, Tuple

log = logging.getLogger("ui")

# ─────────────────────────────────────────────────────────────────────────────
# DESIGN SYSTEM — Editorial científica de lujo
# ─────────────────────────────────────────────────────────────────────────────
CUSTOM_CSS = """
/* Fuentes locales del sistema — sin dependencias de internet */

/* ── Variables ────────────────────────────────────────────────────────────── */
:root {
    --ink:        #0c0d11;
    --paper:      #11131a;
    --surface:    #181b24;
    --raised:     #1e2230;
    --border:     rgba(255,255,255,0.07);
    --border-hi:  rgba(255,255,255,0.13);
    --gold:       #c9a84c;
    --gold-dim:   rgba(201,168,76,0.12);
    --gold-glow:  rgba(201,168,76,0.06);
    --teal:       #4ecdc4;
    --teal-dim:   rgba(78,205,196,0.10);
    --red-warm:   #e07a5f;
    --green-sage: #81b29a;
    --text-1:     #e9eaf2;
    --text-2:     #9195aa;
    --text-3:     #50546a;
    --serif:      Georgia, 'Times New Roman', serif;
    --mono:       Consolas, 'Courier New', monospace;
    --body:       Cambria, Georgia, 'Times New Roman', serif;
    --r:          8px;
    --r-lg:       14px;
}

/* ── Reset ───────────────────────────────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }
.gradio-container, .gradio-container * { font-family: var(--body) !important; }
body, .gradio-container { background: var(--ink) !important; color: var(--text-1) !important; }
footer, .svelte-1ipelgc { display: none !important; }

/* ── Fondo con textura sutil ─────────────────────────────────────────────── */
body::before {
    content: '';
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background:
        radial-gradient(ellipse 80% 50% at 20% 10%, rgba(201,168,76,0.04) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 90%, rgba(78,205,196,0.03) 0%, transparent 60%);
}

/* ── Header ──────────────────────────────────────────────────────────────── */
.pme-header {
    position: relative; overflow: hidden;
    padding: 28px 32px 22px;
    background: linear-gradient(180deg, rgba(201,168,76,0.06) 0%, transparent 100%);
    border-bottom: 1px solid var(--border-hi);
    display: flex; align-items: flex-end; justify-content: space-between;
}
.pme-wordmark {
    font-family: var(--serif) !important;
    font-size: 28px; font-weight: 700;
    color: var(--text-1); letter-spacing: -0.5px;
    line-height: 1;
}
.pme-wordmark em {
    font-style: italic; color: var(--gold);
}
.pme-tagline {
    font-family: var(--mono) !important;
    font-size: 10px; color: var(--text-3);
    letter-spacing: 2.5px; text-transform: uppercase;
    margin-top: 6px;
}
.pme-badge {
    font-family: var(--mono) !important;
    font-size: 10px; color: var(--green-sage);
    background: rgba(129,178,154,0.1);
    border: 1px solid rgba(129,178,154,0.25);
    border-radius: 4px; padding: 4px 10px;
    letter-spacing: 1px;
}
.pme-header-line {
    position: absolute; bottom: 0; left: 32px; right: 32px;
    height: 1px;
    background: linear-gradient(90deg, var(--gold), transparent 60%);
    opacity: 0.4;
}

/* ── Tabs ────────────────────────────────────────────────────────────────── */
.tab-nav {
    background: var(--paper) !important;
    border-bottom: 1px solid var(--border) !important;
    padding: 0 24px !important; gap: 0 !important;
}
.tab-nav button {
    font-family: var(--mono) !important;
    font-size: 11px !important; font-weight: 600 !important;
    letter-spacing: 1.5px !important; text-transform: uppercase !important;
    color: var(--text-3) !important;
    padding: 14px 20px !important;
    border-bottom: 2px solid transparent !important;
    transition: all 0.2s ease !important;
    border-radius: 0 !important;
}
.tab-nav button.selected {
    color: var(--gold) !important;
    border-bottom-color: var(--gold) !important;
}
.tab-nav button:hover:not(.selected) { color: var(--text-2) !important; }

/* ── Sección labels ──────────────────────────────────────────────────────── */
.sec-label {
    font-family: var(--mono) !important;
    font-size: 9px !important; font-weight: 600 !important;
    letter-spacing: 2.5px !important; text-transform: uppercase !important;
    color: var(--text-3) !important;
    padding-bottom: 8px !important;
    border-bottom: 1px solid var(--border) !important;
    margin-bottom: 14px !important;
    display: block !important;
}

/* ── Chatbot ─────────────────────────────────────────────────────────────── */
.chat-panel {
    background: var(--paper) !important;
    border: 1px solid var(--border-hi) !important;
    border-radius: var(--r-lg) !important;
    overflow: hidden;
}
.chat-panel .message-wrap { padding: 4px 0 !important; }
.chat-panel .message.user {
    background: linear-gradient(135deg, rgba(201,168,76,0.08), rgba(201,168,76,0.04)) !important;
    border: 1px solid rgba(201,168,76,0.18) !important;
    border-radius: 12px 12px 3px 12px !important;
    color: var(--text-1) !important;
    font-size: 14px !important; line-height: 1.75 !important;
}
.chat-panel .message.bot {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px 12px 12px 3px !important;
    color: var(--text-1) !important;
    font-size: 14px !important; line-height: 1.75 !important;
}
.chat-panel .message p { margin: 0 0 8px 0 !important; }
.chat-panel .message p:last-child { margin-bottom: 0 !important; }

/* ── Input ───────────────────────────────────────────────────────────────── */
#msg-input textarea {
    background: var(--surface) !important;
    border: 1px solid var(--border-hi) !important;
    border-radius: var(--r) !important;
    color: var(--text-1) !important;
    font-family: var(--body) !important;
    font-size: 14px !important; line-height: 1.6 !important;
    padding: 12px 14px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
    resize: none !important;
    pointer-events: auto !important;
    user-select: text !important;
    -webkit-user-select: text !important;
}
#msg-input textarea:focus {
    border-color: rgba(201,168,76,0.5) !important;
    box-shadow: 0 0 0 3px rgba(201,168,76,0.08) !important;
    outline: none !important;
}
#msg-input textarea::placeholder { color: var(--text-3) !important; }

/* ── Botones ─────────────────────────────────────────────────────────────── */
.btn-primary {
    font-family: var(--mono) !important;
    font-size: 12px !important; font-weight: 600 !important;
    letter-spacing: 1.5px !important; text-transform: uppercase !important;
    background: linear-gradient(135deg, #b8923e, var(--gold)) !important;
    border: none !important;
    border-radius: var(--r) !important;
    color: #0c0d11 !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 20px rgba(201,168,76,0.25) !important;
}
.btn-primary:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 28px rgba(201,168,76,0.35) !important;
}
.btn-ghost {
    font-family: var(--mono) !important;
    font-size: 11px !important; font-weight: 600 !important;
    letter-spacing: 1px !important; text-transform: uppercase !important;
    background: transparent !important;
    border: 1px solid var(--border-hi) !important;
    border-radius: var(--r) !important;
    color: var(--text-3) !important;
    transition: all 0.2s !important;
}
.btn-ghost:hover {
    border-color: var(--gold) !important;
    color: var(--gold) !important;
}

/* ── Controles laterales ─────────────────────────────────────────────────── */
.gradio-dropdown label, .gradio-textbox label, .gradio-slider label {
    font-family: var(--mono) !important;
    font-size: 10px !important; font-weight: 600 !important;
    letter-spacing: 1.5px !important; text-transform: uppercase !important;
    color: var(--text-3) !important;
}
.gradio-dropdown select, .gradio-dropdown input,
.gradio-textbox input, .gradio-textbox textarea {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r) !important;
    color: var(--text-1) !important;
    font-family: var(--mono) !important;
    font-size: 12px !important;
    transition: border-color 0.2s !important;
}
.gradio-dropdown select:focus, .gradio-textbox input:focus {
    border-color: rgba(201,168,76,0.4) !important;
}
.gradio-slider input[type=range] { accent-color: var(--gold) !important; }
.gradio-slider .range-value {
    font-family: var(--mono) !important;
    font-size: 12px !important; color: var(--gold) !important;
}

/* ── Indicador de pensando ───────────────────────────────────────────────── */
.thinking {
    display: flex; align-items: center; gap: 12px;
    padding: 13px 16px;
    background: linear-gradient(90deg, rgba(201,168,76,0.06), transparent);
    border: 1px solid rgba(201,168,76,0.2);
    border-left: 3px solid var(--gold);
    border-radius: var(--r);
    margin-bottom: 10px;
}
.thinking-ring {
    width: 16px; height: 16px; flex-shrink: 0;
    border: 2px solid rgba(201,168,76,0.2);
    border-top-color: var(--gold);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.thinking-label {
    font-family: var(--mono) !important;
    font-size: 11px; color: var(--gold);
    letter-spacing: 1.5px; text-transform: uppercase;
}
.thinking-sub {
    font-family: var(--mono) !important;
    font-size: 10px; color: var(--text-3); margin-left: auto;
}

/* ── Panel de fuentes ────────────────────────────────────────────────────── */
.src-block {
    margin-bottom: 10px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r);
    overflow: hidden;
    transition: border-color 0.2s;
}
.src-block:hover { border-color: var(--border-hi); }
.src-head {
    display: flex; align-items: center; justify-content: space-between;
    padding: 9px 12px;
    background: rgba(255,255,255,0.02);
    border-bottom: 1px solid var(--border);
}
.src-name {
    font-family: var(--mono) !important;
    font-size: 11px; font-weight: 600; color: var(--teal);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    max-width: 140px;
}
.src-score-pill {
    font-family: var(--mono) !important;
    font-size: 9px; font-weight: 600; padding: 2px 7px;
    border-radius: 20px; flex-shrink: 0; margin-left: 8px;
}
.src-score-pill.good { background: rgba(129,178,154,0.15); color: var(--green-sage); border: 1px solid rgba(129,178,154,0.3); }
.src-score-pill.mid  { background: rgba(201,168,76,0.12);  color: var(--gold);       border: 1px solid rgba(201,168,76,0.25); }
.src-score-pill.bad  { background: rgba(224,122,95,0.12);  color: var(--red-warm);   border: 1px solid rgba(224,122,95,0.25); }
.src-page {
    font-family: var(--mono) !important;
    font-size: 9px; color: var(--text-3); padding: 0 12px 8px;
    margin-top: 6px;
}
.src-snippet {
    font-size: 11px; color: var(--text-2); line-height: 1.6;
    padding: 0 12px 10px; font-family: var(--body) !important;
}

/* ── Barras de calidad ───────────────────────────────────────────────────── */
.q-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r-lg);
    padding: 16px;
    margin-bottom: 12px;
}
.q-header {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 14px;
}
.q-title { font-family: var(--mono) !important; font-size: 9px; letter-spacing: 2px; text-transform: uppercase; color: var(--text-3); }
.q-status {
    font-family: var(--mono) !important;
    font-size: 9px; font-weight: 700; letter-spacing: 1px;
    padding: 3px 8px; border-radius: 3px;
}
.q-row { display: flex; align-items: center; gap: 10px; margin-bottom: 7px; }
.q-label { font-family: var(--mono) !important; font-size: 9px; letter-spacing: 0.5px; color: var(--text-3); width: 82px; flex-shrink: 0; text-transform: uppercase; }
.q-track { flex: 1; height: 4px; background: rgba(255,255,255,0.05); border-radius: 2px; overflow: hidden; }
.q-fill  { height: 100%; border-radius: 2px; transition: width 1s cubic-bezier(0.4,0,0.2,1); }
.q-fill.hi { background: linear-gradient(90deg, #81b29a, #a8d5b5); box-shadow: 0 0 6px rgba(129,178,154,0.5); }
.q-fill.md { background: linear-gradient(90deg, #c9a84c, #e0c070); box-shadow: 0 0 6px rgba(201,168,76,0.4); }
.q-fill.lo { background: linear-gradient(90deg, #e07a5f, #f0a090); box-shadow: 0 0 6px rgba(224,122,95,0.4); }
.q-pct { font-family: var(--mono) !important; font-size: 10px; color: var(--text-3); width: 30px; text-align: right; }
.q-chips { display: flex; gap: 6px; margin-top: 12px; flex-wrap: wrap; }
.q-chip { font-family: var(--mono) !important; font-size: 9px; color: var(--text-3); background: rgba(255,255,255,0.03); border: 1px solid var(--border); border-radius: 4px; padding: 3px 8px; }
.q-chip span { color: var(--text-1); font-weight: 600; }

/* ── Panel modelo ────────────────────────────────────────────────────────── */
.param-note { font-family: var(--mono) !important; font-size: 10px; color: var(--text-3); line-height: 1.5; margin-top: 2px; margin-bottom: 10px; }
.stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.stat-cell { text-align: center; padding: 12px 8px; background: var(--paper); border: 1px solid var(--border); border-radius: var(--r); }
.stat-val { font-family: var(--mono) !important; font-size: 20px; font-weight: 700; line-height: 1; margin-bottom: 4px; }
.stat-lbl { font-family: var(--mono) !important; font-size: 8px; letter-spacing: 1.5px; text-transform: uppercase; color: var(--text-3); }

/* ── Dashboard ───────────────────────────────────────────────────────────── */
.dash-table { width: 100%; border-collapse: collapse; }
.dash-table th { font-family: var(--mono) !important; font-size: 9px; letter-spacing: 1.5px; text-transform: uppercase; color: var(--text-3); padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--border-hi); }
.dash-table td { padding: 9px 12px; font-family: var(--mono) !important; font-size: 11px; border-bottom: 1px solid var(--border); }
.dash-table tr:last-child td { border-bottom: none; }
.dash-table tr:hover td { background: rgba(255,255,255,0.02); }

/* ── Scrollbar ───────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border-hi); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(201,168,76,0.4); }

/* ── Markdown en chat ────────────────────────────────────────────────────── */
.chat-panel .message code {
    font-family: var(--mono) !important;
    background: rgba(255,255,255,0.06) !important;
    padding: 1px 5px !important; border-radius: 3px !important;
    font-size: 12px !important;
}
.chat-panel .message pre {
    background: var(--ink) !important;
    border: 1px solid var(--border-hi) !important;
    border-radius: 6px !important; padding: 12px !important;
}
"""


# ─────────────────────────────────────────────────────────────────────────────
# HTML helpers
# ─────────────────────────────────────────────────────────────────────────────

def _qbar(label: str, pct: float) -> str:
    cls = "hi" if pct >= 0.65 else ("md" if pct >= 0.35 else "lo")
    return (f'<div class="q-row">'
            f'<span class="q-label">{label}</span>'
            f'<div class="q-track"><div class="q-fill {cls}" style="width:{pct*100:.0f}%"></div></div>'
            f'<span class="q-pct">{pct*100:.0f}%</span>'
            f'</div>')


def _quality_html(ev: Dict, rag_t: float, gen_t: float) -> str:
    ov = ev.get("overall_score", 0)
    gr = ev.get("grounding_score", 0)
    re = ev.get("relevance_score", 0)
    ok = ev.get("pass", False)
    fb = ev.get("is_fallback", False)
    sc = "#81b29a" if ok else ("#c9a84c" if fb else "#e07a5f")
    st = "VERIFIED" if ok else ("FALLBACK" if fb else "LOW")
    return (f'<div class="q-card">'
            f'<div class="q-header">'
            f'<span class="q-title">Calidad</span>'
            f'<span class="q-status" style="color:{sc};background:{sc}18;border:1px solid {sc}33">{st}</span>'
            f'</div>'
            f'{_qbar("Confianza",  ov)}'
            f'{_qbar("Fundament.", gr)}'
            f'{_qbar("Relevancia", re)}'
            f'<div class="q-chips">'
            f'<span class="q-chip">RAG <span>{rag_t:.1f}s</span></span>'
            f'<span class="q-chip">Gen <span>{gen_t:.1f}s</span></span>'
            f'<span class="q-chip">Eval <span>{ev.get("mode","?").upper()}</span></span>'
            f'</div></div>')


def _thinking_html() -> str:
    ts = time.strftime("%H:%M:%S")
    return (f'<div class="thinking">'
            f'<div class="thinking-ring"></div>'
            f'<span class="thinking-label">Procesando consulta</span>'
            f'<span class="thinking-sub">{ts}</span>'
            f'</div>')


def _source_html(results: List[Dict]) -> str:
    if not results:
        return ('<div style="padding:24px;text-align:center">'
                '<div style="font-family:var(--mono);font-size:10px;color:var(--text-3);'
                'letter-spacing:2px;text-transform:uppercase">Sin fuentes</div></div>')
    parts = ['<div style="padding:4px 0">',
             '<div style="font-family:var(--mono);font-size:9px;letter-spacing:2px;'
             'text-transform:uppercase;color:var(--text-3);margin-bottom:10px">Documentos recuperados</div>']
    for i, r in enumerate(results[:4], 1):
        sc = r.get("rerank_score", r.get("score", 0))
        pill_cls = "good" if sc > 0.5 else ("mid" if sc > 0 else "bad")
        sc_txt   = f"{sc:.2f}"
        snip = r["text"][:200].replace("<","&lt;").replace(">","&gt;").replace("\n"," ") + "…"
        fname = r["source"]
        if len(fname) > 26: fname = fname[:23] + "…"
        parts.append(
            f'<div class="src-block">'
            f'<div class="src-head">'
            f'<span class="src-name" title="{r["source"]}">{i}. {fname}</span>'
            f'<span class="src-score-pill {pill_cls}">{sc_txt}</span>'
            f'</div>'
            f'<div class="src-page">Pág. {r["page"]}</div>'
            f'<div class="src-snippet">{snip}</div>'
            f'</div>'
        )
    parts.append('</div>')
    return "".join(parts)


EMPTY_Q = ('<div class="q-card" style="text-align:center;padding:24px 16px">'
           '<div style="font-family:var(--serif);font-size:22px;color:var(--text-3);'
           'margin-bottom:6px;font-style:italic">Calidad</div>'
           '<div style="font-family:var(--mono);font-size:9px;letter-spacing:1.5px;'
           'color:var(--text-3);text-transform:uppercase">Pendiente de consulta</div>'
           '</div>')

EMPTY_SRC = ('<div style="padding:24px;text-align:center">'
             '<div style="font-family:var(--serif);font-size:22px;color:var(--text-3);'
             'margin-bottom:6px;font-style:italic">Fuentes</div>'
             '<div style="font-family:var(--mono);font-size:9px;letter-spacing:1.5px;'
             'color:var(--text-3);text-transform:uppercase">Pendiente de consulta</div>'
             '</div>')


# ─────────────────────────────────────────────────────────────────────────────
# Inferencia
# ─────────────────────────────────────────────────────────────────────────────

def _gen(llm, prompt, max_tokens=512, temperature=0.4, top_p=0.9, rp=1.1) -> str:
    try:
        r = llm(prompt, max_tokens=int(max_tokens), temperature=float(temperature),
                top_p=float(top_p), repeat_penalty=float(rp), echo=False,
                stop=["Estudiante:", "━━━", "\n\nTutor:", "Human:",
                      "\nFuente:", "\n---", "[Fuente:", "---\n"])
        return r["choices"][0]["text"].strip()
    except Exception as e:
        log.error(f"Inferencia: {e}")
        return "Lo siento, ocurrió un error. Intenta de nuevo."


def process_message(message, history, llm, rag, evaluator, memory,
                    subject, level, mode, user_id, max_tokens, temp, top_p, rp,
                    topk=5, do_retry=True):
    from prompt_builder import build_system_prompt, build_full_prompt
    if not message.strip():
        return history, EMPTY_SRC, EMPTY_Q, ""

    memory.level   = level
    memory.subject = subject
    memory.add_turn("user", message, llm)
    memory.add_topic(subject)

    t0 = time.time()
    results = rag.hybrid_search(message, top_k=topk, llm=llm)
    context = rag.build_context(results)
    rag_t = time.time() - t0

    prompt = build_full_prompt(
        system_prompt=build_system_prompt(subject=subject, level=level, mode=mode),
        context=context,
        memory_block=memory.build_memory_block(),
        student_profile=memory.build_student_profile_block(),
        query=message,
    )

    t1 = time.time()
    response = _gen(llm, prompt, max_tokens, temp, top_p, rp)
    gen_t = time.time() - t1

    ev = evaluator.evaluate(query=message, response=response,
                            context_chunks=results, student_level=level)
    if do_retry and not ev["pass"] and not ev["is_fallback"]:
        log.info(f"Retry (score {ev['overall_score']:.2f})")
        response = _gen(llm, prompt, max_tokens, max(0.1, temp - 0.15), top_p, rp)
        ev = evaluator.evaluate(message, response, results, level)

    memory.add_turn("assistant", response)
    history.append({"role": "user",      "content": message})
    history.append({"role": "assistant", "content": response})

    return (history, _source_html(results), _quality_html(ev, rag_t, gen_t),
            f"RAG {rag_t:.1f}s · Gen {gen_t:.1f}s · Score {ev['overall_score']:.2f}")


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard helpers
# ─────────────────────────────────────────────────────────────────────────────

def _dash_session(ev) -> str:
    s = ev.get_session_summary()
    if not s:
        return ('<div style="padding:32px;text-align:center;font-family:var(--mono);'
                'font-size:10px;color:var(--text-3);letter-spacing:1.5px;text-transform:uppercase">'
                'Sin datos en esta sesión</div>')
    sc = s.get("avg_score", 0)
    c  = "#81b29a" if sc >= 0.65 else ("#c9a84c" if sc >= 0.4 else "#e07a5f")
    return (f'<div class="stat-grid">'
            f'<div class="stat-cell"><div class="stat-val" style="color:{c}">{sc*100:.0f}%</div>'
            f'<div class="stat-lbl">Score medio</div></div>'
            f'<div class="stat-cell"><div class="stat-val" style="color:var(--teal)">{s.get("total_turns",0)}</div>'
            f'<div class="stat-lbl">Turnos</div></div>'
            f'<div class="stat-cell"><div class="stat-val" style="color:var(--gold)">{s.get("fallback_rate",0)*100:.0f}%</div>'
            f'<div class="stat-lbl">Fallback</div></div>'
            f'<div class="stat-cell"><div class="stat-val" style="color:var(--green-sage)">{s.get("pass_rate",0)*100:.0f}%</div>'
            f'<div class="stat-lbl">Pass rate</div></div>'
            f'</div>')


def _dash_history(ev) -> str:
    sessions = ev.load_historical_metrics()
    if not sessions:
        return ('<div style="padding:32px;text-align:center;font-family:var(--mono);'
                'font-size:10px;color:var(--text-3);letter-spacing:1.5px;text-transform:uppercase">'
                'Sin sesiones guardadas</div>')
    rows = ""
    for s in sessions[-10:]:
        sc = s.get("avg_score", 0)
        c  = "#81b29a" if sc >= 0.65 else ("#c9a84c" if sc >= 0.4 else "#e07a5f")
        fname = s.get("session_file","?")[:20]
        rows += (f'<tr><td style="color:var(--text-3)">{fname}</td>'
                 f'<td style="text-align:center">{s.get("total_turns",0)}</td>'
                 f'<td style="text-align:center;color:{c};font-weight:700">{sc*100:.0f}%</td>'
                 f'<td style="text-align:center;color:var(--gold)">{s.get("fallback_rate",0)*100:.0f}%</td>'
                 f'<td style="text-align:center;color:var(--green-sage)">{s.get("pass_rate",0)*100:.0f}%</td>'
                 f'</tr>')
    return (f'<table class="dash-table">'
            f'<thead><tr><th>Sesión</th><th>Turnos</th><th>Score</th><th>Fallback</th><th>Pass</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>')


# ─────────────────────────────────────────────────────────────────────────────
# Launch
# ─────────────────────────────────────────────────────────────────────────────

def launch_ui(llm, rag, evaluator, sess_dir: Path, prompt_dir: Path,
              model_name: str = ""):
    try:
        import gradio as gr
    except ImportError:
        raise

    from memory         import SessionMemory
    from prompt_builder import list_subjects

    _mem: dict = {}
    def get_mem(uid: str) -> SessionMemory:
        u = (uid or "default").strip()
        if u not in _mem:
            _mem[u] = SessionMemory(sess_dir=sess_dir, user_id=u)
        return _mem[u]

    evaluator.logs_dir = sess_dir.parent / "logs"
    evaluator.logs_dir.mkdir(parents=True, exist_ok=True)

    with gr.Blocks(title="Pocket Mentor EDU") as app:

        # ── Header ────────────────────────────────────────────────────────────
        gr.HTML(
            '<div class="pme-header">'
            '  <div>'
            '    <div class="pme-wordmark">Pocket <em>Mentor</em> EDU</div>'
            '    <div class="pme-tagline">RAG Híbrido · Offline · Privacidad total</div>'
            '  </div>'
            '  <div class="pme-badge">● ACTIVO</div>'
            '  <div class="pme-header-line"></div>'
            '</div>'
        )

        with gr.Tabs():

            # ══════════════════════════════════════════════════════════════════
            # TUTOR
            # ══════════════════════════════════════════════════════════════════
            with gr.TabItem("Tutor"):
                with gr.Row(equal_height=False):

                    # Columna izquierda
                    with gr.Column(scale=1, min_width=220):
                        gr.HTML('<span class="sec-label">Configuración</span>')
                        subject_dd = gr.Dropdown(choices=list_subjects(), value="general", label="Materia")
                        level_dd   = gr.Dropdown(choices=["basic","intermediate","advanced"], value="intermediate", label="Nivel")
                        mode_dd    = gr.Dropdown(choices=["normal","socratic","quiz","visual"], value="normal", label="Modo")
                        user_id_tb = gr.Textbox(value="estudiante_1", label="ID Estudiante")
                        reset_btn  = gr.Button("↺  Nueva sesión", elem_classes=["btn-ghost"])
                        gr.HTML('<div style="height:16px"></div>')
                        gr.HTML('<span class="sec-label">Evaluador</span>')
                        eval_mode_dd = gr.Dropdown(
                            choices=["off","fast","full"],
                            value="fast",
                            label="Modo evaluación",
                            info="off=sin eval · fast=rápido · full=embeddings"
                        )
                        retry_chk = gr.Checkbox(
                            value=True,
                            label="Reintento automático si score bajo",
                        )
                        gr.HTML('<div style="height:8px"></div>')
                        gr.HTML('<span class="sec-label">Calidad</span>')
                        quality_box = gr.HTML(value=EMPTY_Q)

                    # Columna central — chat
                    with gr.Column(scale=3):
                        thinking_box = gr.HTML(value="", visible=False)
                        chatbot = gr.Chatbot(
                            label="", height=480,
                            elem_classes=["chat-panel"],
                        )
                        with gr.Row():
                            msg_input = gr.Textbox(
                                placeholder="Escribe tu pregunta…",
                                label="", lines=2, scale=5,
                                show_label=False,
                                elem_id="msg-input",
                            )
                            send_btn = gr.Button(
                                "Enviar", variant="primary", scale=1,
                                elem_classes=["btn-primary"],
                            )

                    # Columna derecha — fuentes
                    with gr.Column(scale=1, min_width=220):
                        gr.HTML('<span class="sec-label">Fuentes</span>')
                        sources_box = gr.HTML(value=EMPTY_SRC)

                history_state = gr.State([])
                debug_state   = gr.State("")

                def on_think(msg):
                    if not msg.strip(): return gr.update(visible=False)
                    return gr.update(value=_thinking_html(), visible=True)

                def on_send(msg, hist, subj, lvl, mode, uid, mt, tp, tpp, rp,
                            topk, eval_mode, do_retry):
                    if not msg.strip():
                        return hist, hist, "", EMPTY_SRC, EMPTY_Q, "", gr.update(visible=False), gr.update(), gr.update()
                    evaluator.set_mode(eval_mode)
                    nh, src, qual, dbg = process_message(
                        msg, hist, llm, rag, evaluator, get_mem(uid),
                        subj, lvl, mode, uid, mt, tp, tpp, rp,
                        topk=int(topk), do_retry=do_retry)
                    return nh, nh, "", src, qual, dbg, gr.update(visible=False), _dash_session(evaluator), _dash_history(evaluator)

                def on_reset(uid):
                    get_mem(uid).reset_session()
                    return [], [], EMPTY_SRC, EMPTY_Q

                reset_btn.click(fn=on_reset, inputs=[user_id_tb],
                                outputs=[chatbot, history_state, sources_box, quality_box])

            # ══════════════════════════════════════════════════════════════════
            # DOCUMENTOS
            # ══════════════════════════════════════════════════════════════════
            with gr.TabItem("Documentos"):
                gr.HTML(
                    '<div style="padding:20px 0 16px">'
                    '<div style="font-family:var(--serif);font-size:20px;font-style:italic;'
                    'color:var(--text-1);margin-bottom:6px">Base de conocimientos</div>'
                    '<div style="font-family:var(--mono);font-size:11px;color:var(--text-3);line-height:1.7">'
                    'Arrastra PDF, TXT o MD · Se indexan automáticamente</div></div>'
                )
                file_upload   = gr.File(label="Subir documentos", file_types=[".pdf",".txt",".md",".docx"], file_count="multiple")
                upload_status = gr.HTML()

                def on_upload(files):
                    if not files:
                        return '<div style="font-family:var(--mono);font-size:11px;color:var(--text-3);padding:8px">Sin archivos.</div>'
                    import shutil
                    from ingester import Ingester
                    kd = sess_dir.parent / "knowledge"
                    kd.mkdir(parents=True, exist_ok=True)
                    n = 0
                    for f in files:
                        src = Path(f.name) if hasattr(f, "name") else Path(str(f))
                        if src.exists():
                            shutil.copy(str(src), str(kd / src.name)); n += 1
                    if not n:
                        return '<div style="font-family:var(--mono);font-size:11px;color:var(--red-warm);padding:8px">Error copiando archivos.</div>'
                    Ingester(know_dir=kd, db_dir=sess_dir.parent/"database").run()
                    rag.reload()
                    return f'<div style="font-family:var(--mono);font-size:11px;color:var(--green-sage);padding:8px">✓ {n} archivo(s) indexado(s).</div>'

                file_upload.change(fn=on_upload, inputs=[file_upload], outputs=[upload_status])

            # ══════════════════════════════════════════════════════════════════
            # MODELO
            # ══════════════════════════════════════════════════════════════════
            with gr.TabItem("Modelo"):
                with gr.Row():
                    with gr.Column():
                        gr.HTML('<span class="sec-label">Parámetros de generación</span>')
                        temp_sl = gr.Slider(0.0, 2.0, value=0.4, step=0.05, label="Temperature")
                        gr.HTML('<div class="param-note">0 = deterministico · 1.5+ = muy creativo · Recomendado: 0.3–0.6</div>')
                        top_p_sl = gr.Slider(0.1, 1.0, value=0.9, step=0.05, label="Top-P")
                        gr.HTML('<div class="param-note">Vocabulario por probabilidad acumulada · 0.9 ideal para tutoria</div>')
                        rep_sl = gr.Slider(1.0, 2.0, value=1.1, step=0.05, label="Repeat Penalty")
                        gr.HTML('<div class="param-note">Penaliza repeticion de tokens · >1.3 reduce loops</div>')
                        tok_sl = gr.Slider(64, 1024, value=512, step=64, label="Max Tokens")
                        gr.HTML('<div class="param-note">Longitud maxima de respuesta · 512 suficiente para 3B</div>')

                    with gr.Column():
                        gr.HTML('<span class="sec-label">Recuperación RAG</span>')
                        topk_sl = gr.Slider(1, 10, value=5, step=1, label="Top-K chunks")
                        gr.HTML('<div class="param-note">Fragmentos a recuperar · 5 optimo para 3B · mas = mas lento</div>')
                        gr.HTML('<div style="height:20px"></div>')
                        gr.HTML('<span class="sec-label">Sistema</span>')

                        def sys_stat():
                            try:
                                import psutil; r = psutil.virtual_memory()
                                ru = f"{r.used/1024**3:.1f}"; rt = f"{r.total/1024**3:.1f}"; rp = f"{r.percent:.0f}"
                            except: ru = rt = rp = "—"
                            _short = (model_name[:16] + "…") if len(model_name) > 17 else (model_name or "ON")
                            return (f'<div class="stat-grid">'
                                    f'<div class="stat-cell"><div class="stat-val" style="color:var(--gold)">{ru}</div><div class="stat-lbl">GB Usados</div></div>'
                                    f'<div class="stat-cell"><div class="stat-val" style="color:var(--text-2)">{rt}</div><div class="stat-lbl">GB Total</div></div>'
                                    f'<div class="stat-cell"><div class="stat-val" style="color:var(--teal)">{rp}%</div><div class="stat-lbl">RAM %</div></div>'
                                    f'<div class="stat-cell"><div class="stat-val" style="color:var(--green-sage);font-size:11px">{_short}</div><div class="stat-lbl">Modelo activo</div></div>'
                                    f'</div>')

                        stat_html = gr.HTML(value=sys_stat())
                        gr.Button("↻  Actualizar", elem_classes=["btn-ghost"]).click(fn=sys_stat, outputs=[stat_html])

                        gr.HTML('<div style="height:16px"></div>')
                        gr.HTML(
                            '<div style="background:var(--surface);border:1px solid var(--border);'
                            'border-radius:var(--r);padding:14px">'
                            '<div style="font-family:var(--mono);font-size:9px;letter-spacing:2px;'
                            'text-transform:uppercase;color:var(--text-3);margin-bottom:8px">Aplicación de cambios</div>'
                            '<div style="font-family:var(--mono);font-size:11px;color:var(--text-2);line-height:1.7">'
                            'Los cambios se aplican en el <span style="color:var(--gold)">siguiente mensaje</span>.<br>'
                            'No requieren reiniciar el sistema.</div></div>'
                        )

            # ══════════════════════════════════════════════════════════════════
            # DASHBOARD
            # ══════════════════════════════════════════════════════════════════
            with gr.TabItem("Dashboard"):
                with gr.Row():
                    with gr.Column():
                        gr.HTML('<span class="sec-label">Sesión actual</span>')
                        sess_html = gr.HTML()
                        gr.Button("↻  Actualizar", elem_classes=["btn-ghost"]).click(
                            fn=lambda: _dash_session(evaluator), outputs=[sess_html])

                    with gr.Column():
                        gr.HTML('<span class="sec-label">Historial</span>')
                        hist_html = gr.HTML()
                        gr.Button("↻  Cargar", elem_classes=["btn-ghost"]).click(
                            fn=lambda: _dash_history(evaluator), outputs=[hist_html])

        # ── Conectar sliders ──────────────────────────────────────────────────
        for trigger in [send_btn.click, msg_input.submit]:
            trigger(
                fn=on_think, inputs=[msg_input], outputs=[thinking_box]
            ).then(
                fn=on_send,
                inputs=[msg_input, history_state, subject_dd, level_dd,
                        mode_dd, user_id_tb, tok_sl, temp_sl, top_p_sl, rep_sl,
                        topk_sl, eval_mode_dd, retry_chk],
                outputs=[chatbot, history_state, msg_input,
                         sources_box, quality_box, debug_state, thinking_box,
                         sess_html, hist_html],
            )

    app.launch(server_name="127.0.0.1", server_port=7860,
               share=False, inbrowser=True, show_error=True, css=CUSTOM_CSS)