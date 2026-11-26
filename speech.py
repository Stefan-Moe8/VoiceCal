import wave
import io
import time
import openai
from config import voice_client, STT_MODEL
from usage import log_usage

# Variables for voic recording
SAMPLE_RATE = 16000  # 16 kHz mono is plenty for speech
PCM_BYTES_PER_SECOND = SAMPLE_RATE * 2  # 16-bit mono = 2 bytes per sample

# Records a wav from the users microphone
def record_wav(seconds=6):
    import sounddevice as sd
    """Record from the default microphone and return WAV bytes."""
    print(f"Recording for {seconds} s... speak now.")
    audio = sd.rec(int(seconds * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="int16")
    sd.wait()
    print("Done.")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)  # 16-bit
        w.setframerate(SAMPLE_RATE)
        w.writeframes(audio.tobytes())
    return buf.getvalue()

# Speech to text: returns the transcript and logs the cost
def transcribe(wav, prompt=None):
    """Speech to text: returns the transcript and logs the cost ($0.0045 per minute of audio)."""
    t0 = time.perf_counter()
    hint = {"prompt": prompt} if prompt else {}
    result = voice_client.audio.transcriptions.create(model=STT_MODEL, file=("speech.wav", wav, "audio/wav"), **hint)
    seconds = getattr(result.usage, "seconds", None) or len(wav) / PCM_BYTES_PER_SECOND
    log_usage("speech to text", STT_MODEL, time.perf_counter() - t0, audio_seconds=seconds)
    return result.text

# Runs a voice call
def voice_call(feature, function, *args, **kwargs):
    """Run a voice call; if the API fails (for example a timeout), print one line and return None."""
    try:
        return function(*args, **kwargs)
    except openai.APIError as e:
        reason = "the speech service did not answer in time" if isinstance(e, openai.APITimeoutError) else type(e).__name__
        print(f"{feature} skipped: {reason}.")
        return None
