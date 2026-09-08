#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MASTER PRODUCER NOCTURNO: SERIE FUNDACIONAL COMPLETA ZNQG (30 VIDEOS: 15 ES + 15 EN)
=====================================================================================
- 15 Episodios Fundacionales de ZhiNeng QiGong en Español e Inglés (~1 min c/u) = 30 Videos
- Exclusividad Huaxia: Metraje histórico de Huaxia SOLO en Ep 07, 08 y 09 (eliminado del resto)
- Clips limpios sin marcos blancos (corte a partir del segundo 4)
- Banco visual enriquecido con SD-Turbo en LíngZi (sin repeticiones) + 31 imágenes curadas + Video Personal
- Ortografía estricta en subtítulos: "ZhiNeng QiGong" y "Qi" protegidos con límites de palabra (\b)
- Miniaturas verticales HD (1080x1920) y metadatos completos para YouTube / Instagram / TikTok
"""

import os
import sys
import re
import json
import base64
import requests
import subprocess
from pathlib import Path
from loguru import logger
from PIL import Image, ImageDraw, ImageFont

# Directorios de Trabajo
SCRIPT_DIR = Path(__file__).resolve().parent
STORAGE_DIR = SCRIPT_DIR / "storage"
CACHE_DIR = STORAGE_DIR / "cache_videos" / "night_production"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_BASE = STORAGE_DIR / "serie_fundacional_30_videos"
OUTPUT_COVERS = OUTPUT_BASE / "portadas_sociales"
OUTPUT_METAS = OUTPUT_BASE / "metadatos_redes"
OUTPUT_BASE.mkdir(parents=True, exist_ok=True)
OUTPUT_COVERS.mkdir(parents=True, exist_ok=True)
OUTPUT_METAS.mkdir(parents=True, exist_ok=True)

# Tipografías y Herramientas
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_MEDIUM = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# FFmpeg binario del entorno virtual de MoneyPrinter
FFMPEG = str(Path(sys.executable).parent.parent / "lib" / "python3.11" / "site-packages" / "imageio_ffmpeg" / "binaries" / "ffmpeg-linux-x86_64-v7.0.2")
if not os.path.exists(FFMPEG):
    FFMPEG = "ffmpeg"

PERSONALES = STORAGE_DIR / "local_videos" / "personales" / "VID_20260628_144710.mp4"
HUAXIA_RAW = STORAGE_DIR / "huaxia_archive" / "clips_916"
BANCO_EXISTENTE = STORAGE_DIR / "local_videos" / "ai_generated" / "banco_imagenes_serie15"

# Setup MoneyPrinter app
sys.path.insert(0, str(SCRIPT_DIR))
from app.services import llm, voice, video, subtitle

def extract_personal_subclip(start_sec: int, duration_sec: int, name: str) -> str:
    out = CACHE_DIR / f"personal_{name}_{start_sec}s.mp4"
    if not out.exists() or out.stat().st_size < 1000:
        cmd = [
            FFMPEG, "-y",
            "-ss", str(start_sec),
            "-i", str(PERSONALES),
            "-t", str(duration_sec),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-c:v", "libx264", "-preset", "fast", "-an",
            str(out)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return str(out)

def extract_clean_huaxia_subclip(clip_name: str, start_sec: int, duration_sec: int, out_name: str) -> str:
    src = HUAXIA_RAW / clip_name
    out = CACHE_DIR / f"huaxia_clean_{out_name}.mp4"
    if not out.exists() or out.stat().st_size < 1000:
        cmd = [
            FFMPEG, "-y",
            "-ss", str(start_sec),
            "-i", str(src),
            "-t", str(duration_sec),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-c:v", "libx264", "-preset", "fast", "-an",
            str(out)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return str(out)

def generate_sd_turbo_image(prompt: str, filename: str) -> str:
    out_path = CACHE_DIR / f"{filename}.png"
    if not out_path.exists() or out_path.stat().st_size < 1000:
        url = "http://127.0.0.1:8002/v1/images/generations"
        payload = {"prompt": prompt, "size": "512x512"}
        try:
            res = requests.post(url, json=payload, timeout=60)
            if res.status_code == 200:
                b64 = res.json()["data"][0]["b64_json"]
                with open(out_path, "wb") as f:
                    f.write(base64.b64decode(b64))
                logger.info(f"SD-Turbo imagen generada: {out_path.name}")
            else:
                logger.warning(f"Fallo SD-Turbo ({res.status_code}) para {filename}")
        except Exception as e:
            logger.warning(f"Error generando imagen SD-Turbo: {e}")

    # Convertir a clip 9:16 de 8s
    clip_out = CACHE_DIR / f"{filename}_8s_916.mp4"
    if not clip_out.exists() and out_path.exists():
        cmd = [
            FFMPEG, "-y", "-loop", "1", "-i", str(out_path), "-t", "8",
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "25",
            str(clip_out)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return str(clip_out)

def ensure_image_clip(img_path: str, duration: int = 8) -> str:
    p = Path(img_path)
    out = CACHE_DIR / f"{p.stem}_{duration}s_916.mp4"
    if not out.exists() or out.stat().st_size < 1000:
        cmd = [
            FFMPEG, "-y", "-loop", "1", "-i", str(p), "-t", str(duration),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "25",
            str(out)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return str(out)

def apply_subtitles_clean(subtitle_path: str, replacements: dict):
    if os.path.exists(subtitle_path):
        with open(subtitle_path, "r", encoding="utf-8") as f:
            srt = f.read()

        sorted_replacements = sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True)
        for orig, repl in sorted_replacements:
            pattern = r'\b' + re.escape(orig) + r'\b'
            srt = re.sub(pattern, repl, srt, flags=re.IGNORECASE)

        # Protección estricta contra prefijos y deformaciones
        srt = re.sub(r'\bQì?neng\s+Qì?kung\b', 'ZhiNeng QiGong', srt, flags=re.IGNORECASE)
        srt = re.sub(r'\bQìna\b', 'China', srt)
        srt = re.sub(r'\bqìna\b', 'china', srt)

        with open(subtitle_path, "w", encoding="utf-8") as f:
            f.write(srt)

def generate_social_covers(title: str, subtitle: str, badge: str, theme_color: tuple, bg_image_path: str, base_name: str, lang: str):
    W, H = 1080, 1920
    if not os.path.exists(bg_image_path):
        return
    bg = Image.open(bg_image_path).convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    o_draw = ImageDraw.Draw(overlay)
    o_draw.rectangle([0, 0, W, H], fill=(0, 0, 0, 80))

    for y in range(350, 1570):
        dist = abs(y - 960) / 610.0
        alpha = int(220 * (1 - dist**1.8))
        o_draw.line([(0, y), (W, y)], fill=(10, 15, 30, max(0, min(230, alpha))))

    combined = Image.alpha_composite(bg, overlay)
    draw = ImageDraw.Draw(combined)

    font_badge = ImageFont.truetype(FONT_BOLD, 28)
    font_title = ImageFont.truetype(FONT_BOLD, 52)
    font_sub = ImageFont.truetype(FONT_BOLD, 32)
    font_foot = ImageFont.truetype(FONT_MEDIUM, 26)

    # Badge
    bbox = draw.textbbox((0, 0), badge, font=font_badge)
    bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
    bx, by = (W - bw) // 2, 580
    draw.rounded_rectangle([bx - 20, by - 10, bx + bw + 20, by + bh + 10], radius=16, fill=(15, 25, 45, 230), outline=theme_color, width=2)
    draw.text((bx, by), badge, font=font_badge, fill=theme_color)

    # Título
    lines = [title] if len(title) < 28 else [title[:25] + "...", title[25:]]
    curr_y = 690
    for line in lines:
        tbox = draw.textbbox((0, 0), line, font=font_title)
        tw = tbox[2] - tbox[0]
        draw.text(((W - tw) // 2 + 2, curr_y + 2), line, font=font_title, fill=(0, 0, 0, 200))
        draw.text(((W - tw) // 2, curr_y), line, font=font_title, fill=(255, 255, 255))
        curr_y += 65

    # Subtítulo
    sbox = draw.textbbox((0, 0), subtitle, font=font_sub)
    sw = sbox[2] - sbox[0]
    draw.text(((W - sw) // 2, curr_y + 30), subtitle, font=font_sub, fill=theme_color)

    # Footer
    foot_text = "Sembradores de Qì • ZhiNeng QiGong" if lang == "ES" else "Qi Sowers • ZhiNeng QiGong"
    fbox = draw.textbbox((0, 0), foot_text, font=font_foot)
    fw = fbox[2] - fbox[0]
    draw.text(((W - fw) // 2, 1340), foot_text, font=font_foot, fill=(200, 210, 225))

    out_file = OUTPUT_COVERS / f"{base_name}_cover_{lang}.png"
    combined.convert("RGB").save(out_file, quality=95)
    logger.info(f"Portada generada: {out_file.name}")

def generate_social_metadata(ep: dict, base_name: str):
    md_content = f"""# KIT DE PUBLICACIÓN Y METADATOS: {ep['num']} - {ep['title_es']}
