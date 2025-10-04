import os
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from datetime import datetime
from collections import defaultdict
import math
import zipfile 

print("✅ STARTING SCRIPT")

# --- Streamlit/GitHub Environment Setup ---
# Define the base directory of the script to ensure all paths are relative and work on the server
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 

# --- Configuration Constants (FIXED FOR RELATIVE PATHS) ---
# Paths
# Using relative paths joined from BASE_DIR for Streamlit compatibility
FIXTURES_FILE_PATH = os.path.join(BASE_DIR, "results.xlsx")
LOGOS_FOLDER = os.path.join(BASE_DIR, "Logos")  
SAVE_FOLDER = os.path.join(BASE_DIR, "Graphics") 
TEMPLATES_FOLDER = os.path.join(BASE_DIR, "Templates") 
TEMPLATE_PATH = os.path.join(TEMPLATES_FOLDER, "fixtures_template.png")
FONT_PATH = os.path.join(BASE_DIR, "BebasNeue Regular.ttf") 

# Image Dimensions and Layout
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1350
CONTENT_HEIGHT_LIMIT = 1040
SAFE_CONTENT_HEIGHT_LIMIT = 950 # Conservative height limit
CONTENT_START_Y = 251.97
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
FONT_SIZE_SCORE = 55
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

# Teams that might need a smaller font
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
        
        # Calculate Bounding Box of typical text for accurate height
        heading_bbox = HEADING_FONT_TEMP.getbbox("League")
        cup_name_bbox = CUP_NAME_FONT_TEMP.getbbox("Example Cup Name")
        
        HEADING_TEXT_HEIGHT = heading_bbox[3] - heading_bbox[1]
        HEADING_SPACE = 20 + HEADING_TEXT_HEIGHT + 20 # 20px buffer before, 20px after

        CUP_NAME_TEXT_HEIGHT = cup_name_bbox[3] - cup_name_bbox[1]
        CUP_NAME_SPACE = 5 + CUP_NAME_TEXT_HEIGHT + 10 # 5px buffer before, 10px after
    except IOError:
        print("Warning: Could not load required fonts for pre-calculation. Using default height estimates.")
        HEADING_SPACE = 100 
        CUP_NAME_SPACE = 70
        HEADING_TEXT_HEIGHT = 60 
        CUP_NAME_TEXT_HEIGHT = 35 
else:
    print("Warning: Configured font path is invalid. Using default height estimates.")
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
    
    # 1. Check Special Mapping
    logo_filename = SPECIAL_LOGO_MAPPING.get(team_name_lower, f'{team_name_clean}.png')
    
    # 2. Search Subfolders (Current Teams, Old Teams)
    for subfolder in ['Current Teams', 'Old Teams']:
        search_path = os.path.join(logos_folder, subfolder, logo_filename)
        if os.path.exists(search_path):
            try:
                # Use Image.LANCZOS for quality resize
                return Image.open(search_path).convert("RGBA").resize((LOGO_WIDTH, LOGO_HEIGHT), Image.LANCZOS)
            except Exception as e:
                print(f"Error loading logo '{logo_filename}' for {team_name}: {e}")

    # 3. Fallback to generic
    generic_logo_path = os.path.join(logos_folder, 'genericlogo.png')
    try:
        print(f"Warning: No specific logo found for {team_name}. Using generic logo.")
        return Image.open(generic_logo_path).convert("RGBA").resize((LOGO_WIDTH, LOGO_HEIGHT), Image.LANCZOS)
    except Exception as e:
        print(f"Error loading generic logo: {e}. Using gray placeholder.")
        return Image.new("RGBA", (LOGO_WIDTH, LOGO_HEIGHT), (200, 200, 200, 255))

def parse_matches_from_file(file_path: str, division: str) -> list[tuple]:
    """Reads matches from the specified Excel sheet."""
    matches = []
    try:
        excel_data = pd.read_excel(file_path, sheet_name=division)
        for _, row in excel_data.iterrows():
            team_1_name = str(row['Team 1 name']).strip() if pd.notna(row['Team 1 name']) else ""
            team_1_score = str(row['Team 1 score']) if pd.notna(row['Team 1 score']) else "-"
            team_2_score = str(row['Team 2 score']) if pd.notna(row['Team 2 score']) else "-"
            team_2_name = str(row['Team 2 name']).strip() if pd.notna(row['Team 2 name']) else ""
            cup_name = None
            if division.lower() == "cup" and 'Cup name' in row and pd.notna(row['Cup name']):
                cup_name = str(row['Cup name']).strip()
            if team_1_name and team_2_name:
                matches.append((team_1_name, team_1_score, team_2_score, team_2_name, cup_name))
    except Exception as e:
        pass
    return matches

