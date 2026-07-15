import asyncio
import os
import sys

from playwright.async_api import async_playwright
from jinja2 import Environment, FileSystemLoader
from parser import parse_broadcast


async def generate_poster(input_file: str, output_file: str) -> list[str]:
    """Parse a broadcast file and render it as a poster PNG."""

    if not os.path.exists(input_file):
        print(f"Error: '{input_file}' not found.")
        sys.exit(1)

    # 1. Parse
    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()
    data = parse_broadcast(content)

    print(f"Parsed {len(data['entries'])} entries from '{input_file}'")
    print(f"  Title:    {data['title']}")
    print(f"  Subtitle: {data['subtitle']}")
    print(f"  Date:     {data['date']}")

    # 2. Select Background Template
    if data['template_type'] == "maghrib":
        bg_name = "kajian_maghrib_template.png"
    elif data['template_type'] == "jumat":
        bg_name = "sholat_jumat_template.png"
    else:
        bg_name = "kajian_subuh_ashar_template.png"
    
    bg_path = os.path.abspath(os.path.join("assets", bg_name))
    if not os.path.exists(bg_path):
        print(f"Error: Background template '{bg_path}' not found.")
        return []
    
    bg_url = f"file://{bg_path}"

    # 3. Chunking & Rendering
    chunk_size = 10
    entries = data['entries']
    total_entries = len(entries)
    
    if total_entries == 0:
        print("No entries to generate.")
        return []
        
    chunks = [entries[i:i + chunk_size] for i in range(0, total_entries, chunk_size)]
    
    # Merge small remainder (< 3 entries) into the previous chunk
    if len(chunks) > 1 and len(chunks[-1]) < 3:
        chunks[-2].extend(chunks.pop())
    generated_files = []
    base_name, ext = os.path.splitext(output_file)
    
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('poster-template.html')

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        
        for idx, chunk in enumerate(chunks):
            if len(chunks) > 1:
                cur_output_file = f"{base_name}_part{idx+1}{ext}"
            else:
                cur_output_file = output_file
                
            rendered_html = template.render(
                title=data['title'],
                subtitle=data['subtitle'],
                date=data['date'],
                entries=chunk,
                background_url=bg_url,
                template_type=data['template_type']
            )

            temp_html = f"_temp_{os.path.basename(input_file).replace('.txt', '')}_part{idx+1}.html"
            with open(temp_html, "w", encoding="utf-8") as f:
                f.write(rendered_html)

            page = await browser.new_page(viewport={'width': 1587, 'height': 2245})
            abs_path = os.path.abspath(temp_html)
            await page.goto(f"file://{abs_path}")
            await page.wait_for_load_state("networkidle")
            await page.wait_for_timeout(1000)

            await page.screenshot(path=cur_output_file, full_page=False)
            print(f"✅ Poster saved: {cur_output_file}")
            generated_files.append(cur_output_file)
            
            if os.path.exists(temp_html):
                os.remove(temp_html)

        await browser.close()

    return generated_files


if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "broadcast.txt"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "poster-generated.png"
    asyncio.run(generate_poster(input_file, output_file))
