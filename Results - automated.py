import os
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from datetime import datetime
from collections import defaultdict

print("STARTING RESULTS SCRIPT")

# --- Streamlit/GitHub Environment Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Configuration Constants ---
LOGOS_FOLDER = os.path.join(BASE_DIR, "Logos")
SAVE_FOLDER = os.path.join(BASE_DIR, "Graphics")
TEMPLATES_FOLDER = os.path.join(BASE_DIR, "Templates")
TEMPLATE_PATH = os.path.join(TEMPLATES_FOLDER, "results_template.png")
FONT_PATH = os.path.join(BASE_DIR, "BebasNeue Regular.ttf")

# Image & Layout
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1350
CONTENT_START_Y = 251.97
SAFE_CONTENT_HEIGHT_LIMIT = 950  # Conservative limit
LEFT_PADDING = 5
TEAM_BOX_WIDTH = 330
SCORE_BOX_WIDTH = 120
LOGO_WIDTH = 140
LOGO_HEIGHT = 120
BOX_HEIGHT = 120
LINE_SPACING = 15
FIXTURE_SPACING = 15
DATE_CIRCLE_SIZE = 142
DATE_CIRCLE_X = 1080 - 138 - 142
DATE_CIRCLE_Y = 95
DATE_CIRCLE_STROKE = 3
HIGH_RES_SCALE = 2
DATE_TEXT_MAX_WIDTH = DATE_CIRCLE_SIZE - 20
DATE_TEXT_MAX_HEIGHT = DATE_CIRCLE_SIZE - 20

# Font Sizes
FONT_SIZE_NORMAL = 65
FONT_SIZE_SCORE = 55
FONT_SIZE_HEADING = 64
FONT_SIZE_CUP_NAME = 39
FONT_SIZE_SMALL_TEAM_NAME = 50
FONT_SIZE_DATE = 40
FONT_SIZE_DATE_MIN = 30
FONT_SIZE_PENALTY_SCORE = 32
FONT_SIZE_PENALTIES_LABEL = 28
VISUAL_Y_OFFSET_CORRECTION = -5

# Special Mappings
SPECIAL_LOGO_MAPPING = {
    "afc aldermaston a": "AFC Aldermaston.png",
    "afc aldermaston b": "AFC Aldermaston.png",
    "eversley & california sunday": "Eversley & California.png",
}
TEAMS_FOR_SMALLER_FONT = ["AFC Aldermaston A", "AFC Aldermaston B"]

# --- Pre-calculate spacing ---
HEADING_SPACE = 100
CUP_NAME_SPACE = 70
if os.path.exists(FONT_PATH):
    try:
        HEADING_FONT_TEMP = ImageFont.truetype(FONT_PATH, FONT_SIZE_HEADING)
        CUP_NAME_FONT_TEMP = ImageFont.truetype(FONT_PATH, FONT_SIZE_CUP_NAME)
        heading_bbox = HEADING_FONT_TEMP.getbbox("Cup")
        cup_name_bbox = CUP_NAME_FONT_TEMP.getbbox("Example Cup Name")
        HEADING_SPACE = 20 + (heading_bbox[3] - heading_bbox[1]) + 20
        CUP_NAME_SPACE = 5 + (cup_name_bbox[3] - cup_name_bbox[1]) + 10
    except Exception as e:
        print(f"Font pre-calc failed: {e}")
else:
    print(f"Font not found at {FONT_PATH}. Using defaults.")

# --- NEW: Enforce League Division Order ---
LEAGUE_DIVISION_ORDER = ["Division 1", "Division 2", "Division 3", "Division 4"]
print("Configuration constants loaded.")


