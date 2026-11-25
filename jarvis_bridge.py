#!/usr/bin/env python3
"""Jarvis Stark - painel local, Ollama, gestos e voz. Apenas localhost."""
import json
import logging
import os
import queue
import re
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
AUDIO = ROOT / "assets" / "should_i_stay_should_i_go.mp3"
HOST, PORT = "127.0.0.1", 8765
MODEL = os.getenv("JARVIS_MODEL", "qwen3.5:2b")
CLAP_THRESH = float(os.getenv("JARVIS_CLAP_THRESH", ".13"))
STATE = {"status": "Pronto para iniciar", "microphone": "Aguardando", "query": "", "answer": "", "sources": [], "listening": True, "music": AUDIO.is_file()}
LOCK = threading.Lock()
VOICE_LOCK = threading.Lock()
LOGGER = logging.getLogger("jarvis")

def update(**kw):
    with LOCK:
        STATE.update(kw)

def status():
    with LOCK:
        return dict(STATE)

def speak(text):
    """Voz masculina brasileira similar em estilo ao mordomo futurista (sem clonagem)."""
    def worker():
        with VOICE_LOCK:
            try:
                from kokoro import KPipeline
                import numpy as np
                import soundfile as sf
                import tempfile
                # pm_alex é a voz masculina disponível para português
                if not hasattr(speak, "pipe"):
                    speak.pipe = KPipeline(lang_code="p")
                samples = []
                for _, _, a in speak.pipe(text[:380], voice="pm_alex", speed=1.06):
                    samples.append(a)
                if samples:
                    with tempfile.NamedTemporaryFile(suffix=".wav") as f:
                        sf.write(f.name, np.concatenate(samples), 24000)
                        subprocess.run(["mpv", "--no-video", "--really-quiet", f.name], timeout=70, check=False)
                        return
            except Exception as exc:
                LOGGER.warning("Kokoro indisponível (%s); tentando voz local simples", exc)
            if shutil.which("espeak-ng"):
                try:
                    subprocess.run(["espeak-ng", "-v", "pt-br+m3", "-s", "150", text[:300]], timeout=35, check=False)
                except Exception:
                    pass
    threading.Thread(target=worker, daemon=True).start()

