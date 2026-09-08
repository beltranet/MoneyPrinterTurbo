#!/usr/bin/env python3
"""
Poblador de Banco de Imágenes y Videos para la Serie de 15 Videos de ZhiNeng QiGong
Descarga recursos fotorrealistas verticales (9:16) en alta definición desde Pexels 
para garantizar máxima variedad visual sin repeticiones en cada uno de los 15 episodios.
"""

import os
import json
import urllib.request
from pathlib import Path

PEXELS_KEY = "sMqMa5QLLlrCLI5aXwdeYqen8YEjMTfRFNifC6j1sZsuM3d6qvM2JUkM"
BASE_DIR = Path(__file__).parent.resolve()
BANCO_DIR = BASE_DIR / "storage" / "local_videos" / "ai_generated" / "banco_imagenes_serie15"
BANCO_DIR.mkdir(parents=True, exist_ok=True)

EPISODES_TOPICS = [
    {
        "num": "01",
        "name": "ep01_que_es_el_qi",
        "query": "meditation energy light",
        "title": "¿Qué es el Qì?"
    },
    {
        "num": "02",
        "name": "ep02_que_es_zhineng_qigong",
        "query": "qigong movement nature",
        "title": "¿Qué es Zhìnéng Qìgōng?"
    },
    {
        "num": "03",
        "name": "ep03_el_campo_de_qi",
        "query": "group meditation outdoors",
        "title": "El Campo de Qì (Qì Chǎng)"
    },
    {
        "num": "04",
        "name": "ep04_el_qi_primordial",
        "query": "nebula cosmos stars galaxy",
        "title": "El Qì Primordial (Hùnyuán Qì)"
    },
    {
        "num": "05",
        "name": "ep05_las_tres_capas",
        "query": "particles glowing abstract blue",
        "title": "La Teoría de las Tres Capas"
    },
    {
        "num": "06",
        "name": "ep06_la_mente_guia_al_qi",
        "query": "peaceful face serene meditation",
        "title": "La Mente Guía al Qì"
    },
    {
        "num": "07",
        "name": "ep07_el_hospital_sin_medicinas",
        "query": "zen temple hall tranquility",
        "title": "El Hospital Sin Medicinas"
    },
    {
        "num": "08",
        "name": "ep08_estudiante_vs_paciente",
        "query": "person breathing mountain sunrise",
        "title": "De Paciente a Estudiante"
    },
    {
        "num": "09",
        "name": "ep09_evidencia_de_sanacion",
        "query": "dna science glowing light",
        "title": "Evidencia de Sanación"
    },
    {
        "num": "10",
        "name": "ep10_peng_qi_guan_ding_fa",
        "query": "raising hands sky sunset",
        "title": "Pěng Qì Guàn Dǐng Fǎ"
    },
    {
        "num": "11",
        "name": "ep11_dun_qiang_gong",
        "query": "spine posture discipline yoga",
        "title": "Dùn Qiáng Gōng (Sentadillas)"
    },
    {
        "num": "12",
        "name": "ep12_el_estado_de_mingjue",
        "query": "lake reflection morning stillness",
        "title": "El Estado de Míngjué"
    },
    {
        "num": "13",
        "name": "ep13_los_8_versos_del_campo",
        "query": "standing top mountain horizon",
        "title": "Los 8 Versos del Campo de Qì"
    },
    {
        "num": "14",
        "name": "ep14_salud_longevidad",
        "query": "healthy elderly vitality smile",
        "title": "Cultivo de Salud y Longevidad"
    },
    {
        "num": "15",
        "name": "ep15_practica_autonoma_comunidad",
        "query": "community park morning sunrise",
        "title": "Práctica Autónoma y Comunidad"
    }
]

import ssl

ssl_context = ssl._create_unverified_context()

def download_pexels_image(url, target_path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, context=ssl_context) as resp, open(target_path, "wb") as f:
        f.write(resp.read())

def fetch_images_for_episodes():
    print(f"Abasteciendo banco de imagenes en: {BANCO_DIR}\n")
    downloaded_count = 0

    for ep in EPISODES_TOPICS:
        q = urllib.parse.quote(ep["query"])
        url = f"https://api.pexels.com/v1/search?query={q}&per_page=2&orientation=portrait"
        req = urllib.request.Request(url, headers={
            "Authorization": PEXELS_KEY,
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

        try:
            with urllib.request.urlopen(req, context=ssl_context) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                photos = data.get("photos", [])
                for idx, photo in enumerate(photos, 1):
                    img_url = photo.get("src", {}).get("portrait") or photo.get("src", {}).get("large")
                    if img_url:
                        filename = f"{ep['name']}_res{idx}.jpg"
                        target = BANCO_DIR / filename
                        download_pexels_image(img_url, str(target))
                        print(f"[{ep['num']}/15] Guardada: {filename} ({ep['title']})")
                        downloaded_count += 1
        except Exception as e:
            print(f"Error descargando para {ep['title']}: {e}")

    print(f"\n¡Completado! Se descargaron {downloaded_count} imagenes nuevas en el banco.")

if __name__ == "__main__":
    fetch_images_for_episodes()
