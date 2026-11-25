# Jarvis Stark — Local Voice and Assistant Panel

A lightweight local assistant bridge with a browser panel, optional speech output, and a local Ollama model. The prototype is designed to listen and respond on the same machine.

## Features

- Python HTTP server with a small HTML control panel.
- Local Ollama generation through `127.0.0.1:11434`.
- Optional speech synthesis using Kokoro, with an espeak-ng fallback.
- Optional web search for queries that explicitly need current information.
- State and status endpoints for the local panel.
- Binds to `127.0.0.1:8765` rather than exposing the panel to the LAN.

## Run

Requirements: Python 3.10+ and a local Ollama service with a compatible model. Optional speech/search capabilities need their corresponding local Python packages and system programs.

```bash
python3 jarvis_bridge.py
```

Open http://127.0.0.1:8765 on the same computer.

Configuration is available through environment variables such as `JARVIS_MODEL` and `JARVIS_CLAP_THRESH`. Never commit local credentials or private model assets.

## Project status

This is a local prototype. Model availability, speech packages, audio devices, and network search determine which optional features work on a particular machine. The optional intro audio is a user-supplied local asset and is not included in this repository.

---

[Português](./README.md) · [Español](./README.es.md)
