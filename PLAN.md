# VoiceBuddy v2 — Plan

## Context

VoiceBuddy v1 (2023) birbirinden kopuk iki programdı: `myasist` (Vosk + scikit-learn ile Türkçe komut asistanı) ve `GPT` (ayrı bir exe olarak başlatılan sohbet). v1'in temel sorunları: koda gömülü API anahtarları, `exec` ile fonksiyon çağırma, güven eşiği olmayan intent modeli, asistanın kendi sesini duyması, sabit dosya yolları ve bugün artık çalışmayan OpenAI çağrısı.

v2 sıfırdan yazılacak ve GitHub portfolyosunun ana projesi olacak. Hedef: tek bir uygulama, basit ve her satırı açıklanabilir kod, sadece CPU (Ryzen 5 7530U, 24 GB RAM, ekran kartı yok), Windows 11, Python 3.12.

**Verilen kararlar**
- Tetikleme: hem uyandırma kelimesi hem bas-konuş tuşu (ayardan seçilir).
- LLM sohbet: bulut API, opsiyonel.
- Sesli cevap: online doğal ses.
- İlk sürüm yetenekleri: uygulama/site açma, saat-tarih-zamanlayıcı, hava durumu.

**Varsayımlar**
- Arayüz yalnızca terminal.
- Kod içi isimler ve yorumlar İngilizce; sohbetteki açıklamalar Türkçe.
- README İngilizce (`README.md`) + Türkçe kopya (`README.tr.md`).
- Bas-konuş: tuşa bir kez basarsın, konuşursun, susunca kayıt kendisi biter (basılı tutmak gerekmez). Böylece iki tetikleme modu aynı kayıt fonksiyonunu kullanır.
- Namaz vakitleri/kıble ve Steam ilk sürümde yok (seçmedin); sonradan `intents.json`'a bir satır eklemekle gelir.

---

## 1. Mimari

Tek bir döngü, her aşama tek bir dosya ve tek bir ana fonksiyon:

```
 TETİKLEME            KAYIT                  YAZIYA ÇEVİRME        INTENT
 trigger.py    →      audio.py        →      stt.py         →      intent.py
 uyandırma kelimesi   sessizlik olana        faster-whisper        TF-IDF + LogReg
 ya da kısayol        kadar kaydet           metin döner           (intent, güven) döner
                                                                        │
                        ┌───────────────────────────────────────────────┤
                        │ güven ≥ eşik                                  │ güven < eşik
                        ▼                                               ▼
                   skills.py                                       chat.py (opsiyonel)
                   SKILLS sözlüğünden fonksiyon                    LLM'e sor; kapalıysa
                   çağrılır, cevap metni döner                     "Bunu anlamadım"
                        │                                               │
                        └──────────────────────┬────────────────────────┘
                                               ▼
                                            tts.py  →  hoparlör  →  başa dön
```

`main.py` içindeki döngü kabaca şu kadar olacak:

```python
while True:
    reason = wait_for_trigger()        # trigger.py -> "user" ya da "timer"
    if reason == "timer":
        speak("Süre doldu")            # yalnızca ana döngü konuşur
        continue
    audio = record_until_silence()     # audio.py
    text = transcribe(audio)           # stt.py
    intent, confidence = predict(text) # intent.py
    if confidence >= THRESHOLD:
        answer = SKILLS[intent.skill](intent, text)   # skills.py
    else:
        answer = ask_llm(text)         # chat.py (kapalıysa sabit cevap)
    speak(answer)                      # tts.py
```

