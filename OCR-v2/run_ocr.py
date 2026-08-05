import argparse
import os
import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForImageTextToText

def main():
    parser = argparse.ArgumentParser(description="Run Surya OCR 2 using Hugging Face Transformers.")
    default_image = os.path.abspath(os.path.join(os.path.dirname(__file__), "../OCR/test_images/image.png"))
    parser.add_argument(
        "image_path",
        nargs="?",
        default=default_image,
        help=f"Path to the document image to OCR (default: {default_image})"
    )
    args = parser.parse_args()

    if not os.path.exists(args.image_path):
        print(f"Error: Image file not found at '{args.image_path}'. Please specify a valid path.")
        return

    model_id = "datalab-to/surya-ocr-2"

    print(f"Loading processor and model '{model_id}' in bfloat16...")
    processor = AutoProcessor.from_pretrained(model_id)
    model = AutoModelForImageTextToText.from_pretrained(
        model_id,
        dtype=torch.bfloat16,
        device_map="cuda"
    )

    print(f"Loading image from '{args.image_path}'...")
    image = Image.open(args.image_path).convert("RGB")

    # Format the prompt for Surya OCR
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": "Read the text in this image."}
            ]
        }
    ]

    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(text=[text], images=[image], padding=True, return_tensors="pt").to("cuda")

    print("Running OCR inference...")
    with torch.no_grad():
        generated_ids = model.generate(**inputs, max_new_tokens=1024)

    # Trim the prompt tokens out of the generated output
    generated_ids_trimmed = [
        out_ids[len(in_ids):] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
    ]

    output_text = processor.batch_decode(
        generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )

    print("\n--- OCR Result ---")
    print(output_text[0])

if __name__ == "__main__":
    main()
