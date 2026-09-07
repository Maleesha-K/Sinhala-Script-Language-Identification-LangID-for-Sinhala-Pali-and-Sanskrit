import os
import sys
import pandas as pd

def fix_win_path(path):
    abs_path = os.path.abspath(path)
    if sys.platform == "win32" and not abs_path.startswith("\\\\?\\"):
        return "\\\\?\\" + abs_path
    return abs_path

# Auto-resolve project root
if not os.path.exists("Comparison Tables - Final copy.csv") and os.path.exists("../Comparison Tables - Final copy.csv"):
    os.chdir("../")

template_path = fix_win_path("Comparison Tables - Final copy.csv")
out_path = fix_win_path("Comparison Tables - FastText Finetuned.csv")

# Read existing template
with open(template_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for idx, line in enumerate(lines):
    parts = line.strip().split(",")
    # Pad parts to 38 elements if shorter
    while len(parts) < 38:
        parts.append("")
        
    # Check if this is Zero-Shot fastText LID-176 row (Row index 6 in 0-indexed file, line starting with fastText LID-176 before FineTuning Results)
    if idx == 6 and parts[0] == "fastText LID-176":
        # Zero-shot flores_plus (cols 1..11)
        # Model, Sinhala-Sinh, Pali-Sinh, Sanskrit-Sinh, Sanskrit-Deva, English-Latn, Tamil-Taml, Hindi-Deva, Bengali-Beng, Arabic-Arab, French-Latn, German-Latn
        parts[1] = "0.5438"   # Sinhala-Sinh (on hybrid test dataset)
        parts[2] = "0"        # Pali-Sinh
        parts[3] = "0"        # Sanskrit-Sinh
        parts[4] = "0.9594"   # Sanskrit-Deva
        parts[5] = "0.7213"   # English-Latn
        parts[6] = "1"        # Tamil-Taml
        parts[7] = "0.9629"   # Hindi-Deva
        parts[8] = "1"        # Bengali-Beng
        parts[9] = "0.6667"   # Arabic-Arab
        parts[10] = "0.9873"  # French-Latn
        parts[11] = "0.9892"  # German-Latn
        
        # Zero-shot commonlid (cols 13..24)
        parts[13] = "fastText LID-176"
        parts[14] = "0.5438"  # Sinhala-Sinh
        parts[15] = "0"       # Pali-Sinh
        parts[16] = "0"       # Sanskrit-Sinh
        parts[17] = "0.8886"  # Sanskrit-Deva
        parts[18] = "0.9725"  # English-Latn
        parts[19] = "0.9643"  # Tamil-Taml
        parts[20] = "0.9816"  # Hindi-Deva
        parts[21] = "0.9936"  # Bengali-Beng
        parts[22] = "0.9947"  # Arabic-Arab
        parts[23] = "0.9447"  # French-Latn
        parts[24] = "0.9672"  # German-Latn
        
        # Zero-shot wili-2018 (cols 26..37)
        parts[26] = "fastText LID-176"
        parts[27] = "0.5438"  # Sinhala-Sinh
        parts[28] = "0"       # Pali-Sinh
        parts[29] = "0"       # Sanskrit-Sinh
        parts[30] = "0.9904"  # Sanskrit-Deva
        parts[31] = "0.9434"  # English-Latn
        parts[32] = "0.995"   # Tamil-Taml
        parts[33] = "0.9904"  # Hindi-Deva
        parts[34] = "0.9529"  # Bengali-Beng
        parts[35] = ""        # Arabic-Arab
        parts[36] = "0.9779"  # French-Latn
        parts[37] = "0.9850"  # German-Latn

    # Check if this is FineTuning fastText LID-176 row (Row index 19 in 0-indexed file)
    elif idx == 19 and parts[0] == "fastText LID-176":
        # Fine-tuned flores_plus (cols 1..11)
        parts[1] = "0.6047"   # Sinhala-Sinh
        parts[2] = "0.6268"   # Pali-Sinh
        parts[3] = "0.6331"   # Sanskrit-Sinh
        parts[4] = ""         # Sanskrit-Deva
        parts[5] = ""         # English-Latn
        parts[6] = ""         # Tamil-Taml
        parts[7] = ""         # Hindi-Deva
        parts[8] = ""         # Bengali-Beng
        parts[9] = ""         # Arabic-Arab
        parts[10] = ""        # French-Latn
        parts[11] = ""        # German-Latn
        
        # Fine-tuned commonlid (cols 13..24)
        parts[13] = "fastText LID-176"
        parts[14] = "0.0851"  # Sinhala-Sinh
        parts[15] = "0.4258"  # Pali-Sinh
        parts[16] = "0.3521"  # Sanskrit-Sinh
        parts[17] = ""        # Sanskrit-Deva
        parts[18] = ""        # English-Latn
        parts[19] = ""        # Tamil-Taml
        parts[20] = ""        # Hindi-Deva
        parts[21] = ""        # Bengali-Beng
        parts[22] = ""        # Arabic-Arab
        parts[23] = ""        # French-Latn
        parts[24] = ""        # German-Latn
        
        # Fine-tuned wili-2018 (cols 26..37)
        parts[26] = "fastText LID-176"
        parts[27] = "0.7559"  # Sinhala-Sinh
        parts[28] = "0.6625"  # Pali-Sinh
        parts[29] = "0.6071"  # Sanskrit-Sinh
        parts[30] = ""        # Sanskrit-Deva
        parts[31] = ""        # English-Latn
        parts[32] = ""        # Tamil-Taml
        parts[33] = ""        # Hindi-Deva
        parts[34] = ""        # Bengali-Beng
        parts[35] = ""        # Arabic-Arab
        parts[36] = ""        # French-Latn
        parts[37] = ""        # German-Latn
        
    new_lines.append(",".join(parts) + "\n")

with open(out_path, "w", encoding="utf-8") as f:
    f.writelines(new_lines)

print(f"Successfully generated populated comparison table CSV at: {out_path}")
