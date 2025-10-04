import os
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from datetime import datetime
from collections import defaultdict
import math
import zipfile 

print("✅ STARTING RESULTS SCRIPT")

# --- Streamlit/GitHub Environment Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 

# --- Configuration Constants (Must match Fixtures script for consistency) ---
# Paths
RESULTS_FILE_PATH = os.path.join(BASE_DIR, "results.xlsx")
LOGOS_FOLDER = os.path.join(BASE_DIR, "Logos")  
SAVE_FOLDER = os.path.join(BASE_DIR, "Graphics") 
TEMPLATES_FOLDER = os.path.join(BASE_DIR, "Templates") 
TEMPLATE_PATH = os.path.join(TEMPLATES_FOLDER, "results_template.png") # Changed to results_template
FONT_PATH = os.path.join(BASE_DIR, "BebasNeue Regular.ttf") 

# Image Dimensions and Layout 
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1350
CONTENT_START_Y = 251.97
SAFE_CONTENT_HEIGHT_LIMIT = 950 # Conservative height limit

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
HEADING_SPACE = 0
CUP_NAME_SPACE = 0
HEADING_TEXT_HEIGHT = 0
CUP_NAME_TEXT_HEIGHT = 0

if os.path.exists(FONT_PATH):
    try:
        HEADING_FONT_TEMP = ImageFont.truetype(FONT_PATH, FONT_SIZE_HEADING)
        CUP_NAME_FONT_TEMP = ImageFont.truetype(FONT_PATH, FONT_SIZE_CUP_NAME)
        
        heading_bbox = HEADING_FONT_TEMP.getbbox("League")
        cup_name_bbox = CUP_NAME_FONT_TEMP.getbbox("Example Cup Name")
        
        HEADING_TEXT_HEIGHT = heading_bbox[3] - heading_bbox[1]
        HEADING_SPACE = 20 + HEADING_TEXT_HEIGHT + 20 

        CUP_NAME_TEXT_HEIGHT = cup_name_bbox[3] - cup_name_bbox[1]
        CUP_NAME_SPACE = 5 + CUP_NAME_TEXT_HEIGHT + 10 
    except IOError:
        HEADING_SPACE = 100 
        CUP_NAME_SPACE = 70
        HEADING_TEXT_HEIGHT = 60 
        CUP_NAME_TEXT_HEIGHT = 35 
else:
    HEADING_SPACE = 100 
    CUP_NAME_SPACE = 70
    HEADING_TEXT_HEIGHT = 60 
    CUP_NAME_TEXT_HEIGHT = 35 

print("✅ Configuration constants loaded.")

# --- Helper Functions ---

def get_logo(team_name: str, logos_folder: str) -> Image.Image:
    """Finds and resizes the logo for a team."""
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
        # print(f"Warning: No specific logo found for {team_name}. Using generic logo.")
        return Image.open(generic_logo_path).convert("RGBA").resize((LOGO_WIDTH, LOGO_HEIGHT), Image.LANCZOS)
    except Exception as e:
        print(f"Error loading generic logo: {e}. Using gray placeholder.")
        return Image.new("RGBA", (LOGO_WIDTH, LOGO_HEIGHT), (200, 200, 200, 255))

def parse_matches_from_file(file_path: str, division: str) -> list[tuple]:
    """Reads matches from the specified Excel sheet."""
    matches = []
    try:
        # Ensure 'Cup name' is included even for league tabs, in case it's used as a column
        excel_data = pd.read_excel(file_path, sheet_name=division)
        for _, row in excel_data.iterrows():
            team_1_name = str(row['Team 1 name']).strip() if pd.notna(row['Team 1 name']) else ""
            # Ensure scores are strings, even if they are integers in the Excel sheet
            team_1_score = str(int(row['Team 1 score'])) if pd.notna(row['Team 1 score']) and pd.api.types.is_number(row['Team 1 score']) else str(row['Team 1 score']) if pd.notna(row['Team 1 score']) else "-"
            team_2_score = str(int(row['Team 2 score'])) if pd.notna(row['Team 2 score']) and pd.api.types.is_number(row['Team 2 score']) else str(row['Team 2 score']) if pd.notna(row['Team 2 score']) else "-"
            team_2_name = str(row['Team 2 name']).strip() if pd.notna(row['Team 2 name']) else ""
            cup_name = None
            if 'Cup name' in row and pd.notna(row['Cup name']):
                cup_name = str(row['Cup name']).strip()
            
            # Check for valid scores (not '-') to ensure it's a result, not a postponed fixture
            if team_1_name and team_2_name and team_1_score != "-" and team_2_score != "-":
                matches.append((team_1_name, team_1_score, team_2_score, team_2_name, cup_name))
    except Exception as e:
        # print(f"Could not load sheet {division}: {e}")
        pass
    return matches

