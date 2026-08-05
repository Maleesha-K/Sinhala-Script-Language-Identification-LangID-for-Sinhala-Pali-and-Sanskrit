import argparse
import os
from PIL import Image
from surya.ocr import run_ocr
from surya.model.detection.model import load_model as load_det_model, load_processor as load_det_processor
from surya.model.recognition.model import load_model as load_rec_model
from surya.model.recognition.processor import load_processor as load_rec_processor

def main():
    parser = argparse.ArgumentParser(description="Test surya-ocr on Sinhala script images.")
    parser.add_argument("image_path", help="Path to the image containing Sinhala/Pali/Sanskrit in Sinhala script")
    parser.add_argument("--langs", nargs="+", default=["si"], help="Language codes (e.g. si for Sinhala, sa for Sanskrit, pi for Pali)")
    args = parser.parse_args()

    if not os.path.exists(args.image_path):
        print(f"Error: Image not found at {args.image_path}")
        return

    print(f"Loading image from {args.image_path}...")
    image = Image.open(args.image_path)

    print("Loading Surya OCR models (this might take a while on the first run)...")
    det_processor, det_model = load_det_processor(), load_det_model()
    rec_model, rec_processor = load_rec_model(), load_rec_processor()

    print(f"Running OCR for languages: {args.langs}...")
    predictions = run_ocr([image], [args.langs], det_model, det_processor, rec_model, rec_processor)

    print("\n--- OCR Results ---")
    for idx, prediction in enumerate(predictions):
        print(f"\nResults for image {idx + 1}:")
        for line in prediction.text_lines:
            print(f"Text: {line.text}")
            print(f"Confidence: {line.confidence:.4f}")
            print(f"BBox: {line.bbox}")
            print("-" * 20)

if __name__ == "__main__":
    main()
