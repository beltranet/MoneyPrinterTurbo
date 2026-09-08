#!/usr/bin/env python3
"""
generate_qi_explainer_es_en.py
================================
Generador de videos de 1 minuto sobre "¿Qué es el Qì?" (Versión ES y Versión EN)
Utilizando Base de Conocimiento, Archivo Huaxia (clips 9:16) y Banco Curado.
"""

import os
import sys
import uuid
import shutil
from pathlib import Path
import subprocess
import imageio_ffmpeg
import re

CURRENT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(CURRENT_DIR))

from loguru import logger
from app.models.schema import VideoParams, VideoAspect, VideoConcatMode, VideoTransitionMode
from app.services import voice, task as task_service

FONT_BOLD = str(CURRENT_DIR / "resource" / "fonts" / "BeVietnamPro-Bold.ttf")

def add_audio_tail_padding(audio_path: str, padding_seconds: float = 1.0):
    if os.path.exists(audio_path):
        ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
        temp_path = audio_path + ".padded.mp3"
        cmd = [
            ffmpeg_exe,
            "-y",
            "-i", audio_path,
            "-af", f"apad=pad_dur={padding_seconds}",
            temp_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        os.replace(temp_path, audio_path)

def ensure_video_clip(media_path: str, cache_dir: Path, duration: int = 8) -> str:
    path = Path(media_path)
    if path.suffix.lower() in [".jpg", ".jpeg", ".png"]:
        out_clip = cache_dir / f"{path.stem}_{duration}s_916.mp4"
        if not out_clip.exists():
            ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
            cmd = [
                ffmpeg_exe,
                "-y",
                "-loop", "1",
                "-i", str(path),
                "-t", str(duration),
                "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-r", "25",
                str(out_clip)
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return str(out_clip)
    return str(path)

def generate_video_explainer(config: dict, output_dir: Path, cache_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    final_dest = output_dir / config["output_name"]

    logger.info(f"=== GENERANDO VIDEO: {config['title']} ({config['lang'].upper()}) ===")
    logger.info(f"Destino final: {final_dest}")

    # 1. Preparar y normalizar materiales a clips de video 9:16
    materials = []
    for m in config["materials"]:
        m_str = str(m)
        if os.path.exists(m_str):
            clip_path = ensure_video_clip(m_str, cache_dir, duration=8)
            materials.append(clip_path)
        else:
            logger.warning(f"Material no encontrado, omitiendo: {m_str}")

    if not materials:
        logger.error(f"No hay materiales válidos para {config['title']}")
        return False

    task_id = str(uuid.uuid4())
    task_dir = CURRENT_DIR / "storage" / "tasks" / task_id
    task_dir.mkdir(parents=True, exist_ok=True)

    audio_path = str(task_dir / "audio.mp3")
    subtitle_path = str(task_dir / "subtitle.srt")

    # 2. Síntesis de voz con Edge-TTS
    logger.info(f"Generando voz con: {config['voice_name']}...")
    sub_maker = voice.tts(
        text=config["phonetic_script"],
        voice_name=config["voice_name"],
        voice_rate=1.0,
        voice_file=audio_path,
        voice_volume=1.0
    )

    if sub_maker:
        voice.create_subtitle(
            sub_maker=sub_maker,
            text=config["phonetic_script"],
            subtitle_file=subtitle_path
        )

    add_audio_tail_padding(audio_path, padding_seconds=1.2)

    # 3. Sustitución robusta de términos fonéticos en subtítulos (.srt) con límites de palabra (\b)
    if os.path.exists(subtitle_path):
        with open(subtitle_path, "r", encoding="utf-8") as f:
            srt_content = f.read()

        replacements = config.get("replacements", {})
        sorted_replacements = sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True)
        for orig, repl in sorted_replacements:
            pattern = r'\b' + re.escape(orig) + r'\b'
            srt_content = re.sub(pattern, repl, srt_content, flags=re.IGNORECASE)

        # Reglas de protección estricta contra fragmentaciones y aberraciones de prefijo
        srt_content = re.sub(r'\bQì?neng\s+Qì?kung\b', 'ZhiNeng QiGong', srt_content, flags=re.IGNORECASE)
        srt_content = re.sub(r'\bQìna\b', 'China', srt_content)
        srt_content = re.sub(r'\bqìna\b', 'china', srt_content)

        with open(subtitle_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
        logger.info("Subtítulos sincronizados y tipografía ajustada con límites de palabra (\\b).")

    audio_duration = voice.get_audio_duration(audio_path)
    logger.info(f"Duración del audio de narración: {audio_duration:.2f} segundos")

    # 4. Configurar parámetros de renderizado
    video_params = VideoParams(
        video_subject=config["title"],
        video_script=config["phonetic_script"],
        video_source="local",
        video_materials=[{"url": m} for m in materials],
        video_concat_mode=VideoConcatMode.sequential,
        video_transition_mode=VideoTransitionMode.shuffle,
        video_clip_duration=7,
        video_aspect=VideoAspect.portrait,
        voice_name=config["voice_name"],
        subtitle_enabled=True,
        subtitle_position="custom",
        custom_position=60.0,
        font_name="BeVietnamPro-Bold.ttf" if os.path.exists(FONT_BOLD) else "MicrosoftYaHeiBold.ttc",
        text_fore_color="#FFFFFF",
        stroke_color="#000000",
        stroke_width=3,
        text_background_color="#000000",
        rounded_subtitle_background=True
    )

    # 5. Generar video final
    logger.info("Iniciando composición y renderizado final...")
    video_paths, combined_paths, warnings = task_service.generate_final_videos(
        task_id=task_id,
        params=video_params,
        downloaded_videos=materials,
        audio_file=audio_path,
        subtitle_path=subtitle_path,
        audio_duration=audio_duration
    )

    if video_paths and os.path.exists(video_paths[0]):
        shutil.copy(video_paths[0], final_dest)
        logger.success(f"✅ Video generado con éxito: {final_dest}")
        shutil.rmtree(task_dir, ignore_errors=True)
        return True
    else:
        logger.error(f"❌ Error al generar video: {config['title']}")
        return False

def main():
    output_dir = CURRENT_DIR / "storage" / "trilogia_fundacional" / "especial_que_es_el_qi"
    output_dir.mkdir(parents=True, exist_ok=True)

    cache_dir = CURRENT_DIR / "storage" / "cache_videos" / "especial_qi_clips"
    cache_dir.mkdir(parents=True, exist_ok=True)

    huaxia_dir = CURRENT_DIR / "storage" / "huaxia_archive" / "clips_916"
    banco_img_dir = CURRENT_DIR / "storage" / "local_videos" / "ai_generated" / "banco_imagenes_serie15"

    common_materials = [
        str(banco_img_dir / "ep01_que_es_el_qi_01.jpg"),
        str(huaxia_dir / "huaxia_mass_qifield_kaihe_916.mp4"),
        str(banco_img_dir / "ep05_las_tres_capas_res1.jpg"),
        str(banco_img_dir / "ep06_la_mente_guia_al_qi_res2.jpg"),
        str(huaxia_dir / "huaxia_collective_healing_916.mp4"),
        str(huaxia_dir / "huaxia_scientific_tests_916.mp4"),
        str(banco_img_dir / "ep04_el_qi_primordial_res2.jpg"),
    ]

    videos = [
        # 1. VERSIÓN ESPAÑOL
        {
            "lang": "es",
            "title": "¿Qué es el Qì?",
            "output_name": "Que_es_el_Qi_ES_1080x1920.mp4",
            "voice_name": "es-MX-JorgeNeural",
            "phonetic_script": (
                "¿Qué es realmente el Chi? Lejos de conceptos místicos o leyendas, en Chineng Chikung y la Teoría "
                "de la Completud Hunyuan, el Chi es la sustancia y energía fundamental que compone todo en el universo. "
                "La ciencia moderna y la sabiduría milenaria coinciden en que la materia tiene tres capas: "
                "masa física, energía y la información que la organiza. El Chi es el puente vivo que une tu cuerpo físico "
                "con tu mente consciente. Cuando el Chi es abundante y fluye sin bloqueos por tus meridianos, tus células "
                "se regeneran, tu sistema inmune se fortalece y tu mente alcanza una profunda paz. El mayor descubrimiento "
                "de Chineng Chikung es que el Chi sigue a la conciencia: a donde va tu atención, fluye el Chi. "
                "Al aprender a cultivar y dirigir tu energía vital, recuperas el control total de tu salud y tu bienestar."
            ),
            "replacements": {
                "Chineng Chikung": "ZhiNeng QiGong",
                "Doctor Pang Ming": "Dr. Pang Ming",
                "Chi": "Qi"
            },
            "materials": common_materials
        },
        # 2. VERSIÓN INGLÉS
        {
            "lang": "en",
            "title": "What is Qi?",
            "output_name": "What_is_Qi_EN_1080x1920.mp4",
            "voice_name": "en-US-ChristopherNeural",
            "phonetic_script": (
                "What is Qi? Far from being a mystical myth, in ZhiNeng Qigong and the Hunyuan Entirety Theory, "
                "Qi is the fundamental substance and energy that connects everything in the universe. Both ancient "
                "wisdom and modern physics reveal that matter exists in three layers: physical mass, energy, and information. "
                "Qi is the living bridge between your physical body and your conscious mind. When your Qi is abundant "
                "and flows freely throughout your body, your cells regenerate, your immune system strengthens, and your "
                "mind enters deep peace and clarity. The greatest breakthrough of ZhiNeng Qigong is that Qi follows consciousness: "
                "where your attention goes, Qi flows. By learning to cultivate and guide your vital energy, you reclaim "
                "absolute autonomy over your health, vitality, and life."
            ),
            "replacements": {
                "ZhiNeng Qigong": "ZhiNeng QiGong",
                "Doctor Pang Ming": "Dr. Pang Ming",
                "Qi": "Qi"
            },
            "materials": common_materials
        }
    ]

    for v in videos:
        success = generate_video_explainer(v, output_dir, cache_dir)
        if not success:
            logger.error(f"Fallo en la producción de {v['output_name']}")

    logger.success("=== PRODUCCIÓN COMPLETADA DE AMBOS VIDEOS ===")

if __name__ == "__main__":
    main()