**Bu tasarımın v1 sorunlarını nasıl çözdüğü**
- *Kendini duyma:* döngü sıralı; asistan konuşurken mikrofon akışı kapalı. Ayrıca cevap metinlerinde uyandırma kelimesi geçmeyecek.
- *`exec`:* yerine `SKILLS = {"open": open_target, "time": tell_time, ...}` sözlüğü.
- *Güven eşiği:* `predict_proba` en yüksek olasılığı verir; eşik altı komut çalıştırmaz.
- *Sabit yollar ve gömülü anahtarlar:* ayarlar `config.toml`'da, anahtarlar `.env`'de (git'e girmez).
- *Test edilebilirlik:* her yetenek cevabı **metin olarak döndürür**, kendisi konuşmaz. Böylece mikrofon/hoparlör olmadan pytest ile test edilir.

**Zamanlayıcı çakışması nasıl önleniyor**
- Zamanlayıcı için ayrı thread yok. `set_timer` yalnızca bitiş zamanını bir listeye yazar.
- Mikrofonu ve hoparlörü yalnızca ana döngü kullanır. Bu yüzden zamanlayıcı kayıtla ya da başka bir cevapla çakışamaz; kilit (lock) da gerekmez.
- `wait_for_trigger()` beklerken yaklaşık 0,1 sn'de bir "süresi dolan zamanlayıcı var mı?" diye bakar. Varsa `"timer"` döndürür ve ana döngü "Süre doldu" der.
- Süre kayıt, yazıya çevirme ya da cevap sırasında dolarsa bildirim o tur bitince söylenir (en fazla birkaç saniye gecikir).

---

## 2. Teknoloji seçenekleri ve öneriler

### Konuşma tanıma (STT)
| Seçenek | Artı | Eksi |
|---|---|---|
| **Vosk** `small-tr` | Çok hafif, akış halinde (kelime kelime) çalışır, v1'de modeli zaten var | Serbest cümlelerde Türkçe doğruluğu düşük; LLM sohbeti için yetersiz |
| **faster-whisper** (`base`/`small`, int8) | Türkçe doğruluğu belirgin şekilde daha iyi, noktalama koyar, CPU için optimize | Akış halinde değil (cümle bitince çevirir); model daha büyük, kısa komutta tahminen 1–3 sn |
| whisper.cpp | CPU'da hızlı | Python tarafı daha zahmetli |

**Öneri: ikisi birlikte, ayrı işlerde.** Komutu yazıya çevirmek için **faster-whisper**; uyandırma kelimesini sürekli dinlemek için **Vosk**. `base` mi `small` mı sorusunu tahminle değil, Adım 3'te kendi laptopunda ölçerek seçeceğiz (bu ölçüm README'ye de girer).

### Uyandırma kelimesi
| Seçenek | Artı | Eksi |
|---|---|---|
| **Vosk + kısıtlı sözlük** (`KaldiRecognizer(model, rate, '["<kelime>", "[unk]"]')`) | Ek model yok, Türkçe kelime serbestçe seçilir, v1 modeli (`HCLr.fst`/`Gr.fst` var) bunu destekler | Kısa kelimelerde yanlış tetiklenme olabilir |
| openWakeWord | Bu iş için tasarlanmış | Hazır Türkçe model yok, kendi modelini eğitmek gerekir |
| Porcupine | Çok isabetli | Hesap/erişim anahtarı ve lisans kısıtı |

**Öneri: Vosk + kısıtlı sözlük.** Kelime `config.toml`'dan okunur.

**Seçilen kelime: "pusula"** (yedek: "kaptan"). v1'deki "kral" bırakıldı: tek heceli ve günlük konuşmada geçtiği için yanlış tetiklenmeye açıktı. Kısıtlı sözlük yalnızca modelin tanıdığı kelimelerle çalışır; "pusula"nın modelde olup olmadığı Adım 12'de denenecek, yoksa yedeğe geçilecek.

### Bas-konuş kısayolu
`keyboard` kütüphanesi (`keyboard.wait("f9")`, tek satır) ya da `pynput` (daha bakımlı ama callback gerektirir). **Öneri: `keyboard`**; kurulumda sorun çıkarsa `pynput`.

### Kayıt sonu tespiti
| Seçenek | Artı | Eksi |
|---|---|---|
| **Ses seviyesi (RMS) eşiği** | 10 satır numpy, tamamen açıklanabilir | Gürültülü ortamda eşik ayarı gerekir |
| webrtcvad / Silero VAD | Daha isabetli | Ek bağımlılık, kara kutu |

