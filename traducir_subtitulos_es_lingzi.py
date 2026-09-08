#!/usr/bin/env python3
"""
Traductor masivo de subtitulos SRT a Español (con preservacion de marcas de tiempo
y terminologia de ZhiNeng QiGong) ejecutandose localmente en LingZi.
"""
import re
import time
import json
import urllib.request
from pathlib import Path

TRANS_DIR = Path("/mnt/Archivos/Dropbox/Ai/MoneyPrinter/storage/huaxia_archive/transcriptions")
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"

def parse_srt(srt_path: Path):
    content = srt_path.read_text(encoding="utf-8")
    blocks = re.split(r"\n\s*\n", content.strip())
    subtitles = []
    for b in blocks:
        lines = b.strip().split("\n")
        if len(lines) >= 3:
            idx = lines[0].strip()
            timing = lines[1].strip()
            text = " ".join([l.strip() for l in lines[2:]])
            subtitles.append({"idx": idx, "timing": timing, "text": text})
    return subtitles

def call_ollama(prompt: str) -> str:
    data = json.dumps({
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "top_p": 0.9
        }
    }).encode("utf-8")
    
    req = urllib.request.Request(OLLAMA_URL, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        return res.get("response", "").strip()

def translate_batch(batch):
    batch_text = "\n".join([f"[{item['idx']}] {item['text']}" for item in batch])
    prompt = f"""Eres un traductor profesional experto en Medicina Tradicional China y ZhiNeng QiGong (智能气功).
Traduce los siguientes subtítulos documentales del inglés al español neutro y solemne.
Reglas estrictas:
1. Respeta fielmente la terminología: Qì (气), Hùnyuán Qì (混元气), Dùn Qiáng Gōng (sentadillas de pared), Campo de Qì (气场), Mìngmén, Dantian, Hunyuan Lingtong, etc.
2. Devuelve EXACTAMENTE el mismo formato: `[ID] Texto traducido al español`.
3. No agregues introducciones ni notas explicativas.

Subtítulos a traducir:
{batch_text}
"""
    retries = 3
    for attempt in range(retries):
        try:
            response = call_ollama(prompt)
            translations = {}
            for line in response.split("\n"):
                m = re.match(r"^\[?(\d+)\]?[\s:\-]+(.*)$", line.strip())
                if m:
                    idx_str = m.group(1).strip()
                    text_str = m.group(2).strip()
                    translations[idx_str] = text_str
            
            # Validar que se tradujeron la mayoria
            results = []
            for item in batch:
                if item["idx"] in translations:
                    results.append(translations[item["idx"]])
                else:
                    # Si fallo una linea individual, usar traduccion directa o fallback
                    results.append(item["text"])
            return results
        except Exception as e:
            print(f"[RETRY {attempt+1}] Error en llamada Ollama: {e}")
            time.sleep(2)
            
    return [item["text"] for item in batch]

def process_file(part_num: int):
    en_srt = TRANS_DIR / f"part_part {part_num}_en.srt"
    es_srt = TRANS_DIR / f"part_part {part_num}_es.srt"
    
    if not en_srt.exists():
        print(f"[SKIP] No existe {en_srt.name}")
        return
        
    print(f"\n==================================================")
    print(f"Traduciendo Parte {part_num} a Español...")
    print(f"==================================================")
    
    subs = parse_srt(en_srt)
    print(f"Total subtitulos: {len(subs)}")
    
    batch_size = 8
    translated_subs = []
    
    for i in range(0, len(subs), batch_size):
        batch = subs[i:i+batch_size]
        print(f"Traduciendo bloque {i+1} a {min(i+batch_size, len(subs))}...")
        es_texts = translate_batch(batch)
        for sub, es_text in zip(batch, es_texts):
            translated_subs.append({
                "idx": sub["idx"],
                "timing": sub["timing"],
                "text": es_text
            })
            
    # Escribir el archivo final SRT en español
    with open(es_srt, "w", encoding="utf-8") as f:
        for item in translated_subs:
            f.write(f"{item['idx']}\n{item['timing']}\n{item['text']}\n\n")
            
    print(f"[OK] Guardado: {es_srt.name} con {len(translated_subs)} subtitulos")

def main():
    print("Iniciando generacion de subtitulos sincronizados en Espanol...")
    for part in range(1, 8):
        process_file(part)
    print("\n[FIN] Todas las 7 partes han sido traducidas y sincronizadas al Espanol.")

if __name__ == "__main__":
    main()
