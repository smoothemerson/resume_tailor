# Resume Tailor

A CLI tool that reads a LaTeX resume and uses a local Ollama LLM to tailor it to a job description.

## Usage

```bash
resume-tailor [--model MODEL] [--resume PATH] [--output-dir DIR]
```

Paste the job description when prompted, then type `END` on its own line to submit.

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) running locally at `http://localhost:11434`
- A base LaTeX resume at the configured path

## Install

```bash
uv tool install .
```