**Öneri: RMS eşiği** (~1 sn sessizlik ya da en fazla ~10 sn). Yetersiz kalırsa sonradan VAD'e geçilir.

### Intent (niyet) tanıma
| Seçenek | Artı | Eksi |
|---|---|---|
| Anahtar kelime kuralları | En basit | Farklı söyleyişlere dayanıksız, ML hikâyesi yok |
| **TF-IDF (karakter n-gram) + LogisticRegression** | v1'in fikri, küçük ve hızlı; karakter n-gram Türkçe ekleri tolere eder ("youtube'u", "youtubu"); `predict_proba` ile güven eşiği; mülakatta anlatması kolay | Örnek cümle sayısına bağlı |
| Cümle gömmeleri (sentence-transformers) | Anlamca yakın cümleleri yakalar | PyTorch bağımlılığı, ağır, açıklaması zor |
| LLM ile fonksiyon çağırma | En esnek | İnternet + ücret; çekirdek offline olmaz |

**Öneri: TF-IDF + LogisticRegression.** v1'deki `words.py` örnekleri `data/intents.json`'a taşınır. Ayrı bir test cümlesi setiyle doğruluk ölçülür.

### Sesli cevap (TTS) — online seçtin
| Seçenek | Artı | Eksi |
|---|---|---|
| **edge-tts** | Ücretsiz, anahtar yok, çok doğal Türkçe sesler (Emel/Ahmet) | Microsoft'un resmi olmayan kullanımı; bir gün bozulabilir |
| gTTS (v1) | Basit | Ses daha yapay, yine resmi değil |
| Azure Speech | Resmi, aynı sesler, ücretsiz kota | Hesap + anahtar kurulumu |
| ElevenLabs / OpenAI TTS | En iyi kalite | Ücretli |

**Öneri: edge-tts.** Tek fonksiyon `speak(text)` arkasında durur; motor değişirse yalnızca `tts.py` değişir. İnternet yoksa cevap terminale yazılır. README'de dürüstçe belirtilir: *STT ve intent offline, TTS ve LLM online.*

### LLM sohbet (opsiyonel, bulut)
| Seçenek | Not |
|---|---|
| **Claude API** (`claude-haiku-5-5`, `anthropic` paketi) | Hızlı ve ucuz sınıf; sesli cevap için ideal |
| OpenAI API | Benzer |
| Gemini API | Ücretsiz kotası var |

**Öneri: Claude Haiku.** `.env`'de anahtar yoksa özellik kendiliğinden kapalı. Son ~10 mesaj listede tutulur (sohbet hafızası), sistem mesajı "kısa, konuşma diliyle Türkçe cevap ver" der. Güncel fiyat ve API ayrıntılarını o adımda resmi dokümandan kontrol edeceğim.