## SERIE FUNDACIONAL ZHINENG QIGONG (30 VIDEOS)

---

### 🇲🇽 VERSIÓN ESPAÑOL (ES)

#### 1. Título para YouTube (Reels & Shorts)
`{ep['num']} | {ep['title_es']} - ZhiNeng QiGong (Subtitulado)`

#### 2. Descripción Completa para YouTube / Facebook
```text
{ep['desc_es']}

🌿 En esta Serie Fundacional de 15 Episodios aprenderás las bases teóricas y científicas del ZhiNeng QiGong (智能气功), el sistema de desarrollo de la conciencia y autorregulación creado por el Dr. Pang Ming.

⏱️ Puntos Clave del Video:
00:00 - Introducción y Fundamentos
00:20 - Principio Teórico y Aplicación Práctica
00:45 - Integración Diaria y Cultivo de Qì

🧘‍♂️ Conecta con la Comunidad de Sembradores de Qì:
✨ Suscríbete al canal para no perderte ningún episodio de la serie.
💬 Comenta tus sensaciones al practicar y comparte con quienes busquen salud y serenidad.

{ep['hashtags_es']}
```

#### 3. Etiquetas SEO para YouTube (Tags)
```text
{ep['tags_es']}
```

#### 4. Copy para Instagram Reel / TikTok
```text
{ep['copy_ig_es']}

👉 Guarda este video para recordar este fundamento en tu práctica diaria.
{ep['hashtags_es']}
```

---

### 🇺🇸 ENGLISH VERSION (EN)

#### 1. YouTube Title (Reels & Shorts)
`{ep['num']} | {ep['title_en']} - ZhiNeng QiGong (HD & Subtitled)`

#### 2. Full YouTube / Facebook Description
```text
{ep['desc_en']}

🌿 In this 15-Episode Foundation Series, you will discover the scientific and theoretical pillars of ZhiNeng QiGong (智能气功), the transformative mind-energy science founded by Dr. Pang Ming.

⏱️ Key Highlights:
00:00 - Introduction and Core Concept
00:20 - Energetic Mechanism & Mind Alignment
00:45 - Daily Cultivation & Inner Harmony

🧘‍♂️ Connect with Qi Sowers:
✨ Subscribe to stay updated with every lesson of this foundational journey.
💬 Share your reflections in the comments below!

{ep['hashtags_en']}
```

#### 3. YouTube SEO Tags
```text
{ep['tags_en']}
```

