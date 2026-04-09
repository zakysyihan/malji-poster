import re
import json
import sys


def parse_broadcast(content):
    """Parse a Malang Mengaji broadcast message into structured data."""
    content = content.replace('\r\n', '\n')

    lines = [line.strip() for line in content.split('\n') if line.strip()]

    # --- Extract title ---
    title = ""
    for line in lines:
        # Match the first line with the main emoji header
        cleaned = re.sub(r'[^\w\s\',.]', '', line).strip()
        if cleaned and len(cleaned) > 10:
            title = cleaned
            # Remove leading/trailing formatting artifacts
            title = title.strip('*').strip('_').strip()
            break

    # --- Extract template type & subtitle ---
    template_type = "maghrib"
    subtitle = "Ba'da Maghrib wilayah Malang Raya"
    
    title_lower = title.lower()
    content_lower = content.lower()
    
    # Detect session type
    if "jum'at" in title_lower or "jumat" in title_lower or "khutbah" in title_lower:
        template_type = "jumat"
        subtitle = "Khatib Jum'at"
    elif "subuh" in title_lower or "dhuha" in title_lower or "ashar" in title_lower or \
       "subuh" in content_lower or "dhuha" in content_lower or "ashar" in content_lower:
        template_type = "subuh_ashar"
        subtitle = "Ba'da Subuh, Dhuha, Ashar Malang Raya"
    elif "maghrib" in title_lower or "maghrib" in content_lower:
        template_type = "maghrib"
        subtitle = "Ba'da Maghrib wilayah Malang Raya"
    else:
        # Fallback based on emoji
        if "☀️" in content:
            template_type = "subuh_ashar"
            subtitle = "Wilayah Malang Raya"
        else:
            template_type = "maghrib"
            subtitle = "Wilayah Malang Raya"

    # --- Extract date ---
    date_info = ""
    for line in lines:
        # Look for "Pekan" pattern
        if re.search(r'Pekan', line, re.IGNORECASE):
            date_info = line.strip('*').strip('_').strip()
            # Clean up any Markdown bold/italic markers
            date_info = re.sub(r'[*_]', '', date_info).strip()
            break
            
    if not date_info:
        try:
            from datetime import datetime, timedelta
            try:
                from zoneinfo import ZoneInfo
                tz = ZoneInfo('Asia/Jakarta')
            except ImportError:
                import pytz
                tz = pytz.timezone('Asia/Jakarta')
                
            now = datetime.now(tz)
            
            # Smart determination of date based on type
            if template_type == "jumat":
                days_ahead = (4 - now.weekday()) % 7
                target_date = now + timedelta(days=days_ahead)
            else:
                target_date = now
                
            week_of_month = (target_date.day - 1) // 7 + 1
            
            days_id = {"Monday": "Senin", "Tuesday": "Selasa", "Wednesday": "Rabu", "Thursday": "Kamis", "Friday": "Jum'at", "Saturday": "Sabtu", "Sunday": "Ahad"}
            months_id = ["", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
            
            day_name = days_id[target_date.strftime("%A")]
            month_name = months_id[target_date.month]
            
            from hijri_converter import Gregorian
            hijri = Gregorian(target_date.year, target_date.month, target_date.day).to_hijri()
            hijri_months = ["", "Muharram", "Safar", "Rabi'ul Awal", "Rabi'ul Akhir", "Jumadil Awal", "Jumadil Akhir", "Rajab", "Sya'ban", "Ramadhan", "Syawwal", "Dzulqa'dah", "Dzulhijjah"]
            
            date_info = f"Pekan ke-{week_of_month} : {day_name}, {target_date.day} {month_name} {target_date.year} / {hijri.day} {hijri_months[hijri.month]} {hijri.year} H"
        except Exception:
            pass

    # --- Parse entries ---
    if template_type == "jumat":
        # Parse numbered list
        sections = re.split(r'_{5,}', content)
        entries_section = sections[-1] if len(sections) > 1 else content
        entries_section = re.split(r'••════••|_Barakallahufiikum_', entries_section)[0]
        
        # Split by "1. ", "2. ", etc
        raw_entries = re.split(r'\n(?=\d+\.\s)', entries_section)
        parsed_entries = []
        for raw_entry in raw_entries:
            entry_lines = [l.strip() for l in raw_entry.split('\n') if l.strip()]
            if not entry_lines or not re.match(r'^\d+\.\s', entry_lines[0]):
                continue
            
            speaker = re.sub(r'^\d+\.\s*', '', entry_lines[0]).strip()
            place = entry_lines[1] if len(entry_lines) > 1 else ""
            tema = entry_lines[2] if len(entry_lines) > 2 else "Tematik"
            
            # clean tema if starts with Tema:
            tema = re.sub(r'^Tema\s*:\s*', '', tema, flags=re.IGNORECASE).strip('*"\' ')
            
            parsed_entries.append({
                "no": len(parsed_entries) + 1,
                "theme": tema,
                "speaker": speaker,
                "place": place,
                "time": "11.35 WIB",
                "note": "Ikhwan"
            })
    else:
        # Get the section between the separator lines and the footer
        sections = re.split(r'_{5,}', content)
        entries_section = sections[-1] if len(sections) > 1 else content

        # Remove the footer (social media, donation info)
        entries_section = re.split(r'••════••', entries_section)[0]

        # Split by any of the standard open book emojis
        raw_entries = re.split(r'\n(?=(?:📔|📒|📕|📖))', entries_section)

        parsed_entries = []

        for raw_entry in raw_entries:
            if not raw_entry.strip() or not re.search(r'(?:📔|📒|📕|📖)', raw_entry):
                continue

            theme_m = re.search(r'(?:📔|📒|📕|📖)\s*(.*)', raw_entry)
            speaker_m = re.search(r'👤\s*(.*)', raw_entry)
            place_m = re.search(r'📍\s*(.*)', raw_entry)
            time_m = re.search(r'⏰\s*(.*)', raw_entry)
            note_m = re.search(r'🚻\s*(.*)', raw_entry)

            if not (theme_m and speaker_m and place_m):
                continue

            # Extract just the mosque/building name from the full address
            raw_place = place_m.group(1).strip()
            # Take text before the first comma (usually the name)
            place_name = raw_place.split(',')[0].strip()
            # If the name still has "Jl." in it, it was part of the address — keep the whole first segment
            if place_name.startswith('Jl.') or place_name.startswith('Jalan'):
                place_name = raw_place  # fallback to full

            parsed_entries.append({
                "no": len(parsed_entries) + 1,
                "theme": theme_m.group(1).strip(),
                "speaker": speaker_m.group(1).strip(),
                "place": place_name,
                "time": time_m.group(1).strip() if time_m else "Ba'da Maghrib - selesai",
                "note": note_m.group(1).strip() if note_m else "Umum",
            })

    return {
        "title": title,
        "subtitle": subtitle,
        "template_type": template_type,
        "date": date_info,
        "entries": parsed_entries,
    }


if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "broadcast.txt"
    try:
        with open(input_file, "r") as f:
            content = f.read()
        result = parse_broadcast(content)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
