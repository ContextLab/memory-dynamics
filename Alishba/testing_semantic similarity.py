import os
import csv
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer, util
from tqdm import tqdm

# === CONFIG ===
model_name = "all-mpnet-base-v2"
model = SentenceTransformer(model_name)

# Files
scene_file = r"d:\memory-dynamics-master\memory-dynamics-master\data\annotations\Atlanta_Ep1_Event_Tags_by_Scene.txt"

participant_files = [
    #r"C:\Users\Alishba\Downloads\prediction files\Transcriptions\Tested Participant Files_MD-020119-A-03\debugRQQWb_debugwDi2H\debugRQQWb_debugwDi2H-prediction.txt",
    #r"C:\Users\Alishba\Downloads\prediction files\Transcriptions\Tested Participant Files_MD-020119-A-03\debugRQQWb_debugwDi2H\debugRQQWb_debugwDi2H-recall.txt",
    r"C:\Users\Alishba\Downloads\prediction files\Transcriptions\Tested Participant Files_MD-020119-A-03\debugWRfIG_debugJWnAi\debugWRfIG_debugJWnAi-delayed.txt"
]

# === FUNCTIONS ===

def read_lines(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def compute_all_similarities(part_lines, scene_lines):
    print(" Embedding texts...")
    part_embs = model.encode(part_lines, convert_to_tensor=True, show_progress_bar=True)
    scene_embs = model.encode(scene_lines, convert_to_tensor=True, show_progress_bar=True)
    print(" Computing cosine similarities...")
    return util.cos_sim(part_embs, scene_embs)

def save_matrix_to_csv(part_lines, scene_lines, sim_matrix, output_csv_path):
    with open(output_csv_path, "w", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Participant Sentence", "Episode Scene", "Similarity Score"])
        for i, part_line in enumerate(part_lines):
            for j, scene_line in enumerate(scene_lines):
                score = float(sim_matrix[i][j])
                writer.writerow([part_line, scene_line, round(score, 4)])

# === MAIN ===

def main():
    print(" Loading episode scenes...")
    scene_lines = read_lines(scene_file)
    print(f" Loaded {len(scene_lines)} scene lines.")

    for file_path in participant_files:
        print(f"\n Processing file: {Path(file_path).name}")
        if not Path(file_path).exists():
            print(f" File not found: {file_path}")
            continue

        part_lines = read_lines(file_path)
        print(f" Loaded {len(part_lines)} participant lines.")

        sim_matrix = compute_all_similarities(part_lines, scene_lines)

        output_csv = Path(file_path).with_name(f"{Path(file_path).stem}_FULL_matrix.csv")
        save_matrix_to_csv(part_lines, scene_lines, sim_matrix, output_csv)

        print(f" Saved full similarity matrix to: {output_csv}")

if __name__ == "__main__":
    main()