#### 4. Instagram Reel / TikTok Copy
```text
{ep['copy_ig_en']}

👉 Save this Reel for your daily practice reminder!
{ep['hashtags_en']}
```
"""
    out_md = OUTPUT_METAS / f"{base_name}_metadatos_sociales.md"
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md_content)
    logger.info(f"Metadatos sociales guardados: {out_md.name}")

def produce_single_video(video_subject: str, script_text: str, voice_name: str, materials: list, out_path: Path, replacements: dict):
    if out_path.exists() and out_path.stat().st_size > 1000000:
        logger.info(f"Video ya existe: {out_path.name}")
        return

    temp_id = f"prod_{out_path.stem}"
    task_dir = STORAGE_DIR / "tasks" / temp_id
    task_dir.mkdir(parents=True, exist_ok=True)

    audio_file = str(task_dir / "tts_voice.mp3")
    subtitle_file = str(task_dir / "subtitles.srt")

    logger.info(f"Sintetizando voz: {voice_name}...")
    voice.tts(text=script_text, voice_name=voice_name, voice_rate=1.0, voice_file=audio_file)
    logger.info("Transcribiendo subtítulos...")
    subtitle.create(audio_file=audio_file, subtitle_file=subtitle_file)

    logger.info("Aplicando ortografía estricta a subtítulos...")
    apply_subtitles_clean(subtitle_file, replacements)

    logger.info(f"Ensamblando video {out_path.name}...")
    final_video = video.combine_videos(
        combined_video_path=str(out_path),
        video_paths=materials,
        audio_file=audio_file,
        video_aspect=video.VideoAspect.portrait,
        max_clip_duration=7,
        threads=8
    )

    if final_video and os.path.exists(final_video):
        logger.info(f"Incrustando subtítulos en {out_path.name}...")
        video_with_subs = str(out_path).replace(".mp4", "_subbed.mp4")
        video.add_subtitles(
            source_path=final_video,
            subtitles_path=subtitle_file,
            output_path=video_with_subs,
            font_size=18,
            font_color="&H00FFFFFF",
            outline_color="&H00000000",
            outline_width=2,
            bottom_margin=380
        )
        if os.path.exists(video_with_subs):
            os.replace(video_with_subs, out_path)
            logger.success(f"Video finalizado con éxito: {out_path.name}")

def main():
    logger.info("===================================================================")
    logger.info("  ORQUESTADOR AUTÓNOMO NOCTURNO: SERIE FUNDACIONAL (30 VIDEOS)")
    logger.info("===================================================================")

    # 1. Preparar metraje Huaxia (SOLO se usará en Ep 07, 08 y 09)
    logger.info("-> Preparando clips limpios de Huaxia (sin pantallas blancas)...")
    huaxia_campus = extract_clean_huaxia_subclip("huaxia_campus_arrival_916.mp4", start_sec=4, duration_sec=8, out_name="campus")
    huaxia_healing = extract_clean_huaxia_subclip("huaxia_collective_healing_916.mp4", start_sec=4, duration_sec=8, out_name="healing")
    huaxia_scientific = extract_clean_huaxia_subclip("huaxia_scientific_tests_916.mp4", start_sec=3, duration_sec=8, out_name="scientific")
    huaxia_dunqiang = extract_clean_huaxia_subclip("huaxia_dun_qiang_gong_demo_916.mp4", start_sec=2, duration_sec=8, out_name="dunqiang")
    huaxia_care = extract_clean_huaxia_subclip("huaxia_wheelchair_care_916.mp4", start_sec=2, duration_sec=8, out_name="wheelchair_care")

    # 2. Preparar Subclips del Video Personal VID_20260628_144710.mp4
    logger.info("-> Preparando clips del video personal...")
    p_clip1 = extract_personal_subclip(start_sec=15, duration_sec=6, name="p1_intro")
    p_clip2 = extract_personal_subclip(start_sec=45, duration_sec=6, name="p2_posture")
    p_clip3 = extract_personal_subclip(start_sec=85, duration_sec=6, name="p3_mind")
    p_clip4 = extract_personal_subclip(start_sec=140, duration_sec=6, name="p4_energy")
    p_clip5 = extract_personal_subclip(start_sec=210, duration_sec=6, name="p5_harmony")
    p_clip6 = extract_personal_subclip(start_sec=245, duration_sec=6, name="p6_focus")
    p_clip7 = extract_personal_subclip(start_sec=270, duration_sec=6, name="p7_flow")

    # 3. Generar Banco de Imágenes Temáticas Inéditas con SD-Turbo en LingZi
    logger.info("-> Sintetizando imágenes originales con SD-Turbo en LingZi...")
    sd_nebula = generate_sd_turbo_image("golden cosmic energy spiral, vibrant hunyuan nebula, photorealistic 8k", "sd_cosmic_nebula")
    sd_cell = generate_sd_turbo_image("luminous biological cells glowing with healing golden light, cellular regeneration", "sd_cellular_light")
    sd_meridian = generate_sd_turbo_image("human silhouette meditating with flowing energy lines, peaceful harmony, ethereal", "sd_energy_meridians")
    sd_mind = generate_sd_turbo_image("crystal clear pond reflecting radiant dawn, calm focused awareness, zen", "sd_pure_mind")
    sd_spine = generate_sd_turbo_image("spine alignment glowing with vitality, warm light, health, anatomical beauty", "sd_healthy_spine")

    # 4. Asegurar clips 9:16 del banco curado existente (31 imágenes temáticas)
    logger.info("-> Asegurando clips 9:16 del banco de imágenes curadas...")
    curated_clips = {}
    for num in range(1, 16):
        s_num = f"{num:02d}"
        for res in ["res1", "res2"]:
            matches = list(BANCO_EXISTENTE.glob(f"ep{s_num}_*_{res}.jpg"))
            if matches:
                curated_clips[f"ep{s_num}_{res}"] = ensure_image_clip(str(matches[0]), duration=8)
    # Extra ep01
    ep01_extra = BANCO_EXISTENTE / "ep01_que_es_el_qi_01.jpg"
    if ep01_extra.exists():
        curated_clips["ep01_01"] = ensure_image_clip(str(ep01_extra), duration=8)

    # 5. MATRIZ MAESTRA: LOS 15 EPISODIOS FUNDACIONALES
    episodes = [
        # EPISODIO 01
        {
            "num": "01",
            "base_name": "ep01_que_es_el_qi",
            "badge_es": "SERIE FUNDAMENTOS • EP. 01",
            "badge_en": "FOUNDATION SERIES • EP. 01",
            "title_es": "¿Qué es el Qi y cómo Transforma tu Salud?",
            "title_en": "What is Qi and How It Transforms Health",
            "sub_es": "La Ciencia de la Energía Vital",
            "sub_en": "The Science of Vital Energy",
            "color": (0, 225, 255),
            "cover_bg": str(BANCO_EXISTENTE / "ep01_que_es_el_qi_01.jpg"),
            "materials": [sd_nebula, p_clip1, curated_clips.get("ep01_res1", sd_cell), curated_clips.get("ep01_res2", p_clip3), sd_meridian],
            "script_es": (
                "¿Qué es realmente el Chi? Lejos de leyendas o misticismo, en Chineng Chikung entendemos el Chi "
                "como la sustancia y energía fundamental que sostiene todo en el universo. Es la fuerza viva que nutre "
                "tus células, regula tu sistema nervioso y recarga tu vitalidad diaria. Cuando el Chi es abundante "
                "y fluye sin obstáculos, el cuerpo activa su capacidad natural de autorregulación y la mente encuentra "
                "profunda serenidad. Cultivar tu Chi no es fantasía, es ciencia y entrenamiento diario."
            ),
            "script_en": (
                "What is Qi really? Beyond mysticism or fantasy, in ZhiNeng QiGong we understand Qi as the fundamental "
                "substance and vital energy that sustains everything in the universe. It is the living force nourishing your cells, "
                "regulating your nervous system, and restoring your daily vitality. When Qi is abundant and flows freely, the body "
                "activates its natural self-healing capacity while the mind attains profound serenity. Cultivating your Qi is not magic; "
                "it is daily scientific practice."
            ),
            "desc_es": "Descubre qué es el Qì (气) desde la perspectiva científica del ZhiNeng QiGong y cómo transforma tu salud y vitalidad.",
            "desc_en": "Discover what Qi (气) truly is from the scientific lens of ZhiNeng QiGong and how it restores natural vitality.",
            "tags_es": "Que es el Qi, ZhiNeng QiGong, Chi Kung, Energia Vital, Salud Holistica, Autocuracion, Pang Ming, Hunyuan Qi",
            "tags_en": "What is Qi, ZhiNeng QiGong, Chi Kung, Vital Energy, Holistic Health, Self Healing, Pang Ming, Hunyuan Qi",
            "hashtags_es": "#ZhiNengQiGong #Qi #EnergiaVital #SanacionHolistica #BienestarNatural",
            "hashtags_en": "#ZhiNengQiGong #Qi #VitalEnergy #HolisticHealing #Mindfulness",
            "copy_ig_es": "¿Sabías que el Qì no es misticismo sino ciencia de la energía vital? Aprende cómo nutrir tus células hoy mismo.",
            "copy_ig_en": "Qi is not mysticism; it is the fundamental science of vital energy. Learn how to cultivate yours today."
        },
        # EPISODIO 02
        {
            "num": "02",
            "base_name": "ep02_que_es_zhineng_qigong",
            "badge_es": "SERIE FUNDAMENTOS • EP. 02",
            "badge_en": "FOUNDATION SERIES • EP. 02",
            "title_es": "ZhiNeng QiGong: Ciencia y Conciencia Humana",
            "title_en": "ZhiNeng QiGong: Science and Human Consciousness",
            "sub_es": "El Legado del Dr. Pang Ming",
            "sub_en": "The Legacy of Dr. Pang Ming",
            "color": (255, 200, 80),
            "cover_bg": str(BANCO_EXISTENTE / "ep02_que_es_zhineng_qigong_res1.jpg"),
            "materials": [curated_clips.get("ep02_res1", sd_mind), p_clip2, curated_clips.get("ep02_res2", sd_meridian), p_clip4, sd_cell],
            "script_es": (
                "¿Qué hace diferente a Chineng Chikung de otras disciplinas? Creado por el Doctor Pang Ming, médico "
                "occidental y tradicional, es un sistema científico de desarrollo de la conciencia y salud integral. "
                "No consiste en simples movimientos físicos, sino en la unión armónica entre mente, cuerpo y Chi. "
                "A través de métodos precisos, entrenamos a la mente para guiar la energía a donde el cuerpo más lo necesita. "
                "Es el arte de convertirte en el arquitecto consciente de tu propia salud."
            ),
            "script_en": (
                "What makes ZhiNeng QiGong unique? Founded by Dr. Pang Ming, a master of both Western and Traditional Chinese Medicine, "
                "it is a scientific methodology of consciousness development and holistic health. It is not merely physical movement, "
                "but the harmonious integration of mind, body, and Qi. Through precise practice, we train the mind to guide energy "
                "where the body needs it most, empowering you to become the conscious creator of your own health."
            ),
            "desc_es": "¿Qué es el ZhiNeng QiGong y quién es el Dr. Pang Ming? Conoce el sistema científico de medicina energética más riguroso.",
            "desc_en": "What is ZhiNeng QiGong and who is Dr. Pang Ming? Learn the most rigorous medical energy science created in modern times.",
            "tags_es": "ZhiNeng QiGong, Dr Pang Ming, Medicina Tradicional China, Mente y Cuerpo, Salud y Conciencia, Qigong Cientifico",
            "tags_en": "ZhiNeng QiGong, Dr Pang Ming, Traditional Chinese Medicine, Mind Body Connection, Holistic Wellness, Qigong Science",
            "hashtags_es": "#ZhiNengQiGong #DrPangMing #Conciencia #SaludIntegral #MedicinaEnergetica",
            "hashtags_en": "#ZhiNengQiGong #DrPangMing #Consciousness #MindBody #EnergyMedicine",
            "copy_ig_es": "ZhiNeng QiGong: Donde la ciencia médica se encuentra con la energía vital. Descubre el legado del Dr. Pang Ming.",
            "copy_ig_en": "ZhiNeng QiGong: Where medical science unites with vital energy. Discover the profound legacy of Dr. Pang Ming."
        },
        # EPISODIO 03
        {
            "num": "03",
            "base_name": "ep03_el_campo_de_qi",
            "badge_es": "SERIE FUNDAMENTOS • EP. 03",
            "badge_en": "FOUNDATION SERIES • EP. 03",
            "title_es": "El Campo de Qi (Qi Chang): Sincronía Colectiva",
            "title_en": "The Qi Field (Qi Chang): Collective Resonance",
            "sub_es": "Resonancia y Mente Grupal",
            "sub_en": "Synchronization and Healing Field",
            "color": (160, 100, 255),
            "cover_bg": str(BANCO_EXISTENTE / "ep03_el_campo_de_qi_res1.jpg"),
            "materials": [curated_clips.get("ep03_res1", sd_nebula), p_clip3, curated_clips.get("ep03_res2", sd_meridian), p_clip5, sd_mind],
            "script_es": (
                "¿Has sentido alguna vez la fuerza multiplicada de meditar o entrenar en grupo? En Chineng Chikung "
                "esto se conoce como Chi Chang, o el Campo de Chi. Es un espacio cuántico donde la intención, el corazón "
                "y la energía de muchas personas se sincronizan para crear una resonancia colectiva de sanación. "
                "Al conectarte al campo, tu práctica se profundiza diez veces más que al practicar solo. "
                "En el campo de Chi, la salud de uno es el impulso y la fuerza de todos."
            ),
            "script_en": (
                "Have you ever experienced the multiplied strength of meditating in a group? In ZhiNeng QiGong, "
                "this is known as the Qi Chang, or the Qi Field. It is a space where the focused intention and energy of many individuals "
                "synchronize to form a powerful collective resonance of healing. When you connect to the Qi Field, your practice deepens "
                "tenfold compared to practicing alone. Within the field, individual wellness uplifts everyone."
            ),
            "desc_es": "El Campo de Qì (Qì Chǎng): Cómo la intención colectiva multiplica los resultados de tu práctica y sanación.",
            "desc_en": "The Qi Field (Qi Chang): How collective synchronized intention accelerates personal healing and inner peace.",
            "tags_es": "Campo de Qi, Qi Chang, Resonancia Colectiva, Meditacion Grupal, Sanacion Cuantica, ZhiNeng QiGong",
            "tags_en": "Qi Field, Qi Chang, Collective Resonance, Group Meditation, Energy Healing, ZhiNeng QiGong",
            "hashtags_es": "#CampoDeQi #QiChang #ResonanciaColectiva #ZhiNengQiGong #SanacionGrupal",
            "hashtags_en": "#QiField #QiChang #CollectiveHealing #ZhiNengQiGong #Meditation",
            "copy_ig_es": "Cuando mentes y corazones se sincronizan, el Campo de Qì hace posible lo extraordinario.",
            "copy_ig_en": "When conscious minds harmonize, the collective Qi Field awakens extraordinary healing."
        },
        # EPISODIO 04
        {
            "num": "04",
            "base_name": "ep04_el_qi_primordial",
            "badge_es": "TEORÍA HUNYUAN • EP. 04",
            "badge_en": "HUNYUAN THEORY • EP. 04",
            "title_es": "El Qi Primordial (Hunyuan Qi): Fuente Infinita",
            "title_en": "The Primordial Qi (Hunyuan Qi): Infinite Source",
            "sub_es": "La Sustancia Pura de la Naturaleza",
            "sub_en": "The Boundless Universal Energy",
            "color": (0, 225, 255),
            "cover_bg": str(BANCO_EXISTENTE / "ep04_el_qi_primordial_res1.jpg"),
            "materials": [sd_nebula, curated_clips.get("ep04_res1", p_clip4), curated_clips.get("ep04_res2", sd_cell), p_clip1, sd_meridian],
            "script_es": (
                "Todo en el universo proviene de una sola fuente inagotable: el Hunyuan Chi. "
                "En la teoría de Chineng Chikung, el Hunyuan Chi es la sustancia primordial informe de donde nacen la materia, "
                "la energía y la información. A diferencia de otros sistemas de energía, el Hunyuan Chi no tiene límites ni desgaste. "
                "Al practicar Chineng Chikung, no gastas tu propia energía vital, sino que te conectas directamente "
                "con la abundancia infinita de la naturaleza. Aprende a nutrir tu vida desde la fuente pura."
            ),
            "script_en": (
                "Everything in the cosmos originates from a single inexhaustible source: Hunyuan Qi. In ZhiNeng QiGong theory, "
                "Hunyuan Qi is the formless primordial substance giving rise to matter, energy, and information. Unlike systems that drain "
                "your personal energy reserves, ZhiNeng QiGong connects you directly to nature's limitless abundance. "
                "You do not deplete yourself; you recharge directly from the universal source."
            ),
            "desc_es": "La Teoría del Hùnyuán Qì: La fuente inagotable de energía primordial que nutre todo lo vivo.",
            "desc_en": "The Theory of Hunyuan Qi: The infinite reservoir of primordial energy that nourishes all existence.",
            "tags_es": "Hunyuan Qi, Qi Primordial, Teoria Hunyuan, Pang Ming, Energia Cósmica, ZhiNeng QiGong",
            "tags_en": "Hunyuan Qi, Primordial Qi, Hunyuan Theory, Pang Ming, Universal Energy, ZhiNeng QiGong",
            "hashtags_es": "#HunyuanQi #QiPrimordial #EnergiaUniversal #ZhiNengQiGong #Vitalidad",
            "hashtags_en": "#HunyuanQi #PrimordialEnergy #UniversalQi #ZhiNengQiGong #Vitality",
            "copy_ig_es": "No gastes tu propia energía: conéctate al Hùnyuán Qì inagotable de la naturaleza.",
            "copy_ig_en": "Never drain your personal battery: plug directly into nature's infinite Hunyuan Qi."
        },
        # EPISODIO 05
        {
            "num": "05",
            "base_name": "ep05_las_tres_capas",
            "badge_es": "TEORÍA HUNYUAN • EP. 05",
            "badge_en": "HUNYUAN THEORY • EP. 05",
            "title_es": "La Teoría de las Tres Capas: Materia, Energía e Información",
            "title_en": "The Three Layers: Matter, Energy, and Information",
            "sub_es": "Sanación desde la Información Pura",
            "sub_en": "Healing Through Pure Information",
            "color": (255, 200, 80),
            "cover_bg": str(BANCO_EXISTENTE / "ep05_las_tres_capas_res1.jpg"),
            "materials": [curated_clips.get("ep05_res1", sd_cell), p_clip2, curated_clips.get("ep05_res2", sd_mind), p_clip6, sd_nebula],
            "script_es": (
                "¿Sabías que la materia es solo la capa más superficial de la realidad? El Doctor Pang Ming explicó que todo "
                "existe en tres capas: materia, energía e información. La medicina convencional trabaja principalmente en la materia. "
                "Chineng Chikung opera desde la capa de la información. Cuando transformas la información en tu mente y tu campo, "
                "el Chi se reorganiza de inmediato y la materia en tus células se regenera naturalmente. "
                "Cambia tu información y transformarás tu biología."
            ),
            "script_en": (
                "Did you know physical matter is merely the surface layer of reality? Dr. Pang Ming explained that everything "
                "exists across three interconnected levels: Matter, Energy, and Information. While conventional medicine treats physical matter, "
                "ZhiNeng QiGong works at the causal layer of information. When you transform the information within your consciousness, "
                "Qi instantly reorganizes, and physical cells regenerate naturally. Shift your information, and you transform your biology."
            ),
            "desc_es": "Las Tres Capas de la Realidad: Cómo sanar el cuerpo físico transformando la información en la mente.",
            "desc_en": "The Three Layers of Reality: How shifting conscious information reorganizes energy and heals physical biology.",
            "tags_es": "Tres Capas, Materia Energia Informacion, Pang Ming, Epigenetica, Medicina Cuantica, ZhiNeng QiGong",
            "tags_en": "Three Layers Theory, Matter Energy Information, Pang Ming, Epigenetics, Quantum Healing, ZhiNeng QiGong",
            "hashtags_es": "#TresCapas #InformacionConsciente #BiologiaCuantica #ZhiNengQiGong #Autocuracion",
            "hashtags_en": "#ThreeLayers #ConsciousInformation #QuantumBiology #ZhiNengQiGong #MindOverMatter",
            "copy_ig_es": "Tu cuerpo físico obedece a tu información mental. Cambia tu información y sanarás tu materia.",
            "copy_ig_en": "Physical biology follows conscious information. Transform your mind, and your cells will follow."
        },
        # EPISODIO 06
        {
            "num": "06",
            "base_name": "ep06_la_mente_guia_al_qi",
            "badge_es": "TEORÍA HUNYUAN • EP. 06",
            "badge_en": "HUNYUAN THEORY • EP. 06",
            "title_es": "La Mente Guía al Qi (Yi Dao Qi Dao)",
            "title_en": "Where Mind Goes, Qi Flows (Yi Dao Qi Dao)",
            "sub_es": "El Poder de la Intención Enfocada",
            "sub_en": "The Power of Focused Intention",
            "color": (160, 100, 255),
            "cover_bg": str(BANCO_EXISTENTE / "ep06_la_mente_guia_al_qi_res2.jpg"),
            "materials": [curated_clips.get("ep06_res2", sd_mind), p_clip3, curated_clips.get("ep06_res1", sd_meridian), p_clip7, sd_cell],
            "script_es": (
                "A donde va tu atención, va tu energía. En Chineng Chikung este principio fundamental se llama Yinian: "
                "la mente dirige al Chi. Si tu atención vive dispersa en el estrés y la preocupación constante, tu energía "
                "vital se fuga y agota tus defensas. Pero cuando enfocas tu intención con serenidad y presencia dentro del cuerpo, "
                "el Chi sigue a la mente y revitaliza cada tejido. Domina tu mente y tomarás las riendas de tu vitalidad."
            ),
            "script_en": (
                "Where your attention goes, energy flows. In ZhiNeng QiGong, this cornerstone axiom is known as Yi Dao Qi Dao: "
                "the mind directs the Qi. When attention is scattered in chronic stress and anxious loops, life energy leaks away. "
                "However, when you place calm, focused intention within the body, Qi immediately follows the mind, revitalizing "
                "every cell and tissue. Master your mind, and you hold the steering wheel of your vitality."
            ),
            "desc_es": "Yì Dào Qì Dào: El principio milenario que demuestra cómo la mente dirige la energía hacia la salud.",
            "desc_en": "Yi Dao Qi Dao: The core principle demonstrating how conscious focus commands the flow of vital Qi.",
            "tags_es": "La Mente Guia al Qi, Yi Dao Qi Dao, Atencion Plena, Foco Mental, Sanacion Mental, ZhiNeng QiGong",
            "tags_en": "Mind Directs Qi, Yi Dao Qi Dao, Focused Intention, Mindfulness, Mental Healing, ZhiNeng QiGong",
            "hashtags_es": "#YiDaoQiDao #MenteYQi #IntencionPura #ZhiNengQiGong #FocoMental",
            "hashtags_en": "#YiDaoQiDao #MindDirectsQi #Intention #ZhiNengQiGong #Mindfulness",
            "copy_ig_es": "¿Hacia dónde estás enviando tu energía hoy? Recuerda: a donde va tu mente, fluye tu Qì.",
            "copy_ig_en": "Where are you directing your energy today? Remember: wherever your mind goes, your Qi flows."
        },
        # EPISODIO 07 (HUAXIA EXCLUSIVO 1)
        {
            "num": "07",
            "base_name": "ep07_el_hospital_sin_medicinas",
            "badge_es": "EVIDENCIA HUAXIA • EP. 07",
            "badge_en": "HUAXIA EVIDENCE • EP. 07",
            "title_es": "El Hospital Sin Medicinas: Centro Huaxia",
            "title_en": "The Medicineless Hospital: Huaxia Center",
            "sub_es": "El Mayor Experimento de Sanación Humana",
            "sub_en": "The Greatest Human Healing Experiment",
            "color": (255, 200, 80),
            "cover_bg": str(BANCO_EXISTENTE / "ep07_el_hospital_sin_medicinas_res1.jpg"),
            "materials": [huaxia_campus, curated_clips.get("ep07_res1", sd_cell), huaxia_healing, curated_clips.get("ep07_res2", p_clip2), huaxia_scientific],
            "script_es": (
                "¿Imaginas un hospital con miles de personas donde no se recetaba ni un solo fármaco? En China existió el Centro Huaxia, "
                "el hospital sin medicinas fundado por el Doctor Pang Ming. Durante más de una década, cientos de miles de practicantes "
                "demostraron que el cuerpo puede autorregularse mediante la práctica intensiva de Chineng Chikung y el campo de Chi. "
                "Con una tasa de efectividad médica superior al noventa y cuatro por ciento en más de ciento ochenta padecimientos, "
                "Huaxia demostró el potencial ilimitado de la conciencia humana."
            ),
            "script_en": (
                "Can you imagine a hospital caring for thousands of patients where not a single pharmaceutical drug was prescribed? "
                "In China, the Huaxia Center stood as the world's largest medicineless hospital, founded by Dr. Pang Ming. "
                "For over a decade, hundreds of thousands of practitioners proved that the body can self-regulate through intensive "
                "ZhiNeng QiGong practice and collective Qi fields. Achieving over a ninety-four percent effectiveness rate across "
                "more than one hundred eighty chronic conditions, Huaxia proved the boundless healing power of human consciousness."
            ),
            "desc_es": "El Hospital Huaxia: El legendario centro sin medicamentos donde miles de personas sanaron con ZhiNeng QiGong.",
            "desc_en": "The Huaxia Medicineless Hospital: The legendary clinic where thousands restored health through ZhiNeng QiGong.",
            "tags_es": "Hospital Sin Medicinas, Centro Huaxia, Dr Pang Ming, Sanacion Natural, Autocuracion, ZhiNeng QiGong",
            "tags_en": "Medicineless Hospital, Huaxia Center, Dr Pang Ming, Natural Healing, Self Healing, ZhiNeng QiGong",
            "hashtags_es": "#HospitalSinMedicinas #CentroHuaxia #DrPangMing #ZhiNengQiGong #SaludNatural",
            "hashtags_en": "#MedicinelessHospital #HuaxiaCenter #DrPangMing #ZhiNengQiGong #NaturalHealing",
            "copy_ig_es": "Un hospital sin farmacia ni fármacos: así funcionó el Centro Huaxia con ZhiNeng QiGong.",
            "copy_ig_en": "A hospital without pills or pharmacies: how the Huaxia Center transformed medicine with ZhiNeng QiGong."
        },
        # EPISODIO 08 (HUAXIA EXCLUSIVO 2)
        {
            "num": "08",
            "base_name": "ep08_estudiante_vs_paciente",
            "badge_es": "EVIDENCIA HUAXIA • EP. 08",
            "badge_en": "HUAXIA EVIDENCE • EP. 08",
            "title_es": "De Paciente Pasivo a Estudiante Autónomo",
            "title_en": "From Passive Patient to Autonomous Student",
            "sub_es": "La Filosofía que Cambió la Medicina",
            "sub_en": "The Philosophy that Transformed Medicine",
            "color": (0, 225, 255),
            "cover_bg": str(BANCO_EXISTENTE / "ep08_estudiante_vs_paciente_res1.jpg"),
            "materials": [huaxia_care, curated_clips.get("ep08_res1", sd_mind), huaxia_healing, curated_clips.get("ep08_res2", p_clip1), huaxia_campus],
            "script_es": (
                "En el hospital de Huaxia estaba prohibido llamar a las personas pacientes; se les llamaba estudiantes. "
                "¿Por qué esta distinción? Porque un paciente asume una actitud pasiva, esperando que alguien externo lo cure. "
                "Un estudiante, en cambio, aprende una ciencia de vida para cultivar y restaurar su propia salud. "
                "El verdadero cambio comienza cuando dejas de ser víctima de una condición y asumes el liderazgo de tu propia biología."
            ),
            "script_en": (
                "At the Huaxia Center, people were never called patients; they were called students. Why this profound distinction? "
                "Because a patient assumes a passive role, waiting for an external doctor to fix them. A student, on the other hand, "
                "learns an art of living to cultivate, master, and restore their own vitality. True healing begins the moment you stop "
                "viewing yourself as a passive victim and step up as the empowered student of your own body."
            ),
            "desc_es": "Estudiante vs Paciente: La clave mental de Huaxia para recuperar la autonomía de tu salud.",
            "desc_en": "Student vs Patient: The mental shift taught at Huaxia to reclaim sovereignty over personal vitality.",
            "tags_es": "Estudiante vs Paciente, Autonomia en Salud, Centro Huaxia, Empoderamiento, Sanacion Consciente, ZhiNeng QiGong",
            "tags_en": "Student vs Patient, Health Sovereignty, Huaxia Center, Empowerment, Conscious Healing, ZhiNeng QiGong",
            "hashtags_es": "#EstudianteDeSalud #Autonomia #CentroHuaxia #ZhiNengQiGong #PoderInterior",
            "hashtags_en": "#HealthSovereignty #HuaxiaCenter #Empowerment #ZhiNengQiGong #SelfCare",
            "copy_ig_es": "No seas paciente pasivo; conviértete en estudiante activo de tu propia vida y salud.",
            "copy_ig_en": "Stop being a passive patient; become the conscious student and master of your own vitality."
        },
        # EPISODIO 09 (HUAXIA EXCLUSIVO 3)
        {
            "num": "09",
            "base_name": "ep09_evidencia_sanacion",
            "badge_es": "EVIDENCIA HUAXIA • EP. 09",
            "badge_en": "HUAXIA EVIDENCE • EP. 09",
            "title_es": "101 Milagros y Evidencia Científica",
            "title_en": "101 Miracles and Scientific Evidence",
            "sub_es": "Disolución en Ultrasonido y Estudios Médicos",
            "sub_en": "Ultrasound Dissolution and Clinical Records",
            "color": (160, 100, 255),
            "cover_bg": str(BANCO_EXISTENTE / "ep09_evidencia_de_sanacion_res1.jpg"),
            "materials": [huaxia_scientific, curated_clips.get("ep09_res1", sd_cell), huaxia_healing, curated_clips.get("ep09_res2", p_clip5), huaxia_campus],
            "script_es": (
                "En el libro Ciento un Milagros de Sanación Natural se documentan recuperaciones asombrosas en Huaxia: "
                "desde tumores y artritis severa hasta parálisis. Médicos y científicos internacionales filmaron la disolución "
                "de masas en tiempo real en pantallas de ultrasonido en menos de un minuto, mientras los practicantes sincronizaban el campo de Chi. "
                "No fue magia ni milagro sobrenatural: fue la ciencia del Chi y la intención pura despertando la capacidad autorreguladora del cuerpo."
            ),
            "script_en": (
                "Documented in the clinical records of 101 Miracles of Natural Healing are astonishing recoveries at Huaxia: "
                "from severe tumors to paralysis and chronic organ failure. International scientists and physicians filmed the dissolution "
                "of solid masses in real time on ultrasound monitors in under one minute while practitioners focused the Qi Field. "
                "It was not magic or superstition: it was the rigorous science of Qi awakening the body's innate self-healing genius."
            ),
            "desc_es": "101 Milagros de Sanación: Los estudios médicos y ultrasonidos en tiempo real documentados en Huaxia.",
            "desc_en": "101 Miracles of Natural Healing: Real-time ultrasound evidence and clinical breakthroughs from Huaxia.",
            "tags_es": "101 Milagros, Evidencia Cientifica, Ultrasonido Huaxia, Sanacion en Vivo, Dr Pang Ming, ZhiNeng QiGong",
            "tags_en": "101 Miracles, Scientific Evidence, Ultrasound Huaxia, Real Time Healing, Dr Pang Ming, ZhiNeng QiGong",
            "hashtags_es": "#101Milagros #EvidenciaCientifica #CentroHuaxia #ZhiNengQiGong #CienciaEnergetica",
            "hashtags_en": "#101Miracles #ScientificProof #HuaxiaCenter #ZhiNengQiGong #EnergyScience",
            "copy_ig_es": "Disolución de tumores documentada en ultrasonido: la ciencia del Qì en acción en Huaxia.",
            "copy_ig_en": "Real-time tumor dissolution documented on ultrasound: witness the power of conscious Qi science."
        },
        # EPISODIO 10
        {
            "num": "10",
            "base_name": "ep10_peng_qi_guan_ding_fa",
            "badge_es": "MÉTODOS Y PRÁCTICA • EP. 10",
            "badge_en": "PRACTICE METHODS • EP. 10",
            "title_es": "Peng Qi Guan Ding Fa: Levantar y Verter el Qi",
            "title_en": "Peng Qi Guan Ding Fa: Lift Qi Up, Pour Qi Down",
            "sub_es": "El Primer Método Fundamental de ZNQG",
            "sub_en": "The Foundation Level 1 Method",
            "color": (0, 225, 255),
            "cover_bg": str(BANCO_EXISTENTE / "ep10_peng_qi_guan_ding_fa_res1.jpg"),
            "materials": [curated_clips.get("ep10_res1", sd_meridian), p_clip1, curated_clips.get("ep10_res2", sd_cell), p_clip4, sd_nebula],
            "script_es": (
                "Peng Chi Guan Ding Fa, o Levantar el Chi y Verterlo por la Cabeza, es el método fundamental del primer nivel "
                "de Chineng Chikung. A través de movimientos fluidos y apertura mental, abrimos los poros y canales del cuerpo "
                "para liberar el Chi turbio e integrar el Hunyuan Chi puro de la naturaleza. Es el método practicado por millones "
                "para restaurar el sistema inmunológico y mantener una vitalidad desbordante todos los días."
            ),
            "script_en": (
                "Peng Qi Guan Ding Fa, or Lift Qi Up and Pour Qi Down, is the cornerstone Level 1 method of ZhiNeng QiGong. "
                "Through graceful, circular movements and expanded awareness, we open the body's pores and energy channels, releasing "
                "turbid Qi while infusing pure universal Hunyuan Qi through the crown of the head. Millions practice this daily "
                "to restore their immune system and sustain radiant health."
            ),
            "desc_es": "Pěng Qì Guàn Dǐng Fǎ: Aprende el método esencial de nivel 1 para intercambiar Qì con el universo.",
            "desc_en": "Peng Qi Guan Ding Fa: Master the essential Level 1 practice to exchange Qi directly with nature.",
            "tags_es": "Peng Qi Guan Ding Fa, Levantar el Qi, Nivel 1 ZhiNeng QiGong, Rutina de Qigong, Salud Inmune",
            "tags_en": "Peng Qi Guan Ding Fa, Lift Qi Up, Level 1 ZhiNeng QiGong, Qigong Routine, Immune Health",
            "hashtags_es": "#PengQiGuanDingFa #LevantarElQi #Nivel1 #ZhiNengQiGong #SaludNatural",
            "hashtags_en": "#PengQiGuanDingFa #LiftQiUp #Level1 #ZhiNengQiGong #VitalEnergy",
            "copy_ig_es": "Abre tus canales y recarga tu vitalidad con Pěng Qì Guàn Dǐng Fǎ: el método base de ZhiNeng QiGong.",
            "copy_ig_en": "Open your energy gates and revitalize your body with Peng Qi Guan Ding Fa: the core practice of ZhiNeng QiGong."
        },
        # EPISODIO 11
        {
            "num": "11",
            "base_name": "ep11_dun_qiang_gong",
            "badge_es": "MÉTODOS Y PRÁCTICA • EP. 11",
            "badge_en": "PRACTICE METHODS • EP. 11",
            "title_es": "Dun Qiang Gong: Sentadillas frente a la Pared",
            "title_en": "Dun Qiang Gong: Wall Squat Mastery",
            "sub_es": "El Método Atajo para la Columna y Riñones",
            "sub_en": "The Master Shortcut for Spine and Kidneys",
            "color": (255, 200, 80),
            "cover_bg": str(BANCO_EXISTENTE / "ep11_dun_qiang_gong_res1.jpg"),
            "materials": [curated_clips.get("ep11_res1", sd_spine), p_clip2, curated_clips.get("ep11_res2", sd_meridian), p_clip6, sd_cell],
            "script_es": (
                "Dun Qiang Gong, o las sentadillas frente a la pared, es conocido como el método atajo en Chineng Chikung. "
                "Al deslizar el cuerpo frente a una pared vertical, se estira y flexibiliza toda la columna vertebral, relajando la cintura "
                "y abriendo la puerta de Mingmen. Este método desbloquea rápidamente la energía en la espalda, fortalece los riñones "
                "y revitaliza todo tu cuerpo en solo unos minutos al día."
            ),
            "script_en": (
                "Dun Qiang Gong, or Wall Squats, is revered as the ultimate shortcut method in ZhiNeng QiGong. "
                "By smoothly squatting in front of a flat vertical wall, you flex and align every vertebra of the spine, relaxing the lumbar region "
                "and opening the vital gate of Mingmen. This practice rapidly unlocks stagnant energy along the back, strengthens kidney vitality, "
                "and supercharges your whole system in just minutes a day."
            ),
            "desc_es": "Dùn Qiáng Gōng: Las sentadillas frente a la pared para desbloquear la columna y fortalecer la puerta de Mìngmén.",
            "desc_en": "Dun Qiang Gong: Wall Squats to realign the spine, open Mingmen, and boost core kidney energy.",
            "tags_es": "Dun Qiang Gong, Sentadilla frente a la pared, Columna Vertebral, Mingmen, Fortalecer Rinones, ZhiNeng QiGong",
            "tags_en": "Dun Qiang Gong, Wall Squats, Spine Alignment, Mingmen Gate, Kidney Energy, ZhiNeng QiGong",
            "hashtags_es": "#DunQiangGong #SentadillasDePared #Mingmen #ColumnaSana #ZhiNengQiGong",
            "hashtags_en": "#DunQiangGong #WallSquats #SpineHealth #Mingmen #ZhiNengQiGong",
            "copy_ig_es": "El secreto de la columna y la juventud lumbar: descubre cómo practicar Dùn Qiáng Gōng correctamente.",
            "copy_ig_en": "The secret to spinal flexibility and deep vitality: discover the transformative power of Dun Qiang Gong."
        },
        # EPISODIO 12
        {
            "num": "12",
            "base_name": "ep12_el_estado_de_mingjue",
            "badge_es": "MÉTODOS Y PRÁCTICA • EP. 12",
            "badge_en": "PRACTICE METHODS • EP. 12",
            "title_es": "El Estado de Mingjue: Conciencia Despierta",
            "title_en": "The State of Mingjue: Awakened Consciousness",
            "sub_es": "El Observador Puro Más Allá del Ego",
            "sub_en": "The Pure Observer Beyond Ego",
            "color": (160, 100, 255),
            "cover_bg": str(BANCO_EXISTENTE / "ep12_el_estado_de_mingjue_res1.jpg"),
            "materials": [curated_clips.get("ep12_res1", sd_mind), p_clip3, curated_clips.get("ep12_res2", sd_nebula), p_clip7, sd_meridian],
            "script_es": (
                "Mingjue es el estado donde la conciencia se reconoce y observa a sí misma con absoluta pureza y serenidad. "
                "Al entrar en el estado de Mingjue, la mente trasciende el ruido mental, las emociones aflictivas y los apegos del ego, "
                "convirtiéndose en un espejo cristalino. Desde este estado de conciencia pura, la sanación, la claridad interior "
                "y la paz profunda ocurren de forma espontánea y sin esfuerzo."
            ),
            "script_en": (
                "Mingjue is the profound state where consciousness awakens to observe itself with unconditional clarity and stillness. "
                "Entering Mingjue allows the mind to transcend emotional turbulence, noisy mental chatter, and ego attachments, "
                "becoming like a luminous crystal mirror. From this vantage point of pure consciousness, deep healing, wisdom, "
                "and inner serenity unfold effortlessly."
            ),
            "desc_es": "Míngjué Gōngfu: Cómo alcanzar el estado de observador interno puro y trascender el estrés mental.",
            "desc_en": "Mingjue Gongfu: How to stabilize the pure internal observer and transcend daily mental stress.",
            "tags_es": "Mingjue, Conciencia Pura, Observador Interno, Meditacion Profunda, Trascendencia del Ego, ZhiNeng QiGong",
            "tags_en": "Mingjue, Pure Consciousness, Inner Observer, Deep Meditation, Ego Transcendence, ZhiNeng QiGong",
            "hashtags_es": "#Mingjue #ConcienciaPura #ObservadorInterno #PazMental #ZhiNengQiGong",
            "hashtags_en": "#Mingjue #PureConsciousness #InnerPeace #Awakening #ZhiNengQiGong",
            "copy_ig_es": "Sé el observador, no el drama: descubre el poder transformador de Míngjué en tu vida.",
            "copy_ig_en": "Be the calm observer, not the storm: awaken the transformative power of Mingjue consciousness."
        },
        # EPISODIO 13
        {
            "num": "13",
            "base_name": "ep13_los_8_versos",
            "badge_es": "TRASCENDENCIA • EP. 13",
            "badge_en": "TRANSCENDENCE • EP. 13",
            "title_es": "Los 8 Versos del Campo de Qi (Ding Tian Li Di)",
            "title_en": "The 8 Verses of the Qi Field (Ding Tian Li Di)",
            "sub_es": "Armonización Cósmica en 8 Frases",
            "sub_en": "Cosmic Alignment in Eight Verses",
            "color": (255, 200, 80),
            "cover_bg": str(BANCO_EXISTENTE / "ep13_los_8_versos_del_campo_res1.jpg"),
            "materials": [curated_clips.get("ep13_res1", sd_nebula), p_clip1, curated_clips.get("ep13_res2", sd_mind), p_clip5, sd_cell],
            "script_es": (
                "La cabeza toca el cielo, los pies firmes en la tierra. El cuerpo se relaja y la mente se expande hacia el infinito. "
                "Los ocho versos creados por el Doctor Pang Ming son la llave maestra para organizar el campo de Chi perfecto "
                "antes de cualquier práctica. Al entonar o contemplar estos versos, la mente entra en calma total "
                "y se funde en perfecta armonía con el cosmos. Es el puente sagrado entre el ser humano y el universo."
            ),
            "script_en": (
                "Head touches heaven, feet stand firm on earth. The body relaxes and mind expands into the boundless cosmic void. "
                "The Eight Verses composed by Dr. Pang Ming serve as the master key to establish the ideal Qi Field before every practice. "
                "Contemplating these verses quiets the internal dialogue and establishes profound resonance with the universe. "
                "They form the sacred bridge aligning human consciousness with cosmic harmony."
            ),
            "desc_es": "Los 8 Versos de ZhiNeng QiGong: La estructura para sincronizar mente, cuerpo y cosmos antes de practicar.",
            "desc_en": "The Eight Verses of ZhiNeng QiGong: The sacred framework to harmonize mind, body, and universe.",
            "tags_es": "Ocho Versos, Ding Tian Li Di, Campo de Qi, Dr Pang Ming, Meditacion Cosmica, ZhiNeng QiGong",
            "tags_en": "Eight Verses, Ding Tian Li Di, Qi Field, Dr Pang Ming, Cosmic Meditation, ZhiNeng QiGong",
            "hashtags_es": "#OchoVersos #DingTianLiDi #CampoDeQi #ArmoniaUniversal #ZhiNengQiGong",
            "hashtags_en": "#EightVerses #QiField #CosmicAlignment #InnerStillness #ZhiNengQiGong",
            "copy_ig_es": "La cabeza toca el cielo, los pies en la tierra: armoniza tu energía con los 8 versos de ZhiNeng QiGong.",
            "copy_ig_en": "Head touching heaven, feet rooted on earth: align your energy with the Eight Verses of ZhiNeng QiGong."
        },
        # EPISODIO 14
        {
            "num": "14",
            "base_name": "ep14_salud_longevidad",
            "badge_es": "TRASCENDENCIA • EP. 14",
            "badge_en": "TRANSCENDENCE • EP. 14",
            "title_es": "Cultivo de la Salud y Longevidad Activa",
            "title_en": "Cultivating Health and Active Longevity",
            "sub_es": "Prevención, Vigor y Vitalidad Plena",
            "sub_en": "Prevention, Vigor, and Lifelong Wellness",
            "color": (0, 225, 255),
            "cover_bg": str(BANCO_EXISTENTE / "ep14_salud_longevidad_res1.jpg"),
            "materials": [curated_clips.get("ep14_res1", sd_cell), p_clip2, curated_clips.get("ep14_res2", sd_spine), p_clip4, sd_meridian],
            "script_es": (
                "La verdadera medicina no es reaccionar a la enfermedad, sino cultivar la vitalidad diaria. "
                "Chineng Chikung no solo sirve para recuperarse de dolencias crónicas, sino para blindar tu sistema inmunológico, "
                "mantener tus órganos nutridos y disfrutar de una longevidad activa y lúcida. Al integrar la práctica en tu rutina, "
                "rejuveneces tus células y mantienes una mente despierta sin importar los años que tengas."
            ),
            "script_en": (
                "True healthcare is not merely treating symptoms; it is cultivating vibrant daily wellness. "
                "ZhiNeng QiGong not only helps reverse chronic illness, but fortifies your immune defenses, nourishes internal organs, "
                "and nurtures active, clear-minded longevity. By integrating conscious practice into your daily rhythm, you rejuvenate "
                "your cellular health and maintain youthful vitality regardless of chronological age."
            ),
            "desc_es": "Longevidad y Vitalidad: Cómo el ZhiNeng QiGong regenera tu cuerpo y fortalece tu sistema inmune cada día.",
            "desc_en": "Longevity and Vitality: How ZhiNeng QiGong cellular rejuvenation supports lifelong wellness.",
            "tags_es": "Longevidad Activa, Salud Celular, Sistema Inmunologico, Antienvejecimiento, Prevencion, ZhiNeng QiGong",
            "tags_en": "Active Longevity, Cellular Health, Immune Defense, Anti Aging, Prevention, ZhiNeng QiGong",
            "hashtags_es": "#Longevidad #SaludCelular #VitalidadDiaria #ZhiNengQiGong #BienestarIntegral",
            "hashtags_en": "#Longevity #CellularHealth #DailyVitality #ZhiNengQiGong #HolisticHealth",
            "copy_ig_es": "La verdadera juventud reside en el flujo abundante de tu Qì: cultiva tu longevidad cada día.",
            "copy_ig_en": "True youthfulness flows through abundant Qi: cultivate vibrant, active longevity every day."
        },
        # EPISODIO 15
        {
            "num": "15",
            "base_name": "ep15_practica_autonoma",
            "badge_es": "TRASCENDENCIA • EP. 15",
            "badge_en": "TRANSCENDENCE • EP. 15",
            "title_es": "Práctica Autónoma y Comunidad de Qi",
            "title_en": "Autonomous Practice and Qi Community",
            "sub_es": "Sembradores de Qì para el Mundo",
            "sub_en": "Qi Sowers for Global Wellness",
            "color": (160, 100, 255),
            "cover_bg": str(BANCO_EXISTENTE / "ep15_practica_autonoma_comunidad_res1.jpg"),
            "materials": [curated_clips.get("ep15_res1", sd_nebula), p_clip3, curated_clips.get("ep15_res2", sd_mind), p_clip5, sd_meridian],
            "script_es": (
                "El mayor regalo que te brinda Chineng Chikung es la soberanía sobre tu propia vida. Aprender a gestionar "
                "tu propia energía te libera del miedo y te devuelve el poder de cuidar de tu salud y la de tu familia. "
                "En Sembradores de Chi te acompañamos con sesiones, campo compartido y las bases teóricas para que camines con confianza. "
                "Sé parte de esta comunidad y comienza a transformar tu realidad hoy mismo."
            ),
            "script_en": (
                "The supreme gift of ZhiNeng QiGong is complete sovereignty over your own life. Learning to manage your own Qi "
                "frees you from anxiety and restores your innate power to care for your health and support your loved ones. "
                "At Qi Sowers, we walk alongside you with guided sessions, collective Qi fields, and pure teachings so you can flourish. "
                "Join our community and begin transforming your reality today."
            ),
            "desc_es": "Soberanía y Comunidad: Únete a Sembradores de Qì y haz del ZhiNeng QiGong tu estilo de vida consciente.",
            "desc_en": "Sovereignty and Community: Join Qi Sowers and make ZhiNeng QiGong your daily path to conscious wellness.",
            "tags_es": "Practica Autonoma, Sembradores de Qi, Comunidad Qigong, Soberania de Salud, Dr Pang Ming, ZhiNeng QiGong",
            "tags_en": "Autonomous Practice, Qi Sowers, Qigong Community, Health Sovereignty, Dr Pang Ming, ZhiNeng QiGong",
            "hashtags_es": "#SembradoresDeQi #PracticaAutonoma #ComunidadConsciente #ZhiNengQiGong #HunyuanLingTong",
            "hashtags_en": "#QiSowers #AutonomousPractice #ConsciousCommunity #ZhiNengQiGong #HunyuanLingTong",
            "copy_ig_es": "Recupera la soberanía sobre tu salud y tu energía: bienvenido a la comunidad de Sembradores de Qì.",
            "copy_ig_en": "Reclaim complete sovereignty over your health and energy: welcome to the Qi Sowers community."
        }
    ]

    # Diccionario de ortografía fonética estricta para subtítulos
    replacements_es = {
        "Chineng Chikung": "ZhiNeng QiGong",
        "Chi Chang": "Qì Chǎng",
        "Chi": "Qì",
        "Sembradores de Chi": "Sembradores de Qì",
        "Doctor Pang Ming": "Doctor Páng Míng",
        "Hunyuan Chi": "Hùnyuán Qì",
        "Yinian": "Yìniàn",
        "Peng Chi Guan Ding Fa": "Pěng Qì Guàn Dǐng Fǎ",
        "Dun Qiang Gong": "Dūn Qiáng Gōng",
        "Mingmen": "Mìngmén",
        "Mingjue": "Míngjué",
        "Ding Tian Li Di": "Dǐng Tiān Lì Dì"
    }

    replacements_en = {
        "Zhineng Qigong": "ZhiNeng QiGong",
        "Qi Chang": "Qì Chǎng",
        "Qi": "Qi",
        "Pang Ming": "Dr. Páng Míng",
        "Hunyuan Qi": "Hùnyuán Qì",
        "Yi Dao Qi Dao": "Yì Dào Qì Dào",
        "Peng Qi Guan Ding Fa": "Pěng Qì Guàn Dǐng Fǎ",
        "Dun Qiang Gong": "Dūn Qiáng Gōng",
        "Mingmen": "Mìngmén",
        "Mingjue": "Míngjué"
    }

    total_produced = 0

    # 6. BUCLE PRINCIPAL DE GENERACIÓN (15 EPISODIOS x 2 IDIOMAS = 30 VIDEOS)
    for ep in episodes:
        logger.info(f"\n>>> PROCESANDO EPISODIO {ep['num']}: {ep['title_es']} <<<")

        # 6.1 Portadas Sociales (ES y EN)
        generate_social_covers(
            title=ep["title_es"], subtitle=ep["sub_es"], badge=ep["badge_es"],
            theme_color=ep["color"], bg_image_path=ep["cover_bg"],
            base_name=ep["base_name"], lang="ES"
        )
        generate_social_covers(
            title=ep["title_en"], subtitle=ep["sub_en"], badge=ep["badge_en"],
            theme_color=ep["color"], bg_image_path=ep["cover_bg"],
            base_name=ep["base_name"], lang="EN"
        )

        # 6.2 Metadatos Sociales completos (YouTube, IG, TikTok)
        generate_social_metadata(ep, ep["base_name"])

        # 6.3 Video en Español (es-MX-JorgeNeural)
        out_es = OUTPUT_BASE / f"{ep['num']}_{ep['base_name']}_ES.mp4"
        logger.info(f"--- Generando Video ES: {out_es.name} ---")
        produce_single_video(
            video_subject=ep["title_es"],
            script_text=ep["script_es"],
            voice_name="es-MX-JorgeNeural-Male",
            materials=ep["materials"],
            out_path=out_es,
            replacements=replacements_es
        )
        total_produced += 1

        # 6.4 Video en Inglés (en-US-ChristopherNeural)
        out_en = OUTPUT_BASE / f"{ep['num']}_{ep['base_name']}_EN.mp4"
        logger.info(f"--- Generando Video EN: {out_en.name} ---")
        produce_single_video(
            video_subject=ep["title_en"],
            script_text=ep["script_en"],
            voice_name="en-US-ChristopherNeural-Male",
            materials=ep["materials"],
            out_path=out_en,
            replacements=replacements_en
        )
        total_produced += 1

        logger.info(f"Progreso global: {total_produced}/30 videos completados o procesados.")

    logger.success("===================================================================")
    logger.success("  ¡PRODUCCIÓN DE LOS 30 VIDEOS FUNDACIONALES FINALIZADA CON ÉXITO! ")
    logger.success("===================================================================")

if __name__ == "__main__":
    main()
