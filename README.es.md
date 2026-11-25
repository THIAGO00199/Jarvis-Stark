# Jarvis Stark — Panel local de voz y asistente

Un puente ligero para un asistente local, con panel en el navegador, salida de voz opcional y un modelo Ollama local. El prototipo está diseñado para escuchar y responder en el mismo equipo.

## Funciones

- Servidor HTTP en Python con un pequeño panel HTML.
- Generación local con Ollama mediante `127.0.0.1:11434`.
- Síntesis de voz opcional con Kokoro y alternativa espeak-ng.
- Búsqueda web opcional para consultas que necesitan información actual.
- Endpoints locales de estado y control.
- Se enlaza a `127.0.0.1:8765`, sin exponer el panel a la red local.

## Ejecución

Requisitos: Python 3.10+ y un servicio local Ollama con un modelo compatible. Las funciones opcionales de voz y búsqueda requieren sus paquetes de Python y programas correspondientes.

```bash
python3 jarvis_bridge.py
```

Abre http://127.0.0.1:8765 en el mismo equipo.

La configuración está disponible mediante variables de entorno como `JARVIS_MODEL` y `JARVIS_CLAP_THRESH`. Nunca incluyas credenciales locales ni recursos privados de modelos en Git.

## Estado del proyecto

Es un prototipo local. La disponibilidad del modelo, los paquetes de voz, los dispositivos de audio y la búsqueda en red determinan qué funciones opcionales están disponibles en cada equipo. El audio de introducción opcional debe ser proporcionado localmente por el usuario y no se incluye en este repositorio.

---

[Português](./README.md) · [English](./README.en.md)
