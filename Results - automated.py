import os
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from datetime import datetime
from collections import defaultdict

print("STARTING RESULTS SCRIPT")

# --- Streamlit/GitHub Environment Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Configuration Constants ---
# Paths
RESULTS_FILE_PATH = os.path.join(BASE_DIR, "results.xlsx")
LOGOS_FOLDER = os.path.join(BASE_DIR, "Logos")
SAVE_FOLDER = os.path.join(BASE_DIR, "Graphics")
TEMPLATES_FOLDER = os.path.join(BASE_DIR, "Templates")
TEMPLATE_PATH = os.path.join(TEMPLATES_FOLDER, "results_template.png")
FONT_PATH = os.path.join(BASE_DIR, "BebasNeue Regular.ttf")  # ← Critical

# Image Dimensions and Layout
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1350
CONTENT_START_Y = 251.97
SAFE_CONTENT_HEIGHT_LIMIT = 950

LEFT_PADDING = 5
RIGHT_PADDING = 5
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
DATE_CENTER_X = (DATE_CIRCLE_SIZE * HIGH_RES_SCALE) // 2
DATE_CENTER_Y = (DATE_CIRCLE_SIZE * HIGH_RES_SCALE) // 2

# Font Sizes
FONT_SIZE_NORMAL = 65
FONT_SIZE_SCORE = 75
FONT_SIZE_HEADING = 64
FONT_SIZE_CUP_NAME = 39
FONT_SIZE_SMALL_TEAM_NAME = 50
FONT_SIZE_DATE = 40
FONT_SIZE_DATE_MIN = 30

# Visual Adjustments
VISUAL_Y_OFFSET_CORRECTION = -5

# Special Team Logo Mappings
SPECIAL_LOGO_MAPPING = {
    "afc aldermaston a": "AFC Aldermaston.png",
    "afc aldermaston b": "AFC Aldermaston.png",
}
TEAMS_FOR_SMALLER_FONT = ["AFC Aldermaston A", "AFC Aldermaston B"]

# --- Pre-calculate spacing based on font ---
HEADING_SPACE = 100
CUP_NAME_SPACE = 70
HEADING_TEXT_HEIGHT = 60
CUP_NAME_TEXT_HEIGHT = 35

if os.path.exists(FONT_PATH):
    try:
        HEADING_FONT_TEMP = ImageFont.truetype(FONT_PATH, FONT_SIZE_HEADING)
        CUP_NAME_FONT_TEMP = ImageFont.truetype(FONT_PATH, FONT_SIZE_CUP_NAME)
        
        heading_bbox = HEADING_FONT_TEMP.getbbox("League Results")
        cup_name_bbox = CUP_NAME_FONT_TEMP.getbbox("Example Cup Name")
        
        HEADING_TEXT_HEIGHT = heading_bbox[3] - heading_bbox[1]
        HEADING_SPACE = 20 + HEADING_TEXT_HEIGHT + 20

        CUP_NAME_TEXT_HEIGHT = cup_name_bbox[3] - cup_name_bbox[1]
        CUP_NAME_SPACE = 5 + CUP_NAME_TEXT_HEIGHT + 10
    except Exception as e:
        print(f"Font pre-calc failed: {e}. Using defaults.")
else:
    print(f"Font not found at {FONT_PATH}. Using defaults.")

print("Configuration constants loaded.")

# --- Helper Functions ---

def get_logo(team_name: str, logos_folder: str) -> Image.Image:
    team_name_clean = team_name.strip()
    team_name_lower = team_name_clean.lower()
    
    logo_filename = SPECIAL_LOGO_MAPPING.get(team_name_lower, f'{team_name_clean}.png')
    
    for subfolder in ['Current Teams', 'Old Teams']:
        search_path = os.path.join(logos_folder, subfolder, logo_filename)
        if os.path.exists(search_path):
            try:
                return Image.open(search_path).convert("RGBA").resize((LOGO_WIDTH, LOGO_HEIGHT), Image.LANCZOS)
            except Exception as e:
                print(f"Error loading logo '{logo_filename}' for {team_name}: {e}")

    generic_logo_path = os.path.join(logos_folder, 'genericlogo.png')
    try:
        return Image.open(generic_logo_path).convert("RGBA").resize((LOGO_WIDTH, LOGO_HEIGHT), Image.LANCZOS)
    except Exception as e:
        print(f"Error loading generic logo: {e}. Using gray placeholder.")
        return Image.new("RGBA", (LOGO_WIDTH, LOGO_HEIGHT), (200, 200, 200, 255))

