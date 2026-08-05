import argparse
import os
import torch
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

def main():
    parser = argparse.ArgumentParser(description="Run TrOCR-Sinhala-finetuned using Hugging Face Transformers.")
    default_image = os.path.abspath(os.path.join(os.path.dirname(__file__), "../OCR/test_images/image.png"))
    parser.add_argument(
        "image_path",
        nargs="?",
        default=default_image,
        help=f"Path to the document/line image to OCR (default: {default_image})"
    )
    args = parser.parse_args()

    if not os.path.exists(args.image_path):
        print(f"Error: Image file not found at '{args.image_path}'. Please specify a valid path.")
        return

    model_id = "eshangj/TrOCR-Sinhala-finetuned"
    device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"Loading TrOCR processor and model '{model_id}' onto {device}...")
    processor = TrOCRProcessor.from_pretrained(model_id)
    model = VisionEncoderDecoderModel.from_pretrained(model_id).to(device)

    print(f"Loading image from '{args.image_path}'...")
    image = Image.open(args.image_path).convert("RGB")

    # Prepare image for TrOCR (resizes and normalizes to 384x384 by default)
    pixel_values = processor(images=image, return_tensors="pt").pixel_values.to(device)

    print("Running TrOCR inference...")
    with torch.no_grad():
        generated_ids = model.generate(pixel_values, max_new_tokens=256)

    output_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    print("\n--- TrOCR Result ---")
    print(output_text)

if __name__ == "__main__":
    main()