# --- Helper Functions ---
def get_logo(team_name: str, logos_folder: str) -> Image.Image:
    team_name_lower = team_name.strip().lower()
    team_name_clean = team_name.strip()

    # Special mapping
    for key, filename in SPECIAL_LOGO_MAPPING.items():
        if key in team_name_lower:
            for subfolder in ['Current Teams', 'Old Teams']:
                path = os.path.join(logos_folder, subfolder, filename)
                if os.path.exists(path):
                    try:
                        return Image.open(path).convert("RGBA").resize((LOGO_WIDTH, LOGO_HEIGHT), Image.Resampling.LANCZOS)
                    except Exception as e:
                        print(f"Error loading mapped logo: {e}")
                        break

    # Search by name variants
    search_variants = [team_name_lower.replace(" ", "")]
    if "utd" in team_name_lower: search_variants.append(team_name_lower.replace("utd", "united").replace(" ", ""))
    if "united" in team_name_lower: search_variants.append(team_name_lower.replace("united", "utd").replace(" ", ""))
    if "&" in team_name_lower: search_variants.append(team_name_lower.replace("&", "and").replace(" ", ""))
    if "and" in team_name_lower: search_variants.append(team_name_lower.replace("and", "&").replace(" ", ""))
    search_variants = list(set(search_variants))

    for subfolder in ['Current Teams', 'Old Teams']:
        folder = os.path.join(logos_folder, subfolder)
        if not os.path.isdir(folder): continue
        for f in os.listdir(folder):
            f_lower = f.lower().replace(" ", "")
            if any(v in f_lower for v in search_variants) and f_lower.endswith(('.png', '.jpg', '.jpeg')):
                try:
                    return Image.open(os.path.join(folder, f)).convert("RGBA").resize((LOGO_WIDTH, LOGO_HEIGHT), Image.Resampling.LANCZOS)
                except Exception as e:
                    print(f"Error loading logo: {e}")

    # Generic fallback
    generic_path = os.path.join(logos_folder, 'genericlogo.png')
    try:
        return Image.open(generic_path).convert("RGBA").resize((LOGO_WIDTH, LOGO_HEIGHT), Image.Resampling.LANCZOS)
    except Exception as e:
        print(f"Generic logo failed: {e}. Using gray placeholder.")
        return Image.new("RGBA", (LOGO_WIDTH, LOGO_HEIGHT), (200, 200, 200, 255))


def parse_matches_from_file(file_path: str, division: str) -> list[tuple]:
    matches = []
    try:
        df = pd.read_excel(file_path, sheet_name=division)
        print(f"Loaded {len(df)} rows from {division} tab.")
        for _, row in df.iterrows():
            team_1_name = str(row['Team 1 name']).strip() if pd.notna(row['Team 1 name']) else ""
            team_1_score = str(row['Team 1 score']) if pd.notna(row['Team 1 score']) else "-"
            team_2_score = str(row['Team 2 score']) if pd.notna(row['Team 2 score']) else "-"
            team_2_name = str(row['Team 2 name']).strip() if pd.notna(row['Team 2 name']) else ""
            cup_name = str(row['Cup name']).strip() if division.lower() == "cup" and 'Cup name' in row and pd.notna(row['Cup name']) else None
            penalty_score = None
            if division.lower() == "cup" and 'Penalty score' in row and pd.notna(row['Penalty score']):
                penalty_score = str(row['Penalty score']).strip()
                if not ("-" in penalty_score and len(penalty_score.split("-")) == 2):
                    print(f"Warning: Invalid penalty score '{penalty_score}' for {team_1_name} vs {team_2_name}")
                    penalty_score = None
            if team_1_name and team_2_name:
                matches.append((team_1_name, team_1_score, team_2_score, team_2_name, cup_name, penalty_score))
    except Exception as e:
        print(f"Error reading {division}: {e}")
    return matches


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.split()
    lines = []
    current_line = []
    current_width = 0
    for word in words:
        word_bbox = draw.textbbox((0, 0), word, font=font)
        word_width = word_bbox[2] - word_bbox[0]
        space_width = draw.textbbox((0, 0), " ", font=font)[2] - draw.textbbox((0, 0), " ", font=font)[0]
        if current_line and current_width + word_width + space_width <= max_width:
            current_line.append(word)
            current_width += word_width + space_width
        elif not current_line and word_width <= max_width:
            current_line.append(word)
            current_width = word_width
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_width = word_width
    if current_line:
        lines.append(" ".join(current_line))
    return lines


def get_wrapped_text_block_height(lines: list[str], font: ImageFont.FreeTypeFont, line_spacing: int, draw: ImageDraw.ImageDraw) -> int:
    if not lines: return 0
    total = 0
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        total += bbox[3] - bbox[1]
        if i < len(lines) - 1: total += line_spacing
    return total


