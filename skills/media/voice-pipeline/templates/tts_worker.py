#!/usr/bin/env python3
"""
TTS Persistent Worker — giữ edge-tts connection (Microsoft websocket) trong memory.
Nhận text qua stdin (1 dòng / request), trả JSON qua stdout. MP3 trực tiếp, không convert.

Protocol:
  request:  {"text": "...", "voice": "vi-VN-HoaiMyNeural", "rate": "+20%", "out": "C:/path/out.mp3"}
  response: {"path": "...", "bytes": N, "duration": N, "elapsed": N}

Chạy: python tts_worker.py
Lưu ý: cần `pip install edge-tts mutagen`
"""
import sys, json, os, asyncio, time

async def synthesize(text, voice, rate, out_path):
    import edge_tts
    c = edge_tts.Communicate(text, voice=voice, rate=rate)
    await c.save(out_path)  # MP3 — browser plays natively, no ffmpeg needed
    duration = 0.0
    try:
        from mutagen.mp3 import MP3
        duration = MP3(out_path).info.length
    except Exception:
        pass
    return {
        'path': out_path,
        'bytes': os.path.getsize(out_path) if os.path.exists(out_path) else 0,
        'duration': round(duration, 2),
    }

def main():
    print(json.dumps({"ready": "ok"}), flush=True)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            text = req.get('text', '')
            voice = req.get('voice', 'vi-VN-HoaiMyNeural')
            rate = req.get('rate', '+20%')
            out_path = req.get('out', '')
            if not text or not out_path:
                print(json.dumps({"error": "missing text or out"}), flush=True)
                continue
            t0 = time.time()
            result = loop.run_until_complete(synthesize(text, voice, rate, out_path))
            result['elapsed'] = round(time.time() - t0, 2)
            print(json.dumps(result), flush=True)
        except Exception as e:
            print(json.dumps({"error": str(e)}), flush=True)

if __name__ == '__main__':
    main()