def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """Wraps text to fit within a maximum pixel width."""
    words = text.split()
    lines = []
    current_line = []
    current_width = 0
    
    # Use textbbox for accurate width calculation
    def get_text_width(txt, f):
        return draw.textbbox((0, 0), txt, font=f)[2] - draw.textbbox((0, 0), txt, font=f)[0]
        
    space_width = get_text_width(" ", font)
    
    for word in words:
        word_width = get_text_width(word, font)
             
        # Check if adding the word to the current line exceeds max_width
        if current_line and current_width + word_width + space_width <= max_width:
            current_line.append(word)
            current_width += word_width + space_width
        elif not current_line and word_width <= max_width:
            current_line.append(word)
            current_width = word_width
        else:
            # Word is too wide or doesn't fit, start a new line
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_width = word_width
            
    if current_line:
        lines.append(" ".join(current_line))
    return lines

def get_wrapped_text_block_height(lines: list[str], font: ImageFont.FreeTypeFont, line_spacing: int, draw: ImageDraw.ImageDraw) -> int:
    """Calculates the total vertical space needed for a block of wrapped text."""
    if not lines:
        return 0
    total_height = 0
    for i, line in enumerate(lines):
        # Calculate actual line height using textbbox
        line_bbox = draw.textbbox((0, 0), line, font=font)
        line_actual_height = line_bbox[3] - line_bbox[1]
        
        total_height += line_actual_height
        if i < len(lines) - 1:
            total_height += line_spacing # Add spacing between lines
    return total_height

def calculate_division_height(division_name: str, matches: list, is_first_division: bool = True) -> int:
    """Calculate the height required for a division or cup group with accurate spacing"""
    
    # 1. Height of the main heading (Division X or Cup)
    total_height = HEADING_SPACE
    
    # 2. Add spacing before the first division/section if it's not the first one on the graphic
    if not is_first_division:
        total_height += FIXTURE_SPACING # 15px spacing between sections

    last_cup_name = None
    
    for j, match in enumerate(matches):
        # Base height for the match fixture itself
        match_height = BOX_HEIGHT
        
        # Space for Cup Name header
        cup_name = match[4]
        if division_name.lower().startswith("cup") and cup_name and cup_name != last_cup_name:
            match_height += CUP_NAME_SPACE
            last_cup_name = cup_name
        
        # Space *before* the fixture.
        # This space is added:
        # For any fixture that isn't the first in its division group (i.e., not the one immediately following the Division/Cup Heading or a Cup Name header).
        if j > 0:
            # Check if the previous match started a new cup name block
            prev_match_cup_name = matches[j-1][4] if j > 0 else None
            current_match_cup_name = match[4]
            
            # Add spacing only if the match is not the first *or* is not the first after a new cup header
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
    except IOError as e:
        print(f"Warning: Could not load font from {FONT_PATH}. Using default font. Error: {e}")
        font = score_font = heading_font = cup_name_font = small_font = ImageFont.load_default()

    # --- Date Circle Generation ---
    high_res_size = DATE_CIRCLE_SIZE * HIGH_RES_SCALE
    circle_img = Image.new("RGBA", (high_res_size, high_res_size), (0, 0, 0, 0))
    circle_draw = ImageDraw.Draw(circle_img)
    
    day_text = current_date.strftime("%d")
    month_text = current_date.strftime("%b").upper()
    year_text = current_date.strftime("%Y")
    
    font_size = FONT_SIZE_DATE
    date_font = None 
    
    while font_size >= FONT_SIZE_DATE_MIN:
        try:
            date_font = ImageFont.truetype(FONT_PATH, int(font_size * HIGH_RES_SCALE))
        except IOError:
            date_font = ImageFont.load_default() 

        day_bbox = circle_draw.textbbox((0, 0), day_text, font=date_font)
        month_bbox = circle_draw.textbbox((0, 0), month_text, font=date_font)
        year_bbox = circle_draw.textbbox((0, 0), year_text, font=date_font)
        
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
    
    text_height_half = (day_height + month_height + year_height + 10 * HIGH_RES_SCALE) // 2
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
        
        # 1. Add extra spacing between divisions/sections (if not the first section)
        if not is_first_division_of_graphic:
            y_offset += FIXTURE_SPACING # 15px gap
        
        # 2. Draw Division/Cup Heading
        heading = "Cup" if division_name.lower().startswith("cup") else division_name
        
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
            team_1_name, _, _, team_2_name, cup_name = match
            
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
            
            if not logo_1 or not logo_2:
                # This should not happen if generic logo fallback works, but as a safeguard:
                print(f"Error drawing logos for {team_1_name} vs {team_2_name}. Skipping match drawing.")
                continue

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

            vs_box_x = team_1_box_x + TEAM_BOX_WIDTH + 5
            vs_box_y = y_offset
            d.rectangle([vs_box_x, vs_box_y, vs_box_x + SCORE_BOX_WIDTH, vs_box_y + BOX_HEIGHT - 1], fill=(0, 0, 0, 180))
            
            vs_text = "vs"
            vs_bbox = d.textbbox((0, 0), vs_text, font=score_font)
            vs_text_x = vs_box_x + (SCORE_BOX_WIDTH - (vs_bbox[2] - vs_bbox[0])) // 2
            vs_text_y = vs_box_y + (BOX_HEIGHT - (vs_bbox[3] - vs_bbox[1])) // 2 + visual_y_offset_correction
            d.text((vs_text_x, vs_text_y), vs_text, fill=(255, 255, 255), font=score_font)

            team_2_box_x = vs_box_x + SCORE_BOX_WIDTH + 5
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
        
    output_file_path = os.path.join(save_folder, f"Fixtures_Part{part_number}_{current_time}.png")
    
    img.save(output_file_path) 
    print(f"Graphic saved to: {output_file_path}")


