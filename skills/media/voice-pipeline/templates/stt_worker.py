#!/usr/bin/env python3
"""
STT Persistent Worker — giữ faster-whisper model trong memory.
Nhận audio path qua stdin (1 dòng / request), trả JSON qua stdout.

Protocol:
  request:  {"path": "<audio_path>", "lang": "vi"}\n
  response: {"text": "...", "duration": N}\n
  startup:  {"ready": "loading"} → {"ready": "ok", "model": "..."}

Chạy: python stt_worker.py --model small
"""
import sys, json, argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default='small')
    parser.add_argument('--lang', default='vi')
    args = parser.parse_args()

    try:
        from faster_whisper import WhisperModel
        print(json.dumps({"ready": "loading", "model": args.model}), flush=True)
        model = WhisperModel(args.model, device='cpu', compute_type='int8')
        print(json.dumps({"ready": "ok", "model": args.model}), flush=True)
    except Exception as e:
        print(json.dumps({"fatal": str(e)}), flush=True)
        return 1

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line) if line.startswith('{') else {"path": line}
            audio_path = req.get('path', '')
            lang = req.get('lang', args.lang)
            segments, info = model.transcribe(
                audio_path,
                language=lang,
                vad_filter=True,
                beam_size=1,
            )
            text = ' '.join(s.text.strip() for s in segments).strip()
            print(json.dumps({"text": text, "duration": round(info.duration, 2)}), flush=True)
        except Exception as e:
            print(json.dumps({"error": str(e)}), flush=True)

if __name__ == '__main__':
    sys.exit(main())