### Diğer
- **Ses giriş/çıkış:** `sounddevice` (v1'de de vardı) + `soundfile` (MP3 okumak için).
- **Hava durumu:** **Open-Meteo** — anahtar gerektirmez, repoyu klonlayan herkes çalıştırabilir (v1'deki OpenWeatherMap anahtar istiyordu). Şehir/koordinat `config.toml`'dan.
- **Ayarlar:** `config.toml` (Python'un kendi `tomllib` modülü, ek paket yok) + `.env` (`python-dotenv`).
- **Uygulama açma:** `os.startfile` / `webbrowser`; hedefler `intents.json`'da, koda gömülü yol yok.
- **Zamanlayıcı:** thread yok; bitiş zamanları bir listede tutulur ve ana döngü kontrol eder (bkz. Mimari). Süreyi rakamdan ya da Türkçe sayı kelimesinden ("beş dakika") ayıklayan küçük bir fonksiyon.
- **Test:** `pytest`.

---

## 3. Klasör yapısı

```
voicebuddy/
├─ README.md / README.tr.md
├─ PLAN.md
├─ LICENSE
├─ requirements.txt
├─ .gitignore              # .venv, .env, models/, __pycache__, VoiceBuddy.v1/
├─ .env.example            # ANTHROPIC_API_KEY=
├─ config.toml             # tetikleme modu, uyandırma kelimesi, kısayol, şehir, ses, eşik
├─ main.py                 # ana döngü
├─ voicebuddy/
│  ├─ __init__.py
│  ├─ config.py            # config.toml + .env okur
│  ├─ audio.py             # record_until_silence(), play()
│  ├─ trigger.py           # wait_for_wake_word(), wait_for_hotkey()
│  ├─ stt.py               # transcribe(audio) -> str
│  ├─ intent.py            # train(), predict(text) -> (intent, güven)
│  ├─ skills.py            # yetenek fonksiyonları + SKILLS sözlüğü
│  ├─ chat.py              # ask_llm(text) -> str
│  └─ tts.py               # speak(text)
├─ data/
│  ├─ intents.json         # intent: örnek cümleler, cevaplar, skill, hedef
│  └─ intents_test.json    # değerlendirme için ayrı cümleler
├─ models/                 # Vosk modeli (git'e girmez; v1'deki model_small_tr kopyalanır)
├─ scripts/
│  ├─ benchmark_stt.py     # whisper base/small süre ölçümü
│  └─ evaluate_intents.py  # doğruluk + karışıklık matrisi
├─ tests/                  # test_intent.py, test_skills.py, test_config.py
└─ docs/                   # demo videosu/GIF, ekran görüntüleri
```

Her modülün sonunda küçük bir `if __name__ == "__main__":` denemesi olur (ör. `python -m voicebuddy.tts "merhaba"`), böylece her parça tek başına denenir.

**v1 klasörü:** `VoiceBuddy.v1/` içinde yüzlerce MB exe çıktısı var. `.gitignore`'a eklenecek ve **asla commit edilmeyecek**. Hikâyesi README'de "v1'den v2'ye" bölümünde anlatılır.

---

## 4. Yol haritası

Her adım tek oturumluk; sonunda çalışan ve denenebilen bir şey kalır. Adım 2–10 arasında tetikleme olarak terminalde Enter kullanılır; gerçek tetikleme 11–12'de eklenir.

| # | Adım | Doğrulama |
|---|---|---|
| 0 | **Hazırlık:** `git init`, `.gitignore`, `.venv`, `requirements.txt`, boş klasör iskeleti, bu planı `PLAN.md`'ye yaz. | `git status` içinde `VoiceBuddy.v1/` görünmüyor |
| 1 | **TTS:** `tts.speak()` (edge-tts → MP3 → sounddevice) | `python -m voicebuddy.tts "merhaba"` sesli okur |
| 2 | **Kayıt:** `audio.record_until_silence()` | Konuş, sus; kayıt kendisi biter, wav'ı dinle |
| 3 | **STT:** `stt.transcribe()` + `scripts/benchmark_stt.py` | 5 örnek cümlede `base` ve `small` süresi/doğruluğu tabloya yazılır, model seçilir |
| 4 | **Papağan (ilk uçtan uca):** `main.py` — Enter → konuş → duyduğunu sesli tekrar et. Ardından kısa bir README taslağı + LICENSE, GitHub'da repo oluşturma ve **ilk push** | Söylediğin cümleyi geri duyarsın; repo GitHub'da görünür, içinde `VoiceBuddy.v1/` ve `.env` yok |
| 5 | **Intent modeli:** `data/intents.json` (v1 `words.py` örneklerinden), `intent.py`, güven eşiği | `pytest tests/test_intent.py` geçer; alakasız cümle eşik altında kalır |
| 6 | **Intent değerlendirme:** `intents_test.json` + `evaluate_intents.py` | Doğruluk yüzdesi ve karışıklık matrisi çıktısı |
| 7 | **Yetenek 1 — açma:** `SKILLS` sözlüğü, uygulama/site açma, selamlaşma, kapanma; `main.py`'ye bağla | Sesle "YouTube'u aç" çalışır; pytest geçer |
| 8 | **Yetenek 2 — saat ve tarih** | pytest (sabit bir zamanla) + sesli deneme |
| 9 | **Yetenek 3 — zamanlayıcı:** süre ayıklama + bitiş zamanı listesi (thread yok); Enter beklemesi kısa aralıklı kontrol döngüsüne çevrilir | "beş dakika" / "5 dakika" → 300 sn testi; 10 sn'lik canlı deneme; kayıt sırasında dolan süre tur bitince söylenir |
| 10 | **Yetenek 4 — hava durumu:** Open-Meteo | Sahte (mock) cevapla pytest + canlı deneme |
| 11 | **Tetikleme 1 — kısayol:** `wait_for_hotkey()` | Başka pencere öndeyken kısayol çalışır |
| 12 | **Tetikleme 2 — uyandırma kelimesi:** `wait_for_wake_word()` (Vosk), mod `config.toml`'dan | Kelimeyle uyanır; 5 dk normal konuşmada yanlış tetiklenme sayılır |
| 13 | **LLM sohbet:** `chat.py`, eşik altı → LLM, sohbet hafızası | Anahtar varken soru-cevap; anahtar yokken "anlamadım" |
| 14 | **Sağlamlaştırma:** internet yok / mikrofon yok / boş kayıt durumlarında anlaşılır mesaj | Wi-Fi kapalıyken komutlar çökmeden çalışır |
| 15 | **Vitrin:** README'lerin son hali (İngilizce + Türkçe), demo videosu, GitHub Actions ile pytest | Rozet yeşil; temiz klonda README adımlarıyla kurulur |

Her adımın sonunda bir commit atılır. İlk push Adım 4'ün sonunda yapılır; ondan sonra her adımın sonunda push edilir. Commit geçmişi de portfolyonun parçası olur.

---

## 5. README'de olması gerekenler

1. **Başlık + tek cümle** ("CPU-only Turkish desktop voice assistant") ve rozetler (Python sürümü, testler, lisans).
2. **Demo:** 30–60 sn'lik sesli video bağlantısı (GIF'te ses olmaz) + bir terminal ekran görüntüsü.
3. **Özellikler:** kısa madde listesi; hangisi offline, hangisi online açıkça yazılı.
4. **Mimari:** Mermaid akış şeması (GitHub kendisi çizer) + her modül için bir cümle.
5. **Teknoloji seçimleri ve nedenleri:** "Neden Vosk + faster-whisper?", "Neden LLM yerine klasik sınıflandırıcı?" — mülakat sorularının cevabı burada hazır durur.
6. **Ölçümler:** kendi laptopunda STT süresi (`base` vs `small`), intent doğruluğu, uçtan uca gecikme. Tahmin değil, ölçülmüş sayılar.
7. **Kurulum:** Windows için adım adım (venv, `pip install -r requirements.txt`, model indirme, `.env`).
8. **Kullanım:** örnek komut tablosu (söylediğin → olan), `config.toml` ayarları.
9. **Yeni komut ekleme:** `intents.json`'a bir kayıt + gerekirse bir fonksiyon.
10. **v1'den v2'ye:** neyin neden değiştiğini gösteren kısa tablo (exec → sözlük, gömülü anahtar → `.env`, eşik yok → güven eşiği, iki ayrı program → tek döngü).
11. **Bilinen sınırlar ve sonraki adımlar:** offline TTS (Piper), sistem tepsisi arayüzü, daha fazla yetenek.
12. **Lisans** (MIT).

---

## Doğrulama (genel)

- `pytest` — intent, yetenekler ve ayar okuma; mikrofon/hoparlör gerektirmez.
- `python scripts/evaluate_intents.py` — intent doğruluğu.
- `python scripts/benchmark_stt.py` — STT süreleri.
- `python main.py` — canlı deneme listesi: uygulama açma, saat, tarih, 10 sn zamanlayıcı, hava durumu, alakasız cümle (LLM açık ve kapalı), iki tetikleme modu, internet kapalıyken davranış.