def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """Wraps text to fit within a maximum pixel width."""
    words = text.split()
    lines = []
    current_line = []
    
    def get_text_width(txt, f):
        return draw.textbbox((0, 0), txt, font=f)[2] - draw.textbbox((0, 0), txt, font=f)[0]
        
    space_width = get_text_width(" ", font)
    
    for word in words:
        word_width = get_text_width(word, font)
        
        # Calculate width of the current line + word + space
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
    """Calculates the total vertical space needed for a block of wrapped text."""
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
    """
    Calculate the height required for a division or cup group with accurate spacing.
    This logic is critical for the packing algorithm.
    """
    
    # 1. Height of the main heading (Division X Results or Cup Results)
    total_height = HEADING_SPACE
    
    # 2. Add spacing before the first division/section if it's not the first one on the graphic
    if not is_first_division:
        total_height += FIXTURE_SPACING # 15px spacing between sections

    last_cup_name = None
    
    for j, match in enumerate(matches):
        # Base height for the match result box
        match_height = BOX_HEIGHT
        
        # Space for Cup Name header
        cup_name = match[4]
        if division_name.lower().startswith("cup") and cup_name and cup_name != last_cup_name:
            match_height += CUP_NAME_SPACE
            last_cup_name = cup_name
        
        # Space *before* the fixture/result.
        if j > 0:
            prev_match_cup_name = matches[j-1][4] if j > 0 else None
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

    # Load Fonts
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE_NORMAL)
        score_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_SCORE)
        heading_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_HEADING)
        cup_name_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_CUP_NAME)
        small_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_SMALL_TEAM_NAME)
        date_font_base = FONT_SIZE_DATE # Base size for date circle calculation
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

        # Temporarily use default font if truetype failed just for bounding box calculation
        temp_date_font = date_font if isinstance(date_font, ImageFont.FreeTypeFont) else ImageFont.load_default() 

        day_bbox = circle_draw.textbbox((0, 0), day_text, font=temp_date_font)
        month_bbox = circle_draw.textbbox((0, 0), month_text, font=temp_date_font)
        year_bbox = circle_draw.textbbox((0, 0), year_text, font=temp_date_font)
        
        day_height = day_bbox[3] - day_bbox[1]
        month_height = month_bbox[3] - month_bbox[1]
        year_height = year_bbox[3] - year_bbox[1]

        max_text_width = max(day_bbox[2] - day_bbox[0], month_bbox[2] - month_bbox[0], year_bbox[2] - year_bbox[0])
        # 10 * HIGH_RES_SCALE is the total space between the 3 lines of text
        total_text_height = day_height + month_height + year_height + 10 * HIGH_RES_SCALE 
        
        if max_text_width <= DATE_TEXT_MAX_WIDTH * HIGH_RES_SCALE and total_text_height <= DATE_TEXT_MAX_HEIGHT * HIGH_RES_SCALE:
            break
        
        font_size -= 2
    
    # Draw Circle Background
    circle_draw.ellipse(
        [0, 0, high_res_size, high_res_size],
        fill=(255, 255, 255, 255),
        outline=(0, 0, 0, 255),
        width=DATE_CIRCLE_STROKE * HIGH_RES_SCALE
    )
    
    # Calculate Text Y positions
    text_height_half = total_text_height // 2
    day_y = DATE_CENTER_Y - text_height_half
    month_y = day_y + day_height + 5 * HIGH_RES_SCALE
    year_y = month_y + month_height + 5 * HIGH_RES_SCALE
    
    # Draw Text
    circle_draw.text((DATE_CENTER_X - (day_bbox[2] - day_bbox[0]) // 2, day_y), day_text, fill=(0, 0, 0, 255), font=date_font)
    circle_draw.text((DATE_CENTER_X - (month_bbox[2] - month_bbox[0]) // 2, month_y), month_text, fill=(0, 0, 0, 255), font=date_font)
    circle_draw.text((DATE_CENTER_X - (year_bbox[2] - year_bbox[0]) // 2, year_y), year_text, fill=(0, 0, 0, 255), font=date_font)
    
    # Downscale and paste date circle
    circle_img = circle_img.resize((DATE_CIRCLE_SIZE, DATE_CIRCLE_SIZE), Image.LANCZOS)
    img.paste(circle_img, (DATE_CIRCLE_X, DATE_CIRCLE_Y), circle_img)

    # --- Draw Matches ---
    y_offset = CONTENT_START_Y
    visual_y_offset_correction = VISUAL_Y_OFFSET_CORRECTION
    
    is_first_division_of_graphic = True 
    
    for division_name, matches in sections_to_draw:
        
        # 1. Add extra spacing between divisions/sections
        if not is_first_division_of_graphic:
            y_offset += FIXTURE_SPACING 
        
        # 2. Draw Division/Cup Heading
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
            
            # 3. Draw Cup Name (if applicable and different from the last one)
            if division_name.lower().startswith("cup") and cup_name and cup_name != last_cup_name:
                
                cup_name_x = LEFT_PADDING
                cup_name_bbox = d.textbbox((0, 0), cup_name, font=cup_name_font)
                cup_name_text_height = cup_name_bbox[3] - cup_name_bbox[1]
                
                cup_name_text_y = y_offset + 5 + (CUP_NAME_TEXT_HEIGHT - cup_name_text_height) / 2
                d.text((cup_name_x, cup_name_text_y), cup_name, fill=(255, 255, 0), font=cup_name_font)
                
                y_offset += CUP_NAME_SPACE 
                last_cup_name = cup_name
                is_first_fixture_in_section = True # Reset for fixture spacing

            # 4. Add spacing between fixtures
            if not is_first_fixture_in_section:
                y_offset += FIXTURE_SPACING

            # 5. Draw Fixture Box and Content
            logo_1 = get_logo(team_1_name, logos_folder)
            logo_2 = get_logo(team_2_name, logos_folder)
            
            # Team 1 Logo and Box
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

            # Score Box (CRITICAL CHANGE: DRAW SCORES)
            score_box_x = team_1_box_x + TEAM_BOX_WIDTH + 5
            score_box_y = y_offset
            d.rectangle([score_box_x, score_box_y, score_box_x + SCORE_BOX_WIDTH, score_box_y + BOX_HEIGHT - 1], fill=(100, 100, 100, 200)) # Darker background for results
            
            score_text = f"{score_1} - {score_2}"
            score_bbox = d.textbbox((0, 0), score_text, font=score_font)
            score_width = score_bbox[2] - score_bbox[0]
            score_height = score_bbox[3] - score_bbox[1]
            score_text_x = score_box_x + (SCORE_BOX_WIDTH - score_width) // 2
            score_text_y = score_box_y + (BOX_HEIGHT - score_height) // 2 + visual_y_offset_correction
            d.text((score_text_x, score_text_y), score_text, fill=(255, 255, 255), font=score_font)

            # Team 2 Box and Logo
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
            
            # Advance Y offset by the fixture height
            y_offset += BOX_HEIGHT
            
            is_first_fixture_in_section = False
        
        is_first_division_of_graphic = False 

    # Final Image Saving 
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
        
    output_file_path = os.path.join(save_folder, f"Results_Part{part_number}_{current_time}.png")
    
    img.save(output_file_path) 
    print(f"Graphic saved to: {output_file_path}")


# --- MAIN LOGIC (Containing the fix for UnboundLocalError) ---
def generate_results_graphics(file_path: str, logos_folder: str, save_folder: str, template_path: str):
    """
    Main function to generate results graphics, implementing height-based packing
    and splitting for cup matches.
    """
    # 1. Load Date
    try:
        date_df = pd.read_excel(file_path, sheet_name='Date')
        date_str = str(date_df['Date'].iloc[0]).strip()
        current_date = pd.to_datetime(date_str, errors='coerce')
        if pd.isna(current_date): raise ValueError()
        print(f"Date '{date_str}' successfully parsed as {current_date.strftime('%d %B %Y')}.")
    except Exception:
        print("Warning: Could not read date from file. Using current date.")
        current_date = datetime.now()

    # 2. Load and Group Matches
    divisions = ["Cup", "Division 1", "Division 2", "Division 3", "Division 4"]
    cup_divisions = []
    league_divisions = []

    # Process cup matches by grouping by cup name
    cup_matches = parse_matches_from_file(file_path, "Cup")
    print(f"Loaded {len(cup_matches)} matches from Cup tab in XLSX file.")
    if cup_matches:
        cup_groups = defaultdict(list)
        for match in cup_matches:
            cup_name = match[4] if match[4] else "Unknown Cup"
            cup_groups[cup_name].append(match)
        
        sorted_cup_groups = sorted(cup_groups.items(), key=lambda x: (x[0] != "Hampshire Trophy Cup", x[0])) 
        
        for cup_name, matches in sorted_cup_groups:
            cup_divisions.append({
                'division': f"Cup - {cup_name}",
                'matches': matches,
                'original_div': "Cup"
            })

    # Collect league divisions
    for div in divisions[1:]:
        matches = parse_matches_from_file(file_path, div)
        print(f"Loaded {len(matches)} matches from {div} tab in XLSX file.")
        if matches:
            league_divisions.append({
                'division': div,
                'matches': matches,
                'original_div': div
            })

    # 3. Generate Graphics (Height-based Packing)
    
    # 🚨 FIX 1: Initialize remaining_league_divisions with the initial league divisions 🚨
    remaining_cup_divisions = cup_divisions
    remaining_league_divisions = league_divisions # All league divisions start here
    
    part_number = 1
    trophy_cup_name = "Cup - Hampshire Trophy Cup"
    
    print("\n--- Starting Graphic Generation ---")
    
    # 🚨 FIX 2: Loop as long as there are matches in either list 🚨
    while remaining_cup_divisions or remaining_league_divisions:
        sections_to_draw = []
        current_height = 0
        next_cup_divisions = []
        next_league_divisions = []
        is_first_division_of_graphic = True

        print(f"\n--- Processing graphic {part_number} ---")
        print(f"Remaining divisions (Cup): {[d['division'] for d in remaining_cup_divisions]}")
        
        # --- 3a. Process Cup Divisions ---
        i = 0
        while i < len(remaining_cup_divisions):
            div_data = remaining_cup_divisions[i]
            division_name = div_data['division']
            matches = div_data['matches']
            
            current_matches = matches
            remaining_matches = []
            will_add_to_current = False
            
            # Recalculate full height for the block
            temp_height_full = calculate_division_height("Cup", current_matches, is_first_division_of_graphic)
            
            if division_name == trophy_cup_name:
                # Rule: Include all Trophy Cup matches if space allows.
                if current_height + temp_height_full <= SAFE_CONTENT_HEIGHT_LIMIT or not sections_to_draw:
                    will_add_to_current = True
                else:
                    # If it doesn't fit, move it to the next graphic (cannot split Trophy Cup)
                    next_cup_divisions.append(div_data)
                    i += 1
                    continue
            
            elif division_name == "Cup - Hampshire Vase Cup":
                # Rule: Max 2 Vase Cup matches if Trophy Cup is on the *current* graphic (assuming part 1), otherwise up to 6
                trophy_cup_added_to_current_graphic = any(s[0] == "Cup" and s[1][0][4] == "Hampshire Trophy Cup" for s in sections_to_draw)
                
                max_matches = 2 if trophy_cup_added_to_current_graphic and part_number == 1 else 6
                
                if len(matches) > max_matches:
                    current_matches = matches[:max_matches]
                    remaining_matches = matches[max_matches:]
                    
                temp_height = calculate_division_height("Cup", current_matches, is_first_division_of_graphic) # Height of the subset
                
                if current_height + temp_height <= SAFE_CONTENT_HEIGHT_LIMIT or not sections_to_draw:
                    will_add_to_current = True
                else:
                    # The max_matches subset didn't fit, so push the whole original block to the next graphic
                    next_cup_divisions.append(div_data)
                    print(f"Cup - Hampshire Vase Cup ({len(current_matches)} matches) does not fit.")
                    i += 1
                    continue
            
            else:
                # Other cup types (general splitting logic)
                if current_height + temp_height_full <= SAFE_CONTENT_HEIGHT_LIMIT or not sections_to_draw:
                    will_add_to_current = True
                    temp_height = temp_height_full
                else:
                    # Force split of a too-large cup block if it won't fit whole
                    max_fit_matches = 0
                    
                    for k in range(1, len(matches) + 1):
                        test_height = calculate_division_height("Cup", matches[:k], is_first_division_of_graphic)
                        if current_height + test_height <= SAFE_CONTENT_HEIGHT_LIMIT:
                             max_fit_matches = k
                        elif not sections_to_draw and test_height <= SAFE_CONTENT_HEIGHT_LIMIT:
                             max_fit_matches = k
                        else:
                            break
                    
                    if max_fit_matches > 0:
                        current_matches = matches[:max_fit_matches]
                        remaining_matches = matches[max_fit_matches:]
                        temp_height = calculate_division_height("Cup", current_matches, is_first_division_of_graphic)
                        will_add_to_current = True
                    else:
                        print(f"CRITICAL: {division_name} cannot fit a single match. Skipping.")
                        i += 1
                        continue # Skip this un-packable division


            # --- Execute inclusion or deferral ---
            if will_add_to_current and current_matches:
                sections_to_draw.append(("Cup", current_matches))
                current_height += temp_height
                is_first_division_of_graphic = False
                print(f" -> Added {division_name} ({len(current_matches)} matches). Total height: {current_height}px.")

                if remaining_matches:
                     next_cup_divisions.append({
                        'division': division_name,
                        'matches': remaining_matches,
                        'original_div': "Cup"
                    })
                i += 1
            else:
                # If it didn't fit, move the whole block/rest to the next graphic's cup list
                next_cup_divisions.append(div_data)
                i += 1
                
        # --- 3b. Process League Divisions (Only if no Cup divisions remain to process) ---
        if not next_cup_divisions: # Check against the 'next' list to see if all remaining cup divisions were processed
            league_divisions_to_pack = remaining_league_divisions 
            remaining_league_divisions = [] # Prepare for the next set of leftovers
            
            i = 0
            while i < len(league_divisions_to_pack):
                div_data = league_divisions_to_pack[i]
                division_name = div_data['division']
                matches = div_data['matches']
                
                division_height = calculate_division_height(division_name, matches, is_first_division_of_graphic)

                if current_height + division_height <= SAFE_CONTENT_HEIGHT_LIMIT or not sections_to_draw:
                    sections_to_draw.append((division_name, matches))
                    current_height += division_height
                    is_first_division_of_graphic = False
                    print(f" -> Added {division_name} ({len(matches)} matches). Total height: {current_height}px.")
                    i += 1
                elif not sections_to_draw and division_height > SAFE_CONTENT_HEIGHT_LIMIT:
                    print(f"CRITICAL: {division_name} ({len(matches)} matches, {division_height}px) is too tall to fit on a single graphic ({SAFE_CONTENT_HEIGHT_LIMIT}px). Skipping/Error.")
                    i += 1
                else:
                    # Move the rest of the league divisions to the next graphic's processing list
                    next_league_divisions.extend(league_divisions_to_pack[i:])
                    break # Stop processing league divisions for this graphic
        else:
            # If cup divisions remain for the next graphic, push all current league matches to the next league list
            next_league_divisions.extend(remaining_league_divisions)


        # --- Post-loop graphic generation and cleanup ---

        if sections_to_draw:
            print(f"Final sections for graphic {part_number}: {[s[0] for s in sections_to_draw]}")
            print(f"Total height used: {current_height}px / {SAFE_CONTENT_HEIGHT_LIMIT}px")
            create_match_graphic_with_heading(sections_to_draw, logos_folder, save_folder, part_number, TEMPLATE_PATH, current_date)
            part_number += 1
        
        # Error check for infinite loop
        if not sections_to_draw and (remaining_cup_divisions or remaining_league_divisions):
             print("\nError: Remaining divisions are too large to fit on a single graphic, even the first one. Stopping processing.")
             break

        remaining_cup_divisions = next_cup_divisions
        remaining_league_divisions = next_league_divisions


    print(f"\n✅ Completed generating {part_number-1} graphic(s)")
    print("Results graphics generated successfully!")


# --- Execution ---
print("✅ All functions defined. Attempting to run main function.")
if __name__ == "__main__":
    generate_results_graphics(RESULTS_FILE_PATH, LOGOS_FOLDER, SAVE_FOLDER, TEMPLATE_PATH)