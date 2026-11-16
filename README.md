# VoiceBuddy

A CPU-only Turkish desktop voice assistant for Windows, written in plain, readable Python.

> **Status: work in progress.** This is a from-scratch rewrite of a 2023 project.
> Right now it is a "parrot": it listens, turns your speech into text and says it back.
> Commands, a wake word and chat are next. See the [roadmap](PLAN.md).

## What works today

| Stage | File | How |
|---|---|---|
| Record until you stop talking | `voicebuddy/audio.py` | `sounddevice` + a loudness (RMS) threshold |
| Speech to text (offline) | `voicebuddy/stt.py` | `faster-whisper`, `base` model, int8 on CPU |
| Text to speech (online) | `voicebuddy/tts.py` | `edge-tts`, Turkish neural voice |
| Main loop | `main.py` | Enter → speak → hear it repeated |

Speech recognition runs on your own machine. The spoken answer needs an internet connection.

## Measured, not guessed

Whisper model choice, measured on a Ryzen 5 7530U laptop (no GPU) with five short Turkish commands in my own voice:

| Model | Average time | Correct words |
|---|---|---|
| `base` | 1.20 s | 11/14 |
| `small` | 3.85 s | 11/14 |

Same accuracy, `base` is about three times faster, so `base` is used.
You can repeat the measurement with `python -m scripts.benchmark_stt`.

## Setup

Requires Windows and Python 3.12.

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

The first run downloads the Whisper `base` model.

## Usage

```
python main.py
```

Press Enter, wait for `Listening...`, say a sentence in Turkish and stop talking.
The text appears on screen and is spoken back. Press Ctrl+C to quit.

Each part can also be tried on its own:

```
python -m voicebuddy.tts "merhaba"
python -m voicebuddy.audio
python -m voicebuddy.stt recording.wav
```

## Roadmap

Intent recognition (TF-IDF + logistic regression), skills (open apps and sites, time and date, timer, weather), a hotkey and a wake word, and optional LLM chat. The full plan, with the reasons behind each technology choice, is in [PLAN.md](PLAN.md) (in Turkish).

## License

[MIT](LICENSE)
