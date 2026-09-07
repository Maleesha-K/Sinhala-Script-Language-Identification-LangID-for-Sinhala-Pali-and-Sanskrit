import csv
import os

# Define the columns
headers = [
    "Model", "Dataset", "Evaluation Metric", "Zero-shot",
    "Sinhala-Sinh", "Pali-Sinh", "Sanskrit-Sinh", "Sanskrit-Deva",
    "English-Latn", "Tamil-Taml", "Hindi-Deva", "Bengali-Beng",
    "Arabic-Arab", "French-Latn", "German-Latn"
]

# Raw data extracted from images
# Format: (Model, Dataset, si, pi, sa, en, ta, hi, bn, ar, fr, de)
data_points = [
    ("XLM-R Base", "flores_plus", 0.0000, 0.0000, 0.0000, 0.9985, 0.0000, 0.1835, 0.0000, 0.6671, 0.9990, 1.0000),
    ("XLM-R Base", "commonlid", 0.0000, 0.0000, 0.0000, 0.9473, 0.0000, 0.4403, 0.0000, 0.9955, 0.9483, 0.9677),
    ("XLM-R Base", "wili-2018", 0.0000, 0.0000, 0.0000, 0.9527, 0.0000, 0.1811, 0.0000, 0.0000, 0.9900, 0.9899),
    
    ("ConLID", "flores_plus", 0.7916, "", 0.6027, 0.9960, 0.9995, 0.9970, 0.9995, 0.3733, 1.0000, 0.9970),
    ("ConLID", "commonlid", 0.7916, "", 0.5468, 0.8500, 0.9818, 0.9443, 0.9615, 0.7664, 0.8974, 0.8953),
    ("ConLID", "wili-2018", 0.7916, "", 0.5948, 0.9439, 0.9945, 0.9899, 0.9435, 0.0000, 0.9819, 0.9707),
    
    ("fastText LID-176", "flores_plus", 0.7912, "", 0.5703, 0.7213, 1.0000, 0.9629, 1.0000, 0.6667, 0.9873, 0.9897),
    ("fastText LID-176", "commonlid", 0.7910, "", 0.4904, 0.9724, 0.9643, 0.9702, 0.9936, 0.9947, 0.9447, 0.9673),
    ("fastText LID-176", "wili-2018", 0.7912, "", 0.5931, 0.9385, 0.9950, 0.9889, 0.9529, 0.0000, 0.9774, 0.9854),
    
    ("GlotLID v3", "flores_plus", 0.7914, "", 0.5998, 1.0000, 1.0000, 0.9926, 0.9995, 0.6054, 1.0000, 1.0000),
    ("GlotLID v3", "commonlid", 0.7914, "", 0.5476, 0.9255, 0.9878, 0.9713, 0.9792, 0.9631, 0.9255, 0.9215),
    ("GlotLID v3", "wili-2018", 0.7914, "", 0.5940, 0.9377, 0.9950, 0.9173, 0.9451, 0.0000, 0.9880, 0.9754),
    
    ("NLLB LID-218", "flores_plus", 0.7912, "", 0.5952, 0.9840, 1.0000, 0.9912, 1.0000, 0.6664, 0.9995, 1.0000),
    ("NLLB LID-218", "commonlid", 0.7912, "", 0.5210, 0.9240, 0.9747, 0.9640, 0.9863, 0.9923, 0.9289, 0.9410),
    ("NLLB LID-218", "wili-2018", 0.7912, "", 0.5935, 0.9301, 0.9940, 0.9889, 0.9429, 0.0000, 0.9900, 0.9904),
    
    ("OpenLID-v2", "flores_plus", 0.7912, "", 0.0153, 0.9995, 1.0000, 0.0361, 0.9970, 0.5579, 0.9975, 1.0000),
    ("OpenLID-v2", "commonlid", 0.7912, "", 0.0495, 0.8973, 0.9877, 0.1749, 0.9722, 0.9473, 0.9052, 0.9239),
    ("OpenLID-v2", "wili-2018", 0.7912, "", 0.0120, 0.9427, 0.9940, 0.0134, 0.9424, 0.0000, 0.9687, 0.9817),
]

def create_row(dp):
    model, dataset, si, pi, sa, en, ta, hi, bn, ar, fr, de = dp
    return [
        model, dataset, "Per-language F1", "Yes",
        si, pi, "", sa,  # Sanskrit-Sinh is empty, sa goes to Sanskrit-Deva
        en, ta, hi, bn, ar, fr, de
    ]

# Create directories and write files
datasets = {
    "flores_plus": "Flores",
    "commonlid": "commonlid",
    "wili-2018": "wili"
}

for ds_key, folder_name in datasets.items():
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    filename = os.path.join(folder_name, "results.csv")
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for dp in data_points:
            if dp[1] == ds_key:
                writer.writerow(create_row(dp))

print("Created folders and CSV files.")