def calculate_division_height(division_name: str, matches: list, is_first_division: bool = True) -> int:
    height = HEADING_SPACE
    if not is_first_division:
        height += FIXTURE_SPACING
    last_cup_name = None
    for j, match in enumerate(matches):
        fixture_height = BOX_HEIGHT
        if j > 0:
            fixture_height += FIXTURE_SPACING
        cup_name = match[4]
        if division_name.lower() == "cup" and cup_name and cup_name != last_cup_name:
            fixture_height += CUP_NAME_SPACE
            last_cup_name = cup_name
        height += fixture_height
    return height


# --- Graphic Generation ---
def create_match_graphic_with_heading(sections_to_draw: list[tuple], logos_folder: str, save_folder: str, part_number: int, template_path: str, current_date: datetime):
    try:
        template = Image.open(template_path).convert("RGBA")
        if template.size != (IMAGE_WIDTH, IMAGE_HEIGHT):
            raise ValueError(f"Template must be {IMAGE_WIDTH}x{IMAGE_HEIGHT}")
    except Exception as e:
        print(f"Template error: {e}. Using blank.")
        template = Image.new("RGBA", (IMAGE_WIDTH, IMAGE_HEIGHT), (0, 0, 0, 0))

    img = template.copy()
    d = ImageDraw.Draw(img)

    # Load fonts
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE_NORMAL)
        score_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_SCORE)
        heading_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_HEADING)
        cup_name_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_CUP_NAME)
        small_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_SMALL_TEAM_NAME)
        penalty_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_PENALTY_SCORE)
        label_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_PENALTIES_LABEL)
    except Exception as e:
        print(f"Font load failed: {e}. Using default.")
        font = score_font = heading_font = cup_name_font = small_font = penalty_font = label_font = ImageFont.load_default()

    # Date circle
    high_res = DATE_CIRCLE_SIZE * HIGH_RES_SCALE
    circle = Image.new("RGBA", (high_res, high_res), (0, 0, 0, 0))
    cd = ImageDraw.Draw(circle)
    day = current_date.strftime("%d")
    month = current_date.strftime("%B")
    year = current_date.strftime("%Y")
    font_size = FONT_SIZE_DATE
    while font_size >= FONT_SIZE_DATE_MIN:
        df = ImageFont.truetype(FONT_PATH, int(font_size * HIGH_RES_SCALE))
        db = cd.textbbox((0, 0), day, font=df)
        mb = cd.textbbox((0, 0), month, font=df)
        yb = cd.textbbox((0, 0), year, font=df)
        w = max(db[2] - db[0], mb[2] - mb[0], yb[2] - yb[0])
        h = (db[3] - db[1]) + (mb[3] - mb[1]) + (yb[3] - yb[1]) + 10 * HIGH_RES_SCALE
        if w <= DATE_TEXT_MAX_WIDTH * HIGH_RES_SCALE and h <= DATE_TEXT_MAX_HEIGHT * HIGH_RES_SCALE:
            break
        font_size -= 2
    if font_size < FONT_SIZE_DATE_MIN:
        print(f"Warning: Date font reduced to {FONT_SIZE_DATE_MIN}")
    cd.ellipse([0, 0, high_res, high_res], fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=DATE_CIRCLE_STROKE * HIGH_RES_SCALE)
    total_h = (db[3] - db[1]) + (mb[3] - mb[1]) + (yb[3] - yb[1]) + 10 * HIGH_RES_SCALE
    y = (high_res // 2) - total_h // 2
    cd.text(((high_res - (db[2] - db[0])) // 2, y), day, fill=(0, 0, 0, 255), font=df)
    y += (db[3] - db[1]) + 5 * HIGH_RES_SCALE
    cd.text(((high_res - (mb[2] - mb[0])) // 2, y), month, fill=(0, 0, 0, 255), font=df)
    y += (mb[3] - mb[1]) + 5 * HIGH_RES_SCALE
    cd.text(((high_res - (yb[2] - yb[0])) // 2, y), year, fill=(0, 0, 0, 255), font=df)
    circle = circle.resize((DATE_CIRCLE_SIZE, DATE_CIRCLE_SIZE), Image.Resampling.LANCZOS)
    img.paste(circle, (DATE_CIRCLE_X, DATE_CIRCLE_Y), circle)

    y_offset = CONTENT_START_Y
    is_first = True
    for div_name, matches in sections_to_draw:
        # Use clean heading
        heading = "Cup" if div_name.lower().startswith("cup") else div_name
        if not is_first:
            y_offset += FIXTURE_SPACING
        bbox = d.textbbox((0, 0), heading, font=heading_font)
        x = (IMAGE_WIDTH - (bbox[2] - bbox[0])) // 2
        d.text((x, y_offset + 20), heading, fill=(255, 255, 255), font=heading_font)
        y_offset += 20 + (bbox[3] - bbox[1]) + 20

        last_cup = None
        for match in matches:
            t1, s1, s2, t2, cup_name, pen = match

            if div_name.lower() == "cup" and cup_name and cup_name != last_cup:
                bbox = d.textbbox((0, 0), cup_name, font=cup_name_font)
                d.text((LEFT_PADDING, y_offset + 5), cup_name, fill=(255, 255, 0), font=cup_name_font)
                y_offset += 5 + (bbox[3] - bbox[1]) + 10
                last_cup = cup_name
            else:
                y_offset += FIXTURE_SPACING

            logo1 = get_logo(t1, logos_folder)
            logo2 = get_logo(t2, logos_folder)
            img.paste(logo1, (LEFT_PADDING + 1, int(y_offset) + 1), logo1)

            # Team 1
            x1 = LEFT_PADDING + LOGO_WIDTH + 3
            d.rectangle([x1, y_offset, x1 + TEAM_BOX_WIDTH, y_offset + BOX_HEIGHT - 1], fill=(0, 0, 0, 180))
            f1 = small_font if t1 in TEAMS_FOR_SMALLER_FONT else font
            lines1 = wrap_text(t1, f1, TEAM_BOX_WIDTH - 20, d)
            h1 = get_wrapped_text_block_height(lines1, f1, LINE_SPACING, d)
            start_y1 = y_offset + (BOX_HEIGHT - h1) // 2 + VISUAL_Y_OFFSET_CORRECTION
            cur_y = start_y1
            for line in lines1:
                bbox = d.textbbox((0, 0), line, font=f1)
                lx = x1 + (TEAM_BOX_WIDTH - (bbox[2] - bbox[0])) // 2
                d.text((lx, cur_y), line, fill=(255, 255, 255), font=f1)
                cur_y += (bbox[3] - bbox[1]) + LINE_SPACING

            # Score
            sx = x1 + TEAM_BOX_WIDTH + 5
            d.rectangle([sx, y_offset, sx + SCORE_BOX_WIDTH, y_offset + BOX_HEIGHT - 1], fill=(0, 0, 0, 180))
            score_text = f"{s1} - {s2}"
            sbox = d.textbbox((0, 0), score_text, font=score_font)
            if div_name.lower() == "cup" and pen:
                reg_y = y_offset + 8
                d.text((sx + (SCORE_BOX_WIDTH - (sbox[2] - sbox[0])) // 2, reg_y), score_text, fill=(255, 255, 255), font=score_font)
                label = "PENALTIES"
                lb = d.textbbox((0, 0), label, font=label_font)
                ly = reg_y + (sbox[3] - sbox[1]) + 12
                d.text((sx + (SCORE_BOX_WIDTH - (lb[2] - lb[0])) // 2, ly), label, fill=(255, 255, 0), font=label_font)
                pb = d.textbbox((0, 0), pen, font=penalty_font)
                py = ly + (lb[3] - lb[1]) + 8
                d.text((sx + (SCORE_BOX_WIDTH - (pb[2] - pb[0])) // 2, py), pen, fill=(255, 255, 255), font=penalty_font)
            else:
                d.text((sx + (SCORE_BOX_WIDTH - (sbox[2] - sbox[0])) // 2, y_offset + (BOX_HEIGHT - (sbox[3] - sbox[1])) // 2), score_text, fill=(255, 255, 255), font=score_font)

            # Team 2
            x2 = sx + SCORE_BOX_WIDTH + 5
            d.rectangle([x2, y_offset, x2 + TEAM_BOX_WIDTH, y_offset + BOX_HEIGHT - 1], fill=(0, 0, 0, 180))
            f2 = small_font if t2 in TEAMS_FOR_SMALLER_FONT else font
            lines2 = wrap_text(t2, f2, TEAM_BOX_WIDTH - 20, d)
            h2 = get_wrapped_text_block_height(lines2, f2, LINE_SPACING, d)
            start_y2 = y_offset + (BOX_HEIGHT - h2) // 2 + VISUAL_Y_OFFSET_CORRECTION
            cur_y = start_y2
            for line in lines2:
                bbox = d.textbbox((0, 0), line, font=f2)
                lx = x2 + (TEAM_BOX_WIDTH - (bbox[2] - bbox[0])) // 2
                d.text((lx, cur_y), line, fill=(255, 255, 255), font=f2)
                cur_y += (bbox[3] - bbox[1]) + LINE_SPACING
            img.paste(logo2, (x2 + TEAM_BOX_WIDTH + 2, int(y_offset) + 1), logo2)

            y_offset += BOX_HEIGHT
        is_first = False

    # Save
    os.makedirs(save_folder, exist_ok=True)
    time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join(save_folder, f"Results_Part{part_number}_{time_str}.png")
    img.save(path)
    print(f"Graphic saved: {path}")
    return path  # Return for Streamlit


# --- MAIN LOGIC WITH FIXTURES-STYLE LEAGUE GROUPING ---
def generate_results_graphics(file_path: str, logos_folder: str, save_folder: str, template_path: str):
    # Date
    try:
        df = pd.read_excel(file_path, sheet_name='Date')
        if not df.empty and 'Date' in df.columns:
            date_str = str(df['Date'].iloc[0]).strip()
            current_date = pd.to_datetime(date_str, errors='coerce')
            if pd.isna(current_date):
                raise ValueError()
            print(f"Date parsed: {current_date.strftime('%d %B %Y')}")
        else:
            raise ValueError()
    except Exception as e:
        print(f"Date error: {e}. Using now.")
        current_date = datetime.now()

    # Load data
    cup_matches = parse_matches_from_file(file_path, "Cup")
    league_divisions_map = {}
    for div in LEAGUE_DIVISION_ORDER:
        matches = parse_matches_from_file(file_path, div)
        if matches:
            league_divisions_map[div] = {'division': div, 'matches': matches}

    # Reconstruct in fixed order
    league_divisions = [league_divisions_map[div] for div in LEAGUE_DIVISION_ORDER if div in league_divisions_map]

    # Group cups
    cup_groups = defaultdict(list)
    for m in cup_matches:
        cup_name = m[4] if m[4] else "Unknown Cup"
        cup_groups[cup_name].append(m)
    sorted_cup = sorted(cup_groups.items(), key=lambda x: x[0] != "Hampshire Trophy Cup")
    cup_divisions = [{'division': f"Cup - {name}", 'matches': matches} for name, matches in sorted_cup]

    part_number = 1
    trophy_included = False
    saved_paths = []

    # === CUP GRAPHICS ===
    remaining_cup = cup_divisions.copy()
    print("\n=== CUP GRAPHICS ===")
    while remaining_cup:
        sections = []
        height = 0
        next_cup = []
        first = True
        for div in remaining_cup:
            name = div['division']
            matches = div['matches']
            h = calculate_division_height("Cup", matches, first)
            if name.startswith("Cup - Hampshire Trophy Cup") and not trophy_included:
                if height + h <= SAFE_CONTENT_HEIGHT_LIMIT or not sections:
                    sections.append(("Cup", matches))
                    height += h
                    first = False
                    trophy_included = True
                else:
                    next_cup.append(div)
                continue
            elif name.startswith("Cup - Hampshire Vase Cup"):
                max_m = 2 if trophy_included and part_number == 1 else 6
                if len(matches) > max_m:
                    cur = matches[:max_m]
                    rem = matches[max_m:]
                    ch = calculate_division_height("Cup", cur, first)
                    if height + ch <= SAFE_CONTENT_HEIGHT_LIMIT or not sections:
                        sections.append(("Cup", cur))
                        height += ch
                        first = False
                        if rem:
                            next_cup.append({'division': name, 'matches': rem})
                    else:
                        next_cup.append(div)
                else:
                    if height + h <= SAFE_CONTENT_HEIGHT_LIMIT or not sections:
                        sections.append(("Cup", matches))
                        height += h
                        first = False
                    else:
                        next_cup.append(div)
                continue
            else:
                if height + h <= SAFE_CONTENT_HEIGHT_LIMIT or not sections:
                    sections.append(("Cup", matches))
                    height += h
                    first = False
                else:
                    next_cup.append(div)
        if sections:
            print(f"Final Cup Part {part_number}: {[s[0] for s in sections]}, {height}px")
            path = create_match_graphic_with_heading(sections, logos_folder, save_folder, part_number, template_path, current_date)
            saved_paths.append(path)
            part_number += 1
        remaining_cup = next_cup
        if not next_cup and sections:
            break

    # === LEAGUE GRAPHICS WITH D1+D2+D3 GROUPING ===
    print("\n=== LEAGUE GRAPHICS ===")
    d1_data = next((d for d in league_divisions if d['division'] == "Division 1"), None)
    d2_data = next((d for d in league_divisions if d['division'] == "Division 2"), None)
    d3_data = next((d for d in league_divisions if d['division'] == "Division 3"), None)
    d4_data = next((d for d in league_divisions if d['division'] == "Division 4"), None)

    # PART 1: First Graphic — D1 + D2 + D3 (if fits)
    g1_sections = []
    g1_height = 0
    g1_first = True
    d3_in_g1 = False
    if d1_data:
        h1 = calculate_division_height(d1_data['division'], d1_data['matches'], g1_first)
        if h1 <= SAFE_CONTENT_HEIGHT_LIMIT:
            g1_sections.append((d1_data['division'], d1_data['matches']))
            g1_height += h1
            g1_first = False
    if d2_data and g1_sections:
        h2 = calculate_division_height(d2_data['division'], d2_data['matches'], g1_first)
        if g1_height + h2 <= SAFE_CONTENT_HEIGHT_LIMIT:
            g1_sections.append((d2_data['division'], d2_data['matches']))
            g1_height += h2
            g1_first = False
    if d3_data and len(g1_sections) >= 1:
        h3 = calculate_division_height(d3_data['division'], d3_data['matches'], g1_first)
        if g1_height + h3 <= SAFE_CONTENT_HEIGHT_LIMIT:
            g1_sections.append((d3_data['division'], d3_data['matches']))
            g1_height += h3
            d3_in_g1 = True
    if g1_sections:
        print(f"\n--- League Graphic {part_number}: {[s[0] for s in g1_sections]}, {g1_height}px ---")
        path = create_match_graphic_with_heading(g1_sections, logos_folder, save_folder, part_number, template_path, current_date)
        saved_paths.append(path)
        part_number += 1

    # PART 2: Remaining divisions
    remaining_league = []
    if d2_data and not any(s[0] == "Division 2" for s in g1_sections):
        remaining_league.append(d2_data)
    if d3_data and not d3_in_g1:
        remaining_league.append(d3_data)
    if d4_data:
        remaining_league.append(d4_data)

    # PART 3: Greedy for rest
    while remaining_league:
        sections = []
        height = 0
        next_league = []
        first = True
        for div in remaining_league:
            name = div['division']
            matches = div['matches']
            h = calculate_division_height(name, matches, first and not sections)
            if height + h <= SAFE_CONTENT_HEIGHT_LIMIT or not sections:
                sections.append((name, matches))
                height += h
                first = False
            else:
                next_league.append(div)
        if sections:
            print(f"Final League Part {part_number}: {[s[0] for s in sections]}, {height}px")
            path = create_match_graphic_with_heading(sections, logos_folder, save_folder, part_number, template_path, current_date)
            saved_paths.append(path)
            part_number += 1
        remaining_league = next_league
        if not next_league and sections:
            break

    print(f"\nCompleted: {part_number - 1} graphic(s) generated")
    return saved_paths


print("All functions ready.")

# --- Execution (for local testing) ---
if __name__ == "__main__":
    generate_results_graphics(RESULTS_FILE_PATH, LOGOS_FOLDER, SAVE_FOLDER, TEMPLATE_PATH)
