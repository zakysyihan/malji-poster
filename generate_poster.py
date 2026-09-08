import os
import sys

from PIL import Image, ImageDraw, ImageFont

POSTER_W = 1587
POSTER_H = 2245

FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts", "Outfit-Variable.ttf")

TABLE_TOP = 485
HEADER_BG_TOP = 488
HEADER_BG_BOTTOM = 560
HEADER_CENTER_Y = (HEADER_BG_TOP + HEADER_BG_BOTTOM) // 2
BODY_TOP = 564
TABLE_BOTTOM = 1890

COL_LEFT = [23, 100, 301, 671, 1104, 1444]
COL_RIGHT = [96, 297, 667, 1100, 1439, 1563]
HEADERS = ["NO", "WAKTU", "TEMA", "PEMATERI", "TEMPAT", "KET"]

HDR_BG = (26, 58, 107)
HDR_BORDER = (15, 38, 71)
HDR_TEXT = (255, 255, 255)
ROW_BORDER = (184, 204, 228)
ZEBRA_BG = (230, 238, 248)
WHITE_BG = (255, 255, 255)
TEXT_DARK = (26, 26, 46)
LIBUR_RED = (211, 47, 47)

LINE_STEP = 33
VPAD = 30
BORDER = 3

_font_cache = {}


def get_font(size, weight):
    key = (size, weight)
    if key not in _font_cache:
        font = ImageFont.truetype(FONT_PATH, size)
        font.set_variation_by_axes([weight])
        _font_cache[key] = font
    return _font_cache[key]


def select_background(template_type):
    if template_type == "maghrib":
        return "kajian_maghrib_template.png"
    if template_type == "jumat":
        return "sholat_jumat_template.png"
    return "kajian_subuh_ashar_template.png"


def wrap_text(text, font, max_width):
    if not text:
        return []
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        candidate = word if not current else current + " " + word
        if font.getlength(candidate) <= max_width:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = word
        else:
            while font.getlength(word) > max_width and len(word) > 1:
                cut = 1
                while cut < len(word) and font.getlength(word[:cut + 1]) <= max_width:
                    cut += 1
                lines.append(word[:cut])
                word = word[cut:]
            current = word
    if current:
        lines.append(current)
    return lines


def centered_baseline(draw, text, font, cy):
    y0, y1 = draw.textbbox((0, 0), text, font=font, anchor="ls")[1], draw.textbbox((0, 0), text, font=font, anchor="ls")[3]
    return cy - (y1 - y0) / 2 - y0


