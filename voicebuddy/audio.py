"""Audio input: record from the microphone until the speaker goes quiet."""

import numpy as np
import sounddevice as sd
import soundfile as sf

SAMPLE_RATE = 16000  # samples per second; the rate speech models expect
BLOCK_SECONDS = 0.1  # the microphone is read in pieces of this length
SILENCE_THRESHOLD = 0.01  # a block quieter than this (RMS) counts as silence
SILENCE_SECONDS = 1.0  # stop after this much silence once speech has started
MAX_SECONDS = 10.0  # never record longer than this
WARMUP_SECONDS = 1.0  # measured: the microphone gives only zeros this long after opening


def record_until_silence():
    """Record from the microphone and return the samples as a 1-D array."""
    block_size = int(SAMPLE_RATE * BLOCK_SECONDS)
    max_blocks = int(MAX_SECONDS / BLOCK_SECONDS)
    silent_blocks_to_stop = int(SILENCE_SECONDS / BLOCK_SECONDS)

    blocks = []
    silent_blocks = 0
    speech_started = False

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32") as stream:
        # Opening the microphone takes a moment. Words said before this line
        # are lost, so tell the user when it is really listening.
        # Read and throw away the warm-up part first: it holds no real sound.
        stream.read(int(SAMPLE_RATE * WARMUP_SECONDS))
        print("Listening...")
        while len(blocks) < max_blocks:
            block, overflowed = stream.read(block_size)
            blocks.append(block)

            # RMS (root mean square) is the average loudness of the block.
            rms = np.sqrt(np.mean(block**2))
            if rms >= SILENCE_THRESHOLD:
                speech_started = True
                silent_blocks = 0
            else:
                silent_blocks += 1

            # Silence before the first word must not end the recording.
            if speech_started and silent_blocks >= silent_blocks_to_stop:
                break

    # Join the blocks and drop the channel axis: shape (n, 1) becomes (n,).
    return np.concatenate(blocks)[:, 0]


if __name__ == "__main__":
    # Manual test: python -m voicebuddy.audio
    samples = record_until_silence()
    print(f"Recorded {len(samples) / SAMPLE_RATE:.1f} seconds.")
    sf.write("recording.wav", samples, SAMPLE_RATE)
    sd.play(samples, SAMPLE_RATE)
    sd.wait()