def music_intro():
    if not AUDIO.is_file():
        update(status="Falta copiar should_i_stay_should_i_go.mp3 para assets/")
        return False
    # Apenas reprodução pessoal, não altera ou gera cópia do áudio original.
    try:
        subprocess.Popen(["mpv", "--really-quiet", "--no-video", "--start=0", "--length=25", str(AUDIO)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        update(status="PROTOCOLO STARK · reproduzindo 25 segundos")
        return True
    except Exception as exc:
        update(status=f"Falha ao tocar áudio: {exc}")
        return False

def search_web(question):
    if not any(k in question.lower() for k in ("agora", "hoje", "atual", "2026", "notícia", "noticias", "investim", "cotação", "preço", "pesquis", "buscar", "procure", "pesquise", "melhor")):
        return []
    try:
        from ddgs import DDGS
        data = DDGS(timeout=9).text(question, max_results=5)
        return [{"title": str(x.get("title", ""))[:180], "url": str(x.get("href", "")), "body": str(x.get("body", ""))[:420]}
                for x in data if str(x.get("href", "")).startswith("https://")][:5]
    except Exception as exc:
        LOGGER.warning("Pesquisa externa indisponível: %s", exc)
        return []

def ask(question):
    question = (question or "").strip()[:900]
    if not question:
        return {"answer": "Diga ou digite uma pergunta.", "sources": []}
    if "protocolo stark" in question.lower() or "tocar abertura" in question.lower():
        ok = music_intro()
        answer = "Iniciando protocolo Stark. Abertura musical em execução." if ok else "O arquivo de música ainda não está na pasta assets. Coloque o MP3 e tente novamente."
        update(query=question, answer=answer, sources=[])
        return {"answer": answer, "sources": []}
    update(status="Pesquisando / processando...", query=question)
    sources = search_web(question)
    context = "\n".join(f"Fonte {i + 1}: {s['title']} — {s['body']} ({s['url']})" for i, s in enumerate(sources))
    instruction = ("Você é JARVIS, um assistente inteligente e formal inspirado em um mordomo tecnológico. "
                   "Responda em português do Brasil, objetivamente. Não finja que realizou ações. "
                   "Para assuntos atuais, baseie-se nas fontes fornecidas, diga quando faltarem dados e não invente cotações. "
                   "Em finanças, explique riscos, liquidez e perfil sem recomendar compra específica ao usuário. ")
    prompt = f"{instruction}\n\nFontes recuperadas (podem estar incompletas):\n{context or 'Nenhuma fonte atual disponível.'}\n\nUsuário: {question}\nJARVIS:"
    payload = {"model": MODEL, "prompt": prompt, "stream": False, "options": {"num_predict": 300, "temperature": 0.45}}
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/generate",
                                     data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=150) as resp:
            answer = str(json.load(resp).get("response", "")).strip()
        if not answer:
            answer = "O modelo retornou uma resposta vazia."
    except Exception as exc:
        answer = f"Não consegui consultar o modelo local ({type(exc).__name__}). Verifique Ollama e o modelo {MODEL}."
    if "investim" in question.lower() and not sources:
        answer += "\n\nNão consegui confirmar taxas e condições atuais pela pesquisa web."
    update(status="Pronto", query=question, answer=answer, sources=sources)
    return {"answer": answer, "sources": sources}

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass
    def reply(self, payload, code=200):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            data = (ROOT / "panel.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif self.path == "/api/status":
            self.reply(status())
        else:
            self.send_error(404)
    def do_POST(self):
        if self.path not in ("/api/ask", "/api/intro", "/api/listening"):
            self.send_error(404)
            return
        try:
            n = int(self.headers.get("Content-Length", "0"))
            if n > 4000: self.reply({"error": "Requisição muito grande"}, 413); return
            obj = json.loads(self.rfile.read(n) or b"{}")
            if self.path == "/api/intro": self.reply({"ok": music_intro()})
            elif self.path == "/api/listening":
                update(listening=bool(obj.get("enabled", False)))
                self.reply(status())
            else: self.reply(ask(str(obj.get("question", ""))))
        except Exception as exc:
            self.reply({"error": str(exc)}, 500)

def record_speech():
    import sounddevice as sd
    import numpy as np
    sr = 16000
    update(microphone="Ouvindo comando por 7 segundos", status="Comando por voz · fale agora")
    print("[JARVIS] Fale agora (7 s)...", flush=True)
    samples = sd.rec(int(sr * 7), samplerate=sr, channels=1, dtype="float32")
    sd.wait()
    audio = np.squeeze(samples)
    if float(np.max(np.abs(audio))) < .012:
        update(status="Não ouvi fala suficiente", microphone="Monitorando palmas")
        return
    update(status="Transcrevendo sua fala...")
    from faster_whisper import WhisperModel
    if not hasattr(record_speech, "model"):
        record_speech.model = WhisperModel("tiny", device="cpu", compute_type="int8")
    segments, _ = record_speech.model.transcribe(audio, language="pt", vad_filter=True, beam_size=2)
    heard = " ".join(x.text.strip() for x in segments).strip()
    if heard:
        print("[JARVIS] Ouvi:", heard, flush=True)
        output = ask(heard)
        if "protocolo stark" not in heard.lower():
            speak(output["answer"][:250])
    else:
        update(status="Não reconheci a frase.")
    update(microphone="Monitorando palmas")

def monitor_claps():
    try:
        import sounddevice as sd
        import numpy as np
        update(microphone="Monitorando palmas", status="Microfone ligado · duas palmas para falar")
        print("[JARVIS] Monitorando 2 palmas (ajuste JARVIS_CLAP_THRESH para sensibilidade).", flush=True)
        while True:
            if not status()["listening"]:
                update(microphone="Desligado pelo usuário")
                time.sleep(.3)
                continue
            q = queue.Queue(maxsize=100)
            def callback(indata, frames, t, err):
                try: q.put_nowait(float(np.sqrt(np.mean(indata[:, 0] ** 2))))
                except queue.Full: pass
            with sd.InputStream(samplerate=16000, channels=1, blocksize=512, callback=callback):
                first = 0
                peak = False
                while status()["listening"]:
                    try: rms = q.get(timeout=1.0)
                    except queue.Empty: continue
                    now = time.monotonic()
                    active = rms > CLAP_THRESH
                    if active and not peak:
                        if .17 <= now - first <= 1.3:
                            break
                        first = now
                    peak = active
                    if now - first > 1.3: first = 0
            if not status()["listening"]:
                continue
            print("[JARVIS] Duas palmas detectadas!", flush=True)
            try: record_speech()
            except Exception as exc:
                LOGGER.error("Comando de voz: %s", exc)
                update(status=f"Erro de voz: {exc}", microphone="Monitorando palmas")
            time.sleep(.8)
    except Exception as exc:
        LOGGER.error("Microfone indisponível: %s", exc)
        update(microphone="Indisponível", status="Use a caixa de texto; microfone indisponível")

def open_panel():
    url = f"http://{HOST}:{PORT}"
    browser = next((shutil.which(x) for x in ("chromium", "google-chrome-stable", "brave", "firefox") if shutil.which(x)), None)
    try:
        if browser and any(s in browser for s in ("chromium", "chrome", "brave")):
            subprocess.Popen([browser, f"--app={url}", "--window-size=1050,800", "--new-window"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            webbrowser.open(url)
    except Exception as exc:
        LOGGER.warning("Abra %s manualmente: %s", url, exc)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    threading.Thread(target=monitor_claps, daemon=True).start()
    threading.Timer(1.4, open_panel).start()
    print(f"[JARVIS] Painel local: http://{HOST}:{PORT}")
    print(f"[JARVIS] Arquivo de música: {AUDIO}")
    try: httpd.serve_forever()
    except KeyboardInterrupt: pass
    finally: httpd.server_close()
