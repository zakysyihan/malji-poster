import os
import asyncio
from generate_poster import generate_poster
import glob

async def run_batch_tests():
    test_dir = "test"
    output_dir = "test_output"
    os.makedirs(output_dir, exist_ok=True)
    
    test_files = glob.glob(os.path.join(test_dir, "*.txt"))
    # The user mentioned text_4.txt (typo), glob will find both test_*.txt and text_*.txt if they end in .txt
    # Wait, let me be safe and just find all .txt files
    
    print(f"🚀 Starting batch generation for {len(test_files)} files...")
    
    for input_file in sorted(test_files):
        filename = os.path.basename(input_file)
        output_name = filename.replace(".txt", ".png")
        output_path = os.path.join(output_dir, output_name)
        
        print(f"--- Processing: {filename} ---")
        try:
            await generate_poster(input_file, output_path)
        except Exception as e:
            print(f"❌ Error processing {filename}: {str(e)}")
            
    print("\n✅ Batch generation complete! Check 'test_output/' folder.")

if __name__ == "__main__":
    asyncio.run(run_batch_tests())
