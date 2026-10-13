import time
import base64
import httpx
from typing import Dict, Any, Optional
from app.config import settings

class ElevenLabsEngine:
    """
    ElevenLabs Voice & Audio Promo Generator.
    Turns product copy and hooks into studio-grade voiceover audio for TikTok, Reels, and Shorts.
    """

    VOICE_PRESETS = {
        "warm_artisan": {
            "name": "Rachel (Warm & Authentic Artisan)",
            "voice_id": "21m00Tcm4TlvDq8ikWAM",
            "stability": 0.75,
            "similarity_boost": 0.85
        },
        "luxury_commercial": {
            "name": "Adam (Deep & Sleek Luxury)",
            "voice_id": "pNInz6obpgDQGcFmaJgB",
            "stability": 0.65,
            "similarity_boost": 0.80
        },
        "upbeat_creator": {
            "name": "Bella (Energetic Social Creator)",
            "voice_id": "EXAVITQu4vr4xnSDxMaL",
            "stability": 0.50,
            "similarity_boost": 0.75
        },
        "vintage_storyteller": {
            "name": "Antoni (Vintage & Heirloom Narration)",
            "voice_id": "ErXwobaYiN019PkySvjV",
            "stability": 0.70,
            "similarity_boost": 0.80
        }
    }

    def __init__(self):
        self.api_key = settings.elevenlabs_api_key

    async def generate_promo_voice(
        self,
        script_text: str,
        voice_preset: str = "warm_artisan",
        custom_voice_id: Optional[str] = None
    ) -> Dict[str, Any]:
        start_time = time.time()
        preset = self.VOICE_PRESETS.get(voice_preset, self.VOICE_PRESETS["warm_artisan"])
        voice_id = custom_voice_id or preset["voice_id"]
        
        # Clean script text
        script = script_text.strip()
        if not script:
            script = "Discover hand-crafted quality made with heart and heirloom dedication. Tap the link to view the collection."

        # If ElevenLabs API Key is present, make real call
        if self.api_key:
            try:
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                headers = {
                    "Accept": "audio/mpeg",
                    "Content-Type": "application/json",
                    "xi-api-key": self.api_key
                }
                payload = {
                    "text": script,
                    "model_id": "eleven_turbo_v2_5",
                    "voice_settings": {
                        "stability": preset.get("stability", 0.75),
                        "similarity_boost": preset.get("similarity_boost", 0.85)
                    }
                }
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(url, headers=headers, json=payload)
                    if resp.status_code == 200:
                        audio_base64 = base64.b64encode(resp.content).decode("utf-8")
                        return {
                            "success": True,
                            "script": script,
                            "voice_name": preset["name"],
                            "voice_id": voice_id,
                            "audio_format": "audio/mp3",
                            "audio_base64": f"data:audio/mp3;base64,{audio_base64}",
                            "engine": "ElevenLabs Turbo v2.5",
                            "latency_ms": round((time.time() - start_time) * 1000, 2),
                            "mode": "elevenlabs_api"
                        }
                    else:
                        print(f"[ElevenLabsEngine] API error: {resp.status_code} - {resp.text}")
            except Exception as e:
                print(f"[ElevenLabsEngine] Exception: {e}")

        # Browser Web Speech / Audio Synthesis fallback mode
        return {
            "success": True,
            "script": script,
            "voice_name": preset["name"],
            "voice_id": voice_id,
            "audio_format": "web_speech_synthesis",
            "audio_base64": None,
            "engine": "Web Speech Audio Synthesis (ElevenLabs Script Ready)",
            "note": "Set ELEVENLABS_API_KEY to activate ultra-realistic studio ElevenLabs audio stream. Playing in-browser high-definition voice synthesizer.",
            "latency_ms": round((time.time() - start_time) * 1000, 2),
            "mode": "browser_fallback"
        }

elevenlabs_engine = ElevenLabsEngine()