def generate_fixtures_graphics(file_path: str, logos_folder: str, save_folder: str, template_path: str):
    """
    Main function to generate fixture graphics, separating cup and league matches.
    """
    # --- 1. Load Date ---
    try:
        date_df = pd.read_excel(file_path, sheet_name='Date')
        if not date_df.empty and 'Date' in date_df.columns:
            date_str = str(date_df['Date'].iloc[0]).strip()
            current_date = pd.to_datetime(date_str, errors='coerce')
            if pd.isna(current_date):
                raise ValueError(f"Invalid date format: {date_str}")
        else:
            print("Warning: 'Date' sheet empty or missing 'Date' column. Using current date.")
            current_date = datetime.now()
    except Exception as e:
        print(f"Error reading 'Date' sheet from file: {e}. Using current date.")
        current_date = datetime.now()

    # --- 2. Load and Group Matches ---
    divisions = ["Cup", "Division 1", "Division 2", "Division 3", "Division 4"]
    cup_divisions = []
    league_divisions = []

    # Process cup matches by grouping by cup name
    cup_matches = parse_matches_from_file(file_path, "Cup")
    if cup_matches:
        cup_groups = defaultdict(list)
        for match in cup_matches:
            cup_name = match[4] if match[4] else "Unknown Cup"
            cup_groups[cup_name].append(match)
        
        # Sort to prioritize Hampshire Trophy Cup
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
        if matches:
            league_divisions.append({
                'division': div,
                'matches': matches,
                'original_div': div
            })

    # --- 3. Generate Graphics (Height-based Packing with Specific Cup Rules) ---
    
    # 3a. Process cup matches first
    remaining_cup_divisions = cup_divisions
    part_number = 1
    
    trophy_cup_name = "Cup - Hampshire Trophy Cup"
    
    print("\n=== Processing Cup Graphics ===")
    while remaining_cup_divisions:
        sections_to_draw = []
        current_height = 0
        next_graphic_divisions = []
        is_first_division_of_graphic = True

        print(f"\n--- Processing cup graphic {part_number} ---")
        
        i = 0
        while i < len(remaining_cup_divisions):
            div_data = remaining_cup_divisions[i]
            division_name = div_data['division']
            matches = div_data['matches']
            
            current_matches = matches
            remaining_matches = []
            
            # --- Determine which matches to include based on space and specific rules ---
            
            will_add_to_current = False
            temp_height = 0
            
            if division_name == trophy_cup_name:
                # Rule: Include all Trophy Cup matches if space allows.
                temp_height = calculate_division_height("Cup", current_matches, is_first_division_of_graphic)
                if current_height + temp_height <= SAFE_CONTENT_HEIGHT_LIMIT or not sections_to_draw:
                    will_add_to_current = True
                
            elif division_name == "Cup - Hampshire Vase Cup":
                # Rule: Max 2 Vase Cup matches if Trophy Cup is on the *current* graphic, otherwise up to 6
                trophy_cup_added_to_current_graphic = any(s[0] == "Cup" and s[1][0][4] == "Hampshire Trophy Cup" for s in sections_to_draw)
                
                max_matches = 2 if trophy_cup_added_to_current_graphic and part_number == 1 else 6
                
                if len(matches) > max_matches:
                    current_matches = matches[:max_matches]
                    remaining_matches = matches[max_matches:]
                
                temp_height = calculate_division_height("Cup", current_matches, is_first_division_of_graphic)
                
                if current_height + temp_height <= SAFE_CONTENT_HEIGHT_LIMIT or not sections_to_draw:
                    will_add_to_current = True
                
            else:
                # Other cup types (treat as a single block)
                temp_height = calculate_division_height("Cup", current_matches, is_first_division_of_graphic)
                if current_height + temp_height <= SAFE_CONTENT_HEIGHT_LIMIT or not sections_to_draw:
                    will_add_to_current = True
                
            # --- Execute inclusion or deferral ---

            if will_add_to_current:
                sections_to_draw.append(("Cup", current_matches))
                current_height += temp_height
                is_first_division_of_graphic = False
                
                if remaining_matches:
                     next_graphic_divisions.append({
                        'division': division_name,
                        'matches': remaining_matches,
                        'original_div': "Cup"
                    })
                i += 1
            else:
                # If it didn't fit (and it's not the first division), move the whole block to the next graphic
                next_graphic_divisions.append(div_data)
                i += 1
        
        # --- Post-loop graphic generation and cleanup ---

        if sections_to_draw:
            print(f"Final sections for cup graphic {part_number}: {[len(section[1]) for section in sections_to_draw]} matches")
            print(f"Total height used: {current_height}px / {SAFE_CONTENT_HEIGHT_LIMIT}px")
            create_match_graphic_with_heading(sections_to_draw, logos_folder, save_folder, part_number, template_path, current_date)
            part_number += 1
        
        if not sections_to_draw and remaining_cup_divisions:
             print("Error: Remaining cup divisions are too large to fit on a single graphic. Stopping cup processing.")
             break

        remaining_cup_divisions = next_graphic_divisions
        if not remaining_cup_divisions and sections_to_draw:
             break

    # 3b. Process league matches (Standard packing logic)
    remaining_league_divisions = league_divisions
    print("\n=== Processing League Graphics ===")
    while remaining_league_divisions:
        sections_to_draw = []
        current_height = 0
        next_graphic_divisions = []
        is_first_division_of_graphic = True

        print(f"\n--- Processing league graphic {part_number} ---")
        
        for div_data in remaining_league_divisions:
            division_name = div_data['division']
            matches = div_data['matches']
            
            division_height = calculate_division_height(division_name, matches, is_first_division_of_graphic)

            if current_height + division_height <= SAFE_CONTENT_HEIGHT_LIMIT or not sections_to_draw:
                sections_to_draw.append((division_name, matches))
                current_height += division_height
                is_first_division_of_graphic = False
                print(f" -> Added {division_name} ({len(matches)} matches)")
            else:
                next_graphic_divisions.append(div_data)
                print(f" -> {division_name} doesn't fit. Moving to next graphic.")

        if sections_to_draw:
            print(f"Final sections for league graphic {part_number}: {[section[0] for section in sections_to_draw]}")
            print(f"Total height used: {current_height}px / {SAFE_CONTENT_HEIGHT_LIMIT}px")
            create_match_graphic_with_heading(sections_to_draw, logos_folder, save_folder, part_number, template_path, current_date)
            part_number += 1

        remaining_league_divisions = next_graphic_divisions

        if not sections_to_draw and remaining_league_divisions:
            print("Error: Remaining league divisions are too large to fit on a single graphic. Stopping league processing.")
            break
        
        if not remaining_league_divisions and sections_to_draw:
             break 

    print(f"\n✅ Completed generating {part_number-1} graphic(s)")

print("✅ All functions defined. Attempting to run main function.")
if __name__ == "__main__":
    generate_fixtures_graphics(FIXTURES_FILE_PATH, LOGOS_FOLDER, SAVE_FOLDER, TEMPLATE_PATH)
