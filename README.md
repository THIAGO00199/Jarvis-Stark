# Jarvis Stark — Painel local de voz e assistente

Ponte leve para um assistente local, com painel no navegador, fala opcional e um modelo Ollama executado na própria máquina. O protótipo foi pensado para ouvir e responder localmente.

## Funcionalidades

- Servidor HTTP em Python com um painel HTML.
- Geração local com Ollama em `127.0.0.1:11434`.
- Síntese de voz opcional com Kokoro e alternativa por espeak-ng.
- Pesquisa web opcional para perguntas que precisam de informações atuais.
- Endpoints locais de estado e controle.
- Escuta em `127.0.0.1:8765`, sem expor o painel à rede local.

## Executar

Requisitos: Python 3.10+ e Ollama local com um modelo compatível. Recursos opcionais de voz e pesquisa exigem os respectivos pacotes Python e programas do sistema.

```bash
python3 jarvis_bridge.py
```

Abra http://127.0.0.1:8765 no próprio computador.

A configuração pode ser feita por variáveis de ambiente como `JARVIS_MODEL` e `JARVIS_CLAP_THRESH`. Não envie credenciais locais nem arquivos privados de modelos ao Git.

## Estado do projeto

É um protótipo local. A disponibilidade do modelo, pacotes de voz, dispositivos de áudio e pesquisa em rede determina quais recursos opcionais funcionam em cada máquina. O áudio de abertura opcional deve ser fornecido localmente pelo usuário e não está incluído neste repositório.

---

[Português](./README.md) · [English](./README.en.md) · [Español](./README.es.md)
