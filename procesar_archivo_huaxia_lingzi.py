#!/usr/bin/env python3
"""
Pipeline de procesamiento del archivo audiovisual histórico del Centro Huaxia
Ejecución exclusiva en el nodo de cómputo LingZi.
"""
import os
import glob
import subprocess
from pathlib import Path
from faster_whisper import WhisperModel
import imageio_ffmpeg

FFMPEG_BIN = imageio_ffmpeg.get_ffmpeg_exe()
BASE_DIR = Path("/mnt/Archivos/Dropbox/Ai/MoneyPrinter/storage/huaxia_archive")
RAW_DIR = BASE_DIR / "raw_videos"
AUDIO_DIR = BASE_DIR / "audio"
TRANS_DIR = BASE_DIR / "transcriptions"
CLIPS_DIR = BASE_DIR / "clips_916"

AUDIO_DIR.mkdir(parents=True, exist_ok=True)
TRANS_DIR.mkdir(parents=True, exist_ok=True)
CLIPS_DIR.mkdir(parents=True, exist_ok=True)

def format_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def extract_audio(video_path: Path, audio_path: Path):
    if audio_path.exists() and audio_path.stat().st_size > 1000:
        print(f"[AUDIO] Ya existe: {audio_path.name}")
        return
    print(f"[AUDIO] Extrayendo audio a 16kHz mono: {audio_path.name}...")
    cmd = [
        FFMPEG_BIN, "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        str(audio_path)
    ]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0:
        print(f"[ERROR AUDIO] {res.stderr.decode('utf-8', errors='ignore')}")
    else:
        print(f"[AUDIO OK] {audio_path.name}")

def transcribe_and_translate(audio_path: Path, part_name: str, model: WhisperModel):
    srt_zh_path = TRANS_DIR / f"{part_name}_zh.srt"
    srt_es_path = TRANS_DIR / f"{part_name}_es.srt"
    txt_summary_path = TRANS_DIR / f"{part_name}_summary.txt"
    
    # 1. Transcripción original en Mandarín (con timestamps exactos)
    if not srt_zh_path.exists():
        print(f"[WHISPER] Transcribiendo en Chino: {audio_path.name}...")
        segments_zh, info_zh = model.transcribe(str(audio_path), language="zh", task="transcribe", beam_size=5)
        
        with open(srt_zh_path, "w", encoding="utf-8") as f_zh:
            idx = 1
            for seg in segments_zh:
                start_str = format_timestamp(seg.start)
                end_str = format_timestamp(seg.end)
                f_zh.write(f"{idx}\n{start_str} --> {end_str}\n{seg.text.strip()}\n\n")
                idx += 1
        print(f"[SRT ZH OK] Guardado en {srt_zh_path.name}")
    else:
        print(f"[SRT ZH] Ya existe {srt_zh_path.name}")

    # 2. Traducción a Inglés / Español
    # faster-whisper soporta task="translate" directo a inglés; luego se genera mapeo o traducción
    srt_en_path = TRANS_DIR / f"{part_name}_en.srt"
    if not srt_en_path.exists():
        print(f"[WHISPER] Traduciendo audio a Inglés: {audio_path.name}...")
        segments_en, info_en = model.transcribe(str(audio_path), language="zh", task="translate", beam_size=5)
        
        with open(srt_en_path, "w", encoding="utf-8") as f_en:
            idx = 1
            for seg in segments_en:
                start_str = format_timestamp(seg.start)
                end_str = format_timestamp(seg.end)
                f_en.write(f"{idx}\n{start_str} --> {end_str}\n{seg.text.strip()}\n\n")
                idx += 1
        print(f"[SRT EN OK] Guardado en {srt_en_path.name}")
    else:
        print(f"[SRT EN] Ya existe {srt_en_path.name}")

