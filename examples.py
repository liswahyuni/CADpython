#!/usr/bin/env python3

from main import TextToCAD


def run_examples():
    converter = TextToCAD()
    
    examples = [
        {
            "description": "Kursi makan dengan 4 kaki, dudukan 45x45 cm, tinggi 95 cm",
            "filename": "kursi_makan"
        },
        {
            "description": "Meja kerja ukuran 140x70 cm, tinggi 75 cm",
            "filename": "meja_kerja"
        },
        {
            "description": "Ruangan ukuran 4x5 meter, tinggi 3 meter, dengan 1 pintu di sisi barat dan 1 jendela di sisi utara",
            "filename": "kamar_tidur"
        }
    ]
    
    for example in examples:
        print(f"\nProcessing: {example['description']}")
        print("-" * 50)
        
        converter.process_description(
            example["description"],
            output_dir="examples_output",
            generate_3d=True,
            filename_prefix=example["filename"]
        )


if __name__ == "__main__":
    run_examples()