def parse_matches_from_file(file_path: str, division: str) -> list[tuple]:
    matches = []
    try:
        excel_data = pd.read_excel(file_path, sheet_name=division)
        for _, row in excel_data.iterrows():
            team_1_name = str(row['Team 1 name']).strip() if pd.notna(row['Team 1 name']) else ""
            team_1_score = str(int(row['Team 1 score'])) if pd.notna(row['Team 1 score']) and pd.api.types.is_number(row['Team 1 score']) else str(row['Team 1 score']) if pd.notna(row['Team 1 score']) else "-"
            team_2_score = str(int(row['Team 2 score'])) if pd.notna(row['Team 2 score']) and pd.api.types.is_number(row['Team 2 score']) else str(row['Team 2 score']) if pd.notna(row['Team 2 score']) else "-"
            team_2_name = str(row['Team 2 name']).strip() if pd.notna(row['Team 2 name']) else ""
            cup_name = None
            if 'Cup name' in row and pd.notna(row['Cup name']):
                cup_name = str(row['Cup name']).strip()
            
            if team_1_name and team_2_name and team_1_score != "-" and team_2_score != "-":
                matches.append((team_1_name, team_1_score, team_2_score, team_2_name, cup_name))
    except Exception as e:
        pass
    return matches

def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.split()
    lines = []
    current_line = []
    
    def get_text_width(txt, f):
        return draw.textbbox((0, 0), txt, font=f)[2] - draw.textbbox((0, 0), txt, font=f)[0]
        
    space_width = get_text_width(" ", font)
    
    for word in words:
        word_width = get_text_width(word, font)
        test_line = " ".join(current_line + [word])
        test_width = get_text_width(test_line, font)
             
        if not current_line and word_width <= max_width:
            current_line.append(word)
        elif current_line and test_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def get_wrapped_text_block_height(lines: list[str], font: ImageFont.FreeTypeFont, line_spacing: int, draw: ImageDraw.ImageDraw) -> int:
    if not lines:
        return 0
    total_height = 0
    for i, line in enumerate(lines):
        line_bbox = draw.textbbox((0, 0), line, font=font)
        line_actual_height = line_bbox[3] - line_bbox[1]
        total_height += line_actual_height
        if i < len(lines) - 1:
            total_height += line_spacing 
    return total_height

def calculate_division_height(division_name: str, matches: list, is_first_division: bool = True) -> int:
    total_height = HEADING_SPACE
    if not is_first_division:
        total_height += FIXTURE_SPACING

    last_cup_name = None
    for j, match in enumerate(matches):
        match_height = BOX_HEIGHT
        cup_name = match[4]
        if division_name.lower().startswith("cup") and cup_name and cup_name != last_cup_name:
            match_height += CUP_NAME_SPACE
            last_cup_name = cup_name
        
        if j > 0:
            prev_match_cup_name = matches[j-1][4]
            current_match_cup_name = match[4]
            is_start_of_new_cup_group = (division_name.lower().startswith("cup") and 
                                         current_match_cup_name and 
                                         current_match_cup_name != prev_match_cup_name)
            if not is_start_of_new_cup_group:
                match_height += FIXTURE_SPACING

        total_height += match_height
    return total_height