def extract_broll_clips(video_path: Path, part_num: int):
    """
    Extrae segmentos de impacto y los normaliza a formato vertical 9:16 (1080x1920) con fondo desenfocado
    para usarse directamente en MoneyPrinter
    """
    clips_config = {
        1: [
            {"name": "huaxia_campus_arrival", "ss": "00:01:40", "t": "12", "desc": "Llegada masiva de estudiantes al Centro Huaxia"},
            {"name": "huaxia_books_theory", "ss": "00:07:30", "t": "10", "desc": "Libros oficiales de la Ciencia ZhiNeng Qigong Dr Pang Ming"}
        ],
        2: [
            {"name": "huaxia_patient_intake", "ss": "00:01:10", "t": "12", "desc": "Recepción de estudiantes y diagnóstico de entrada"},
            {"name": "huaxia_wheelchair_care", "ss": "00:02:40", "t": "10", "desc": "Casos clínicos de parálisis siendo atendidos con Qi"}
        ],
        3: [
            {"name": "huaxia_mass_qifield_kaihe", "ss": "00:02:30", "t": "15", "desc": "Miles de practicantes haciendo Kai He en el gran campo"},
            {"name": "huaxia_collective_healing", "ss": "00:05:20", "t": "12", "desc": "Maestros emitiendo Qi colectivo Fa Qi"}
        ],
        4: [
            {"name": "huaxia_scientific_tests", "ss": "00:02:00", "t": "12", "desc": "Pruebas científicas y de laboratorio antes y después"}
        ],
        5: [
            {"name": "huaxia_dun_qiang_gong_demo", "ss": "00:03:00", "t": "15", "desc": "Demostración de sentadillas de pared Dun Qiang Gong"}
        ],
        6: [
            {"name": "huaxia_patient_stands_up", "ss": "00:02:30", "t": "15", "desc": "Paciente en silla de ruedas poniéndose de pie"}
        ],
        7: [
            {"name": "huaxia_celebration_dance", "ss": "00:03:10", "t": "12", "desc": "Celebración y graduación Hunyuan Lingtong"}
        ]
    }
    
    if part_num not in clips_config:
        return
        
    for item in clips_config[part_num]:
        out_clip = CLIPS_DIR / f"{item['name']}_916.mp4"
        if out_clip.exists() and out_clip.stat().st_size > 10000:
            print(f"[CLIP] Ya existe: {out_clip.name}")
            continue
            
        print(f"[CLIP 9:16] Generando {out_clip.name} ({item['desc']})...")
        # Filtro de escala inteligente: Video 4:3 centrado y nítido, con fondo desenfocado rellenando 1080x1920 (9:16)
        filter_complex = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=25:5[bg];"
            "[0:v]scale=1080:-1:force_original_aspect_ratio=decrease[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2"
        )
        cmd = [
            FFMPEG_BIN, "-y",
            "-ss", item["ss"],
            "-i", str(video_path),
            "-t", item["t"],
            "-filter_complex", filter_complex,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "22",
            "-c:a", "aac",
            "-b:a", "128k",
            str(out_clip)
        ]
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode != 0:
            print(f"[CLIP ERROR] {res.stderr.decode('utf-8', errors='ignore')}")
        else:
            print(f"[CLIP OK] Creado: {out_clip.name}")

def main():
    print("==================================================")
    print("Iniciando Procesamiento del Archivo Huaxia en LingZi")
    print(f"Directorio de videos: {RAW_DIR}")
    print("==================================================")
    
    videos = sorted(RAW_DIR.glob("*.mp4"))
    if not videos:
        print(f"[ALERTA] No se encontraron archivos .mp4 en {RAW_DIR}")
        return
        
    print(f"Total de videos a procesar: {len(videos)}")
    
    # 1. Extraer Audio de todas las partes
    for v in videos:
        part_name = v.stem.replace("Bring You A Whole New Life - Huaxia Zhineng Qigong Center (", "part_").replace(")", "").strip()
        audio_file = AUDIO_DIR / f"{part_name}.wav"
        extract_audio(v, audio_file)
        
    # 2. Inicializar modelo Whisper en LingZi (usamos 'small' o 'medium' en CPU i7-9700 optimizado con int8)
    print("\n[MODEL] Cargando modelo faster-whisper (medium / int8)...")
    model = WhisperModel("medium", device="cpu", compute_type="int8")
    print("[MODEL OK] Modelo cargado en RAM")
    
    # 3. Transcripción y Subtitulado
    for v in videos:
        part_name = v.stem.replace("Bring You A Whole New Life - Huaxia Zhineng Qigong Center (", "part_").replace(")", "").strip()
        audio_file = AUDIO_DIR / f"{part_name}.wav"
        transcribe_and_translate(audio_file, part_name, model)
        
    # 4. Generación de B-Roll 9:16 para MoneyPrinter
    print("\n[B-ROLL] Extrayendo y normalizando clips 9:16...")
    for idx, v in enumerate(videos, start=1):
        extract_broll_clips(v, idx)
        
    print("\n==================================================")
    print("Procesamiento completado con éxito en LingZi.")
    print("==================================================")

if __name__ == "__main__":
    main()