def draw_centered_text(draw, cx, baseline_y, text, font, fill, tracking=0):
    widths = [font.getlength(ch) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = cx - total / 2
    for ch, w in zip(text, widths):
        draw.text((x, baseline_y), ch, font=font, fill=fill, anchor="ls")
        x += w + tracking


def draw_text_block(draw, cx, cy, text, font, fill, max_width, lines_step):
    if not text:
        return
    lines = wrap_text(text, font, max_width) or [text]
    n = len(lines)
    y0_first = draw.textbbox((0, 0), lines[0], font=font, anchor="ls")[1]
    y1_last = draw.textbbox((0, 0), lines[-1], font=font, anchor="ls")[3]
    height = lines_step * (n - 1) + (y1_last - y0_first)
    baseline = cy - height / 2 - y0_first
    for i, line in enumerate(lines):
        width = font.getlength(line)
        draw.text((cx - width / 2, baseline + i * lines_step), line, font=font, fill=fill, anchor="ls")


def draw_shadowed_date(draw, text, font):
    x, top = 85, 417
    y0 = draw.textbbox((0, 0), text, font=font, anchor="ls")[1]
    baseline = top - y0
    shadow = (60, 30, 0)
    draw.text((x + 2, baseline + 2), text, font=font, fill=shadow, anchor="ls")
    draw.text((x + 1, baseline + 1), text, font=font, fill=shadow, anchor="ls")
    draw.text((x, baseline), text, font=font, fill=(255, 255, 255), anchor="ls")


def compute_row_heights(lines_counts):
    n = len(lines_counts)
    region = TABLE_BOTTOM - BODY_TOP
    avail = region - BORDER * n
    base, rem = divmod(avail, n)
    heights = [base] * n
    for k in range(rem):
        heights[k] += 1
    natural = [lc * LINE_STEP + VPAD for lc in lines_counts]
    for i in range(n):
        if natural[i] > heights[i]:
            heights[i] = natural[i]
    total = sum(heights)
    while total > avail:
        best = max(range(n), key=lambda j: heights[j] - natural[j])
        surplus = heights[best] - natural[best]
        if surplus <= 0:
            break
        reduce_by = min(surplus, total - avail)
        heights[best] -= reduce_by
        total -= reduce_by
    return heights


def render_poster(template_path, date, entries, output_file):
    poster = Image.open(template_path).convert("RGB")
    draw = ImageDraw.Draw(poster)

    date_font = get_font(28, 600)
    draw_shadowed_date(draw, date, date_font)

    n = len(entries)
    col_widths = [r - l + 1 for l, r in zip(COL_LEFT, COL_RIGHT)]

    def cell_lines(i, text):
        if not text:
            return 1
        font = get_font(24, 600)
        return max(1, len(wrap_text(text, font, col_widths[i] - 20)))

    def cell_text(e, c):
        return [str(e["no"]), e["time"], e["theme"], e["speaker"], e["place"], e["note"]][c]

    lines_counts = [max(cell_lines(c, cell_text(e, c)) for c in range(6)) for e in entries]

    # table header band
    draw.rectangle([20, TABLE_TOP, 1566, TABLE_TOP + BORDER - 1], fill=HDR_BORDER)
    draw.rectangle([20, HEADER_BG_TOP, 1566, HEADER_BG_BOTTOM], fill=HDR_BG)
    draw.rectangle([20, HEADER_BG_BOTTOM + 1, 1566, HEADER_BG_BOTTOM + BORDER], fill=HDR_BORDER)
    for l, r in zip(COL_LEFT, COL_RIGHT):
        draw.rectangle([l, HEADER_BG_TOP, r, HEADER_BG_BOTTOM], fill=HDR_BG)
    header_font = get_font(26, 800)
    for c in range(6):
        text = HEADERS[c]
        cx = (COL_LEFT[c] + COL_RIGHT[c]) / 2
        baseline = centered_baseline(draw, text, header_font, HEADER_CENTER_Y)
        draw_centered_text(draw, cx, baseline, text, header_font, HDR_TEXT, tracking=1)

    heights = compute_row_heights(lines_counts)
    y = BODY_TOP
    body_bottom = y
    row_ranges = []
    for h in heights:
        row_ranges.append((y, y + h - 1))
        y += h + BORDER
    body_bottom = y - 1

    body_font = get_font(24, 600)
    for i, (top, bottom) in enumerate(row_ranges):
        bg = WHITE_BG if i % 2 == 0 else ZEBRA_BG
        draw.rectangle([COL_LEFT[0], top, COL_RIGHT[-1], bottom], fill=bg)
        draw.rectangle([20, bottom + 1, 1566, bottom + BORDER], fill=ROW_BORDER)

    # vertical separators
    for sx in (97, 298, 668, 1101, 1440):
        draw.rectangle([sx, HEADER_BG_TOP, sx + BORDER - 1, HEADER_BG_BOTTOM], fill=HDR_BORDER)
        draw.rectangle([sx, BODY_TOP, sx + BORDER - 1, body_bottom], fill=ROW_BORDER)
    # outer vertical borders
    draw.rectangle([20, HEADER_BG_TOP, 22, HEADER_BG_BOTTOM], fill=HDR_BORDER)
    draw.rectangle([1564, HEADER_BG_TOP, 1566, HEADER_BG_BOTTOM], fill=HDR_BORDER)
    draw.rectangle([20, BODY_TOP, 22, body_bottom], fill=ROW_BORDER)
    draw.rectangle([1564, BODY_TOP, 1566, body_bottom], fill=ROW_BORDER)

    bold_font = get_font(24, 900)
    for i, entry in enumerate(entries):
        top, bottom = row_ranges[i]
        cy = (top + bottom) / 2
        cells = [str(entry["no"]), entry["time"], entry["theme"], entry["speaker"], entry["place"], entry["note"]]
        for c in range(6):
            text = cells[c]
            if not text:
                continue
            is_libur = c == 5 and str(text).lower() == "libur"
            font = bold_font if is_libur else body_font
            fill = LIBUR_RED if is_libur else TEXT_DARK
            draw_text_block(draw, (COL_LEFT[c] + COL_RIGHT[c]) / 2, cy, text, font, fill,
                            col_widths[c] - 20, LINE_STEP)

    poster.save(output_file, "PNG")


def generate_poster(input_file, output_file):
    from parser import parse_broadcast

    if not os.path.exists(input_file):
        print(f"Error: '{input_file}' not found.")
        sys.exit(1)

    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()
    data = parse_broadcast(content)

    print(f"Parsed {len(data['entries'])} entries from '{input_file}'")
    print(f"  Title:    {data['title']}")
    print(f"  Subtitle: {data['subtitle']}")
    print(f"  Date:     {data['date']}")

    bg_name = select_background(data["template_type"])
    bg_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", bg_name))
    if not os.path.exists(bg_path):
        print(f"Error: Background template '{bg_path}' not found.")
        return []

    entries = data["entries"]
    total_entries = len(entries)
    if total_entries == 0:
        print("No entries to generate.")
        return []

    chunk_size = 10
    chunks = [entries[i:i + chunk_size] for i in range(0, total_entries, chunk_size)]
    if len(chunks) > 1 and len(chunks[-1]) < 3:
        chunks[-2].extend(chunks.pop())

    generated_files = []
    base_name, ext = os.path.splitext(output_file)

    for idx, chunk in enumerate(chunks):
        if len(chunks) > 1:
            cur_output_file = f"{base_name}_part{idx + 1}{ext}"
        else:
            cur_output_file = output_file
        render_poster(bg_path, data["date"], chunk, cur_output_file)
        print(f"Poster saved: {cur_output_file}")
        generated_files.append(cur_output_file)

    return generated_files


if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "broadcast.txt"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "poster-generated.png"
    generate_poster(input_file, output_file)
