# VoiceBuddy

A CPU-only Turkish desktop voice assistant for Windows, written in plain, readable Python.

> **Status: work in progress.** This is a from-scratch rewrite of a 2023 project.
> Right now it understands spoken commands and can open apps and websites, greet you and shut itself down.
> More skills, a wake word and chat are next. See the [roadmap](PLAN.md).

## What works today

| Stage | File | How |
|---|---|---|
| Record until you stop talking | `voicebuddy/audio.py` | `sounddevice` + a loudness (RMS) threshold |
| Speech to text (offline) | `voicebuddy/stt.py` | `faster-whisper`, `base` model, int8 on CPU |
| Intent recognition (offline) | `voicebuddy/intent.py` | TF-IDF on character n-grams + logistic regression, with a confidence threshold |
| Skills | `voicebuddy/skills.py` | A dictionary of plain functions: open an app or site, greet, quit |
| Text to speech (online) | `voicebuddy/tts.py` | `edge-tts`, Turkish neural voice |
| Wake word (offline) | `voicebuddy/trigger.py` | `vosk`, small Turkish model; or the F9 hotkey instead |
| Main loop | `main.py` | wake word or F9 → speak → command runs → spoken answer |

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

For the wake word, download `vosk-model-small-tr-0.3` from the [Vosk models page](https://alphacephei.com/vosk/models)
and unzip it so that the files are in `models/vosk-tr/`. With `mode = "hotkey"` in `config.toml` this is not needed.

## Usage

```
python main.py
```

Say "pusula", wait for `Listening...`, say a command in Turkish and stop talking.
To use a key instead, set `mode = "hotkey"` in `config.toml` and press F9 (it works even when another window is in front).
For example "YouTube'u aç", "hesap makinesini aç" or "merhaba". Say "kapan" or press Ctrl+C to quit.

Each part can also be tried on its own:

```
python -m voicebuddy.tts "merhaba"
python -m voicebuddy.audio
python -m voicebuddy.stt recording.wav
python -m voicebuddy.intent "youtube'u aç"
python -m voicebuddy.trigger pusula
```

## Roadmap

More skills (time and date, timer, weather), a hotkey and a wake word, and optional LLM chat. The full plan, with the reasons behind each technology choice, is in [PLAN.md](PLAN.md) (in Turkish).

## License

[MIT](LICENSE)
