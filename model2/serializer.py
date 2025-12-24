# model2/serializer.py
import os, json, csv

def save_json(name, data, folder="outputs"):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return path

def save_text(name, text, folder="outputs"):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path

def append_escalation(row_summary, path="escalate.csv"):
    file_exists = os.path.exists(path)
    with open(path, "a", newline='', encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["filename","row_index","reason"])
        writer.writerow([row_summary.get("filename",""), row_summary.get("row_index",""), row_summary.get("reason","")])
    return path
def save_prompt(name, text, folder="outputs"):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path
