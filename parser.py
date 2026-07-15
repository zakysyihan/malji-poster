import re
import json
import sys


def _time_sort_key(time_str):
    """Convert a time string to a sortable integer (minutes since midnight)."""
    time_str = time_str.lower().strip()

    # Prayer-based times (ordered by typical daily occurrence)
    prayer_order = {
        "subuh": 5 * 60, "dhuha": 8 * 60, "dzuhur": 12 * 60,
        "ashar": 15 * 60 + 30, "maghrib": 18 * 60, "isya": 19 * 60,
    }
    for prayer, minutes in prayer_order.items():
        if f"da {prayer}" in time_str.replace("'", ""):
            return minutes

    # Numeric time: "06.00", "09.00 - 10.00", "11.35 WIB"
    m = re.search(r'(\d{1,2})[.:](\d{2})', time_str)
    if m:
        return int(m.group(1)) * 60 + int(m.group(2))

    return 9999  # unknown times go last


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
    
    # Detect session type — only from the title line
    if "jum'at" in title_lower or "jumat" in title_lower or "khutbah" in title_lower:
        template_type = "jumat"
        subtitle = "Khatib Jum'at"
    elif "subuh" in title_lower or "dhuha" in title_lower or "ashar" in title_lower:
        template_type = "subuh_ashar"
        subtitle = "Ba'da Subuh, Dhuha, Ashar Malang Raya"
    elif "maghrib" in title_lower:
        template_type = "maghrib"
        subtitle = "Ba'da Maghrib wilayah Malang Raya"
    else:
        # Fallback based on emoji in the first line only
        first_line = lines[0] if lines else ""
        if "☀️" in first_line:
            template_type = "subuh_ashar"
            subtitle = "Wilayah Malang Raya"
        else:
            template_type = "maghrib"
            subtitle = "Wilayah Malang Raya"

    # --- Extract date ---
    date_info = ""
    hijri_info = ""
    for i, line in enumerate(lines):
        if re.search(r'Pekan', line, re.IGNORECASE):
            date_info = line.strip('*').strip('_').strip()
            date_info = re.sub(r'[*_]', '', date_info).strip()
            # Look for Hijriyah line within next 3 lines
            for j in range(i + 1, min(i + 4, len(lines))):
                if re.search(r'Hijriyah|hijriyah|Hijri', lines[j], re.IGNORECASE):
                    hijri_info = re.sub(r'[*_]', '', lines[j]).strip()
                    hijri_info = re.sub(r'^Hijriyah\s*:\s*', '', hijri_info, flags=re.IGNORECASE).strip()
                    break
            break
    
    if date_info and hijri_info:
        date_info = f"{date_info} / {hijri_info}"
            
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
            note_m = re.search(r'(?:🚻|❌)\s*(.*)', raw_entry)

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

    # Sort entries by time and re-number
    parsed_entries.sort(key=lambda e: _time_sort_key(e["time"]))
    for i, entry in enumerate(parsed_entries):
        entry["no"] = i + 1

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