# --- Main Graphic Generation Function ---
def create_match_graphic_with_heading(sections_to_draw: list[tuple], logos_folder: str, save_folder: str, part_number: int, template_path: str, current_date: datetime):
    try:
        template = Image.open(template_path).convert("RGBA")
        if template.size != (IMAGE_WIDTH, IMAGE_HEIGHT):
            raise ValueError(f"Template must be exactly {IMAGE_WIDTH}x{IMAGE_HEIGHT} pixels.")
    except Exception as e:
        print(f"Error loading template: {e}. Using transparent background instead.")
        template = Image.new("RGBA", (IMAGE_WIDTH, IMAGE_HEIGHT), (0, 0, 0, 0))
        
    img = template.copy()
    d = ImageDraw.Draw(img)

    # --- Load Fonts (FIXED) ---
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE_NORMAL)
        score_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_SCORE)
        heading_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_HEADING)
        cup_name_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_CUP_NAME)
        small_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_SMALL_TEAM_NAME)  # ← NOW CORRECT
        date_font_base = FONT_SIZE_DATE
    except IOError as e:
        print(f"Warning: Could not load font from {FONT_PATH}. Using default font. Error: {e}")
        font = score_font = heading_font = cup_name_font = small_font = ImageFont.load_default()
        date_font_base = 40

    # --- Date Circle Generation ---
    high_res_size = DATE_CIRCLE_SIZE * HIGH_RES_SCALE
    circle_img = Image.new("RGBA", (high_res_size, high_res_size), (0, 0, 0, 0))
    circle_draw = ImageDraw.Draw(circle_img)
    
    day_text = current_date.strftime("%d")
    month_text = current_date.strftime("%b").upper()
    year_text = current_date.strftime("%Y")
    
    font_size = date_font_base
    date_font = None 
    
    while font_size >= FONT_SIZE_DATE_MIN:
        try:
            date_font = ImageFont.truetype(FONT_PATH, int(font_size * HIGH_RES_SCALE))
        except IOError:
            date_font = ImageFont.load_default() 

        temp_date_font = date_font if isinstance(date_font, ImageFont.FreeTypeFont) else ImageFont.load_default() 

        day_bbox = circle_draw.textbbox((0, 0), day_text, font=temp_date_font)
        month_bbox = circle_draw.textbbox((0, 0), month_text, font=temp_date_font)
        year_bbox = circle_draw.textbbox((0, 0), year_text, font=temp_date_font)
        
        day_height = day_bbox[3] - day_bbox[1]
        month_height = month_bbox[3] - month_bbox[1]
        year_height = year_bbox[3] - year_bbox[1]

        max_text_width = max(day_bbox[2] - day_bbox[0], month_bbox[2] - month_bbox[0], year_bbox[2] - year_bbox[0])
        total_text_height = day_height + month_height + year_height + 10 * HIGH_RES_SCALE 
        
        if max_text_width <= DATE_TEXT_MAX_WIDTH * HIGH_RES_SCALE and total_text_height <= DATE_TEXT_MAX_HEIGHT * HIGH_RES_SCALE:
            break
        
        font_size -= 2
    
    circle_draw.ellipse(
        [0, 0, high_res_size, high_res_size],
        fill=(255, 255, 255, 255),
        outline=(0, 0, 0, 255),
        width=DATE_CIRCLE_STROKE * HIGH_RES_SCALE
    )
    
    text_height_half = total_text_height // 2
    day_y = DATE_CENTER_Y - text_height_half
    month_y = day_y + day_height + 5 * HIGH_RES_SCALE
    year_y = month_y + month_height + 5 * HIGH_RES_SCALE
    
    circle_draw.text((DATE_CENTER_X - (day_bbox[2] - day_bbox[0]) // 2, day_y), day_text, fill=(0, 0, 0, 255), font=date_font)
    circle_draw.text((DATE_CENTER_X - (month_bbox[2] - month_bbox[0]) // 2, month_y), month_text, fill=(0, 0, 0, 255), font=date_font)
    circle_draw.text((DATE_CENTER_X - (year_bbox[2] - year_bbox[0]) // 2, year_y), year_text, fill=(0, 0, 0, 255), font=date_font)
    
    circle_img = circle_img.resize((DATE_CIRCLE_SIZE, DATE_CIRCLE_SIZE), Image.LANCZOS)
    img.paste(circle_img, (DATE_CIRCLE_X, DATE_CIRCLE_Y), circle_img)

    # --- Draw Matches ---
    y_offset = CONTENT_START_Y
    visual_y_offset_correction = VISUAL_Y_OFFSET_CORRECTION
    is_first_division_of_graphic = True 
    
    for division_name, matches in sections_to_draw:
        if not is_first_division_of_graphic:
            y_offset += FIXTURE_SPACING 
        
        heading = "Cup Results" if division_name.lower().startswith("cup") else f"{division_name} Results"
        heading_bbox = d.textbbox((0, 0), heading, font=heading_font)
        heading_width = heading_bbox[2] - heading_bbox[0]
        heading_text_height = heading_bbox[3] - heading_bbox[1]
        heading_x = (IMAGE_WIDTH - heading_width) // 2
        heading_text_y = y_offset + 20 + (HEADING_TEXT_HEIGHT - heading_text_height) / 2
        d.text((heading_x, heading_text_y), heading, fill=(255, 255, 255), font=heading_font)
        
        y_offset += HEADING_SPACE 
        
        last_cup_name = None
        is_first_fixture_in_section = True
        
        for match in matches:
            team_1_name, score_1, score_2, team_2_name, cup_name = match
            
            if division_name.lower().startswith("cup") and cup_name and cup_name != last_cup_name:
                cup_name_x = LEFT_PADDING
                cup_name_bbox = d.textbbox((0, 0), cup_name, font=cup_name_font)
                cup_name_text_height = cup_name_bbox[3] - cup_name_bbox[1]
                cup_name_text_y = y_offset + 5 + (CUP_NAME_TEXT_HEIGHT - cup_name_text_height) / 2
                d.text((cup_name_x, cup_name_text_y), cup_name, fill=(255, 255, 0), font=cup_name_font)
                y_offset += CUP_NAME_SPACE 
                last_cup_name = cup_name
                is_first_fixture_in_section = True

            if not is_first_fixture_in_section:
                y_offset += FIXTURE_SPACING

            logo_1 = get_logo(team_1_name, logos_folder)
            logo_2 = get_logo(team_2_name, logos_folder)
            
            logo_1_x = LEFT_PADDING + 1
            img.paste(logo_1, (logo_1_x, int(y_offset) + 1), logo_1)

            team_1_box_x = logo_1_x + LOGO_WIDTH + 2
            team_1_box_y = y_offset
            d.rectangle([team_1_box_x, team_1_box_y, team_1_box_x + TEAM_BOX_WIDTH, team_1_box_y + BOX_HEIGHT - 1], fill=(0, 0, 0, 180))
            
            team_1_font = small_font if team_1_name in TEAMS_FOR_SMALLER_FONT else font
            team_1_lines = wrap_text(team_1_name, team_1_font, TEAM_BOX_WIDTH - 20, d)
            team_1_total_text_block_height = get_wrapped_text_block_height(team_1_lines, team_1_font, LINE_SPACING, d)
            team_1_start_y_text = team_1_box_y + (BOX_HEIGHT - team_1_total_text_block_height) // 2 + visual_y_offset_correction
            
            current_line_y_team1 = team_1_start_y_text
            for line in team_1_lines:
                line_bbox = d.textbbox((0, 0), line, font=team_1_font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = team_1_box_x + (TEAM_BOX_WIDTH - line_width) // 2
                d.text((line_x, current_line_y_team1), line, fill=(255, 255, 255), font=team_1_font)
                current_line_y_team1 += (line_bbox[3] - line_bbox[1]) + LINE_SPACING

            score_box_x = team_1_box_x + TEAM_BOX_WIDTH + 5
            score_box_y = y_offset
            d.rectangle([score_box_x, score_box_y, score_box_x + SCORE_BOX_WIDTH, score_box_y + BOX_HEIGHT - 1], fill=(100, 100, 100, 200))
            
            score_text = f"{score_1} - {score_2}"
            score_bbox = d.textbbox((0, 0), score_text, font=score_font)
            score_width = score_bbox[2] - score_bbox[0]
            score_height = score_bbox[3] - score_bbox[1]
            score_text_x = score_box_x + (SCORE_BOX_WIDTH - score_width) // 2
            score_text_y = score_box_y + (BOX_HEIGHT - score_height) // 2 + visual_y_offset_correction
            d.text((score_text_x, score_text_y), score_text, fill=(255, 255, 255), font=score_font)

            team_2_box_x = score_box_x + SCORE_BOX_WIDTH + 5
            team_2_box_y = y_offset
            d.rectangle([team_2_box_x, team_2_box_y, team_2_box_x + TEAM_BOX_WIDTH, team_2_box_y + BOX_HEIGHT - 1], fill=(0, 0, 0, 180))
            
            team_2_font = small_font if team_2_name in TEAMS_FOR_SMALLER_FONT else font
            team_2_lines = wrap_text(team_2_name, team_2_font, TEAM_BOX_WIDTH - 20, d)
            team_2_total_text_block_height = get_wrapped_text_block_height(team_2_lines, team_2_font, LINE_SPACING, d)
            team_2_start_y_text = team_2_box_y + (BOX_HEIGHT - team_2_total_text_block_height) // 2 + visual_y_offset_correction
            
            current_line_y_team2 = team_2_start_y_text
            for line in team_2_lines:
                line_bbox = d.textbbox((0, 0), line, font=team_2_font)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = team_2_box_x + (TEAM_BOX_WIDTH - line_width) // 2
                d.text((line_x, current_line_y_team2), line, fill=(255, 255, 255), font=team_2_font)
                current_line_y_team2 += (line_bbox[3] - line_bbox[1]) + LINE_SPACING

            logo_2_x = team_2_box_x + TEAM_BOX_WIDTH + 2
            img.paste(logo_2, (logo_2_x, int(y_offset) + 1), logo_2)
            
            y_offset += BOX_HEIGHT
            is_first_fixture_in_section = False
        
        is_first_division_of_graphic = False 

    # --- Save ---
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    output_file_path = os.path.join(save_folder, f"Results_Part{part_number}_{current_time}.png")
    img.save(output_file_path) 
    print(f"Graphic saved to: {output_file_path}")

# --- MAIN LOGIC ---
def generate_results_graphics(file_path: str, logos_folder: str, save_folder: str, template_path: str):
    try:
        date_df = pd.read_excel(file_path, sheet_name='Date')
        date_str = str(date_df['Date'].iloc[0]).strip()
        current_date = pd.to_datetime(date_str, errors='coerce')
        if pd.isna(current_date): raise ValueError()
        print(f"Date '{date_str}' successfully parsed as {current_date.strftime('%d %B %Y')}.")
    except Exception:
        print("Warning: Could not read date from file. Using current date.")
        current_date = datetime.now()

    divisions = ["Cup", "Division 1", "Division 2", "Division 3", "Division 4"]
    cup_divisions = []
    league_divisions = []

    cup_matches = parse_matches_from_file(file_path, "Cup")
    print(f"Loaded {len(cup_matches)} matches from Cup tab in XLSX file.")
    if cup_matches:
        cup_groups = defaultdict(list)
        for match in cup_matches:
            cup_name = match[4] if match[4] else "Unknown Cup"
            cup_groups[cup_name].append(match)
        sorted_cup_groups = sorted(cup_groups.items(), key=lambda x: x[0] != "Hampshire Trophy Cup")
        for cup_name, matches in sorted_cup_groups:
            cup_divisions.append({
                'division': f"Cup - {cup_name}",
                'matches': matches,
                'original_div': "Cup"
            })

    for div in divisions[1:]:
        matches = parse_matches_from_file(file_path, div)
        print(f"Loaded {len(matches)} matches from {div} tab in XLSX file.")
        if matches:
            league_divisions.append({
                'division': div,
                'matches': matches,
                'original_div': div
            })

    remaining_cup = cup_divisions.copy()
    remaining_league = league_divisions.copy()
    part_number = 1

    print("\n--- Starting Graphic Generation ---")

    while remaining_cup or remaining_league:
        sections_to_draw = []
        current_height = 0
        next_cup = []
        next_league = []
        is_first = True

        print(f"\n--- Processing graphic {part_number} ---")
        print(f"Remaining Cup: {[d['division'] for d in remaining_cup]}")
        print(f"Remaining League: {[d['division'] for d in remaining_league]}")

        # --- PACK CUP FIRST ---
        i = 0
        while i < len(remaining_cup):
            div = remaining_cup[i]
            name = div['division']
            matches = div['matches']
            temp_height = 0

            full_height = calculate_division_height("Cup", matches, is_first)

            if name == "Cup - Hampshire Trophy Cup":
                if current_height + full_height <= SAFE_CONTENT_HEIGHT_LIMIT or not sections_to_draw:
                    sections_to_draw.append(("Cup", matches))
                    current_height += full_height
                    is_first = False
                    i += 1
                    print(f" -> Added {name} ({len(matches)} matches)")
                else:
                    next_cup.append(div)
                    i += 1
                continue

            elif name == "Cup - Hampshire Vase Cup":
                max_matches = 2 if any("Trophy" in s[0] for s in sections_to_draw) and part_number == 1 else 6
                if len(matches) > max_matches:
                    current_matches = matches[:max_matches]
                    remain_matches = matches[max_matches:]
                    temp_height = calculate_division_height("Cup", current_matches, is_first)
                else:
                    current_matches = matches
                    remain_matches = []
                    temp_height = full_height

                if current_height + temp_height <= SAFE_CONTENT_HEIGHT_LIMIT or not sections_to_draw:
                    sections_to_draw.append(("Cup", current_matches))
                    current_height += temp_height
                    is_first = False
                    if remain_matches:
                        next_cup.append({'division': name, 'matches': remain_matches, 'original_div': "Cup"})
                    i += 1
                    print(f" -> Added {name} ({len(current_matches)} matches)")
                else:
                    next_cup.append(div)
                    i += 1
                continue

            else:
                if current_height + full_height <= SAFE_CONTENT_HEIGHT_LIMIT or not sections_to_draw:
                    sections_to_draw.append(("Cup", matches))
                    current_height += full_height
                    is_first = False
                    i += 1
                    print(f" -> Added {name} ({len(matches)} matches)")
                else:
                    max_fit = 0
                    for k in range(1, len(matches) + 1):
                        h = calculate_division_height("Cup", matches[:k], is_first)
                        if current_height + h <= SAFE_CONTENT_HEIGHT_LIMIT or (not sections_to_draw and h <= SAFE_CONTENT_HEIGHT_LIMIT):
                            max_fit = k
                        else:
                            break
                    if max_fit > 0:
                        current_matches = matches[:max_fit]
                        remain_matches = matches[max_fit:]
                        temp_height = calculate_division_height("Cup", current_matches, is_first)
                        sections_to_draw.append(("Cup", current_matches))
                        current_height += temp_height
                        is_first = False
                        if remain_matches:
                            next_cup.append({'division': name, 'matches': remain_matches, 'original_div': "Cup"})
                        i += 1
                        print(f" -> Split {name}: {max_fit} matches")
                    else:
                        next_cup.append(div)
                        i += 1
                continue

        # --- PACK LEAGUE IF NO CUP LEFT ---
        if not next_cup and remaining_league:
            i = 0
            while i < len(remaining_league):
                div = remaining_league[i]
                name = div['division']
                matches = div['matches']
                h = calculate_division_height(name, matches, is_first)

                if current_height + h <= SAFE_CONTENT_HEIGHT_LIMIT or not sections_to_draw:
                    sections_to_draw.append((name, matches))
                    current_height += h
                    is_first = False
                    i += 1
                    print(f" -> Added {name} ({len(matches)} matches)")
                else:
                    next_league.extend(remaining_league[i:])
                    break

        # --- Generate ---
        if sections_to_draw:
            print(f"Final: {[s[0] for s in sections_to_draw]}, Height: {current_height}px")
            create_match_graphic_with_heading(sections_to_draw, logos_folder, save_folder, part_number, template_path, current_date)
            part_number += 1
        else:
            print("No sections fit. Stopping.")
            break

        remaining_cup = next_cup
        remaining_league = next_league

    print(f"\nCompleted generating {part_number-1} result graphic(s)")

print("All functions defined. Attempting to run main function.")
if __name__ == "__main__":
    generate_results_graphics(RESULTS_FILE_PATH, LOGOS_FOLDER, SAVE_FOLDER, TEMPLATE_PATH)
