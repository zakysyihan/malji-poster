import os
import glob
from generate_poster import generate_poster


def run_batch_tests():
    test_dir = "test"
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)

    test_files = glob.glob(os.path.join(test_dir, "*.txt"))

    print(f"Starting batch generation for {len(test_files)} files...")

    for input_file in sorted(test_files):
        filename = os.path.basename(input_file)
        output_name = filename.replace(".txt", ".png")
        output_path = os.path.join(output_dir, output_name)

        print(f"--- Processing: {filename} ---")
        try:
            generate_poster(input_file, output_path)
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")

    print("Batch generation complete! Check 'test_output/' folder.")


if __name__ == "__main__":
    run_batch_tests()
