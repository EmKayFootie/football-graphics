import os
from PIL import Image, ImageDraw, ImageFont # Corrected import
import pandas as pd
from datetime import datetime
from collections import defaultdict
import math

print("✅ STARTING SCRIPT")

# --- Streamlit/GitHub Environment Setup ---
# Define the base directory of the script to ensure all paths are relative and work on the server
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 

# --- Configuration Constants (FIXED FOR RELATIVE PATHS) ---
# Paths
# 🛑 FIX: Use relative paths joined from BASE_DIR for Streamlit compatibility
FIXTURES_FILE_PATH = os.path.join(BASE_DIR, "results.xlsx")
LOGOS_FOLDER = os.path.join(BASE_DIR, "Logos")  
SAVE_FOLDER = os.path.join(BASE_DIR, "Graphics") # This folder must exist on your local machine
TEMPLATES_FOLDER = os.path.join(BASE_DIR, "Templates") 
TEMPLATE_PATH = os.path.join(TEMPLATES_FOLDER, "fixtures_template.png")
FONT_PATH = os.path.join(BASE_DIR, "BebasNeue Regular.ttf") # Font file must be in the repo root

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
HIGH_RES_SCALE = 2 # Used for date circle rendering
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

# Teams that might need a smaller font (for text wrapping)
TEAMS_FOR_SMALLER_FONT = ["AFC Aldermaston A", "AFC Aldermaston B"]

# --- Pre-calculate spacing based on font ---
HEADING_SPACE = 0
CUP_NAME_SPACE = 0

# Check if font path is valid for pre-calculation
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
        # Fallback if font exists but can't be loaded by PIL
        print("Warning: Could not load required fonts for pre-calculation. Using default height estimates.")
        HEADING_SPACE = 100 
        CUP_NAME_SPACE = 70
else:
    # Fallback if font doesn't exist at all
    print("Warning: Configured font path is invalid. Using default height estimates.")
    HEADING_SPACE = 100 
    CUP_NAME_SPACE = 70


print("✅ Configuration constants loaded.")

# --- Helper Functions ---

def get_logo(team_name: str, logos_folder: str) -> Image.Image:
    """Finds and resizes the logo for a team."""
    team_name_clean = team_name.strip()
    team_name_lower = team_name_clean.lower()
    
    logo_filename = SPECIAL_LOGO_MAPPING.get(team_name_lower, f'{team_name_clean}.png')
    
    # Search 'Current Teams' and 'Old Teams'
    for subfolder in ['Current Teams', 'Old Teams']:
        search_path = os.path.join(logos_folder, subfolder, logo_filename)
        if os.path.exists(search_path):
            try:
                # 🛑 FIX: Changed ImageResampling.LANCZOS to Image.LANCZOS
                return Image.open(search_path).convert("RGBA").resize((LOGO_WIDTH, LOGO_HEIGHT), Image.LANCZOS)
            except Exception as e:
                print(f"Error loading logo '{logo_filename}' for {team_name}: {e}")

    generic_logo_path = os.path.join(logos_folder, 'genericlogo.png')
    try:
        print(f"Warning: No specific logo found for {team_name}. Using generic logo.")
        # 🛑 FIX: Changed ImageResampling.LANCZOS to Image.LANCZOS
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
        # print(f"Error reading the file for {division}: {e}") # Keep this quiet if sheet doesn't exist
        pass
    return matches

def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """Wraps text to fit within a maximum pixel width."""
    words = text.split()
    lines = []
    current_line = []
    current_width = 0
    # Use a space width approximation
    if hasattr(font, 'getlength'):
        space_width = font.getlength(" ")
    else:
        # Fallback for default font
        space_width = 8 
    
    for word in words:
        if hasattr(font, 'getlength'):
            word_width = font.getlength(word)
        else:
             # Use textbbox as a fallback for width calculation
             word_width = draw.textbbox((0, 0), word, font=font)[2] - draw.textbbox((0, 0), word, font=font)[0]
             
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
    """Calculate the height required for a division or cup group."""
    division_height = 0
    
    # 1. Spacing BEFORE the division section
    if not is_first_division:
        division_height += FIXTURE_SPACING # 15px spacing between sections
        
    # 2. Height for the Heading
    division_height += HEADING_SPACE
    
    last_cup_name = None
    
    for j, match in enumerate(matches):
        fixture_height_with_buffers = BOX_HEIGHT
        
        # 3. Spacing BEFORE the fixture
        # (Only if it's not the first fixture *after* the heading/cup name)
        is_first_in_section = j == 0
        if division_name.lower().startswith("cup") and match[4] and match[4] != last_cup_name and j > 0:
            # If we're starting a new cup group, the spacing is already included in CUP_NAME_SPACE
            pass
        elif not is_first_in_section:
            fixture_height_with_buffers += FIXTURE_SPACING
            
        # 4. Check for Cup Name space
        cup_name = match[4]
        if division_name.lower().startswith("cup") and cup_name and cup_name != last_cup_name:
            fixture_height_with_buffers += CUP_NAME_SPACE
            last_cup_name = cup_name
            
            # Since CUP_NAME_SPACE includes a bottom buffer, we need to ensure we don't double-space.
            # If this is the start of a cup section, remove the FIXTURE_SPACING we might have added above
            # This logic is complex, so we ensure the space is added *once*.
            if not is_first_in_section:
                fixture_height_with_buffers -= FIXTURE_SPACING 
                
        division_height += fixture_height_with_buffers
    
    return division_height

# --- Main Graphic Generation Function (FIXED) ---
def create_match_graphic_with_heading(sections_to_draw: list[tuple], logos_folder: str, save_folder: str, part_number: int, template_path: str, current_date: datetime):
    try:
        template = Image.open(template_path).convert("RGBA")
    except Exception as e:
        print(f"Error loading template: {e}. Using transparent background instead.")
        template = Image.new("RGBA", (IMAGE_WIDTH, IMAGE_HEIGHT), (0, 0, 0, 0))
    img = template.copy()
    d = ImageDraw.Draw(img)

    # 🛑 FONT FIX START: Loading and Verification
    if not os.path.exists(FONT_PATH):
        print(f"FATAL ERROR: Configured FONT_PATH does not exist: {FONT_PATH}")
        print("Please ensure the font file is committed to your GitHub repository.")
        return 
        
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE_NORMAL)
        score_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_SCORE)
        heading_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_HEADING)
        cup_name_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_CUP_NAME)
        small_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_SMALL_TEAM_NAME)
        date_font = ImageFont.truetype(FONT_PATH, int(FONT_SIZE_DATE * HIGH_RES_SCALE))
    except IOError as e:
        print(f"FATAL ERROR: PIL failed to load font from {FONT_PATH}. Error: {e}")
        print("The font file may be corrupted or incompatible with Pillow.")
        return 
    # 🛑 FONT FIX END

    # --- Date Circle Generation ---
    high_res_size = DATE_CIRCLE_SIZE * HIGH_RES_SCALE
    circle_img = Image.new("RGBA", (high_res_size, high_res_size), (0, 0, 0, 0))
    circle_draw = ImageDraw.Draw(circle_img)
    
    day_text = current_date.strftime("%d")
    month_text = current_date.strftime("%b").upper()
    year_text = current_date.strftime("%Y")
    
    # Calculate optimal date font size
    font_size = FONT_SIZE_DATE
    while font_size >= FONT_SIZE_DATE_MIN:
        # Re-load font at the appropriate size for high-res rendering
        date_font = ImageFont.truetype(FONT_PATH, int(font_size * HIGH_RES_SCALE))
        
        # Calculate text bounding boxes for fitting
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
    
    # Draw the circle (using the calculated date_font)
    circle_draw.ellipse(
        [0, 0, high_res_size, high_res_size],
        fill=(255, 255, 255, 255),
        outline=(0, 0, 0, 255),
        width=DATE_CIRCLE_STROKE * HIGH_RES_SCALE
    )
    
    # Calculate vertical positions for centered text
    text_height_half = (day_height + month_height + year_height + 10 * HIGH_RES_SCALE) // 2
    day_y = DATE_CENTER_Y - text_height_half
    month_y = day_y + day_height + 5 * HIGH_RES_SCALE
    year_y = month_y + month_height + 5 * HIGH_RES_SCALE
    
    circle_draw.text((DATE_CENTER_X - (day_bbox[2] - day_bbox[0]) // 2, day_y), day_text, fill=(0, 0, 0, 255), font=date_font)
    circle_draw.text((DATE_CENTER_X - (month_bbox[2] - month_bbox[0]) // 2, month_y), month_text, fill=(0, 0, 0, 255), font=date_font)
    circle_draw.text((DATE_CENTER_X - (year_bbox[2] - year_bbox[0]) // 2, year_y), year_text, fill=(0, 0, 0, 255), font=date_font)
    
    # 🛑 FIX: Changed ImageResampling.LANCZOS to Image.LANCZOS
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
        
        # Calculate text position (Centered horizontally)
        heading_bbox = d.textbbox((0, 0), heading, font=heading_font)
        heading_width = heading_bbox[2] - heading_bbox[0]
        heading_text_height = heading_bbox[3] - heading_bbox[1]
        heading_x = (IMAGE_WIDTH - heading_width) // 2
        
        # Draw heading text (y_offset + 20 is the start of the text block)
        heading_text_y = y_offset + 20 + (HEADING_TEXT_HEIGHT - heading_text_height) / 2
        d.text((heading_x, heading_text_y), heading, fill=(255, 255, 255), font=heading_font)
        
        # Advance y_offset past the heading and its top/bottom buffer
        y_offset += HEADING_SPACE 
        
        last_cup_name = None
        is_first_fixture_in_division = True
        
        for match in matches:
            team_1_name, _, _, team_2_name, cup_name = match
            
            # 3. Draw Cup Name (if applicable and different from the last one)
            if division_name.lower().startswith("cup") and cup_name and cup_name != last_cup_name:
                
                # Calculate text position (Left-aligned)
                cup_name_x = LEFT_PADDING
                cup_name_bbox = d.textbbox((0, 0), cup_name, font=cup_name_font)
                cup_name_text_height = cup_name_bbox[3] - cup_name_bbox[1]
                
                # Draw cup name text (y_offset + 5 is the start of the text block)
                cup_name_text_y = y_offset + 5 + (CUP_NAME_TEXT_HEIGHT - cup_name_text_height) / 2
                d.text((cup_name_x, cup_name_text_y), cup_name, fill=(255, 255, 0), font=cup_name_font)
                
                # Advance y_offset past the cup name block
                y_offset += CUP_NAME_SPACE 
                last_cup_name = cup_name
                is_first_fixture_in_division = True # Reset for fixture spacing

            # 4. Add spacing between fixtures
            if not is_first_fixture_in_division:
                y_offset += FIXTURE_SPACING

            # 5. Draw Fixture Box and Content
            logo_1 = get_logo(team_1_name, logos_folder)
            logo_2 = get_logo(team_2_name, logos_folder)
            
            # ... (Team 1 Logic) ...
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
                line_height = line_bbox[3] - line_bbox[1]
                line_x = team_1_box_x + (TEAM_BOX_WIDTH - line_width) // 2
                d.text((line_x, current_line_y_team1), line, fill=(255, 255, 255), font=team_1_font)
                current_line_y_team1 += line_height + LINE_SPACING

            # ... (vs Logic) ...
            vs_box_x = team_1_box_x + TEAM_BOX_WIDTH + 5
            vs_box_y = y_offset
            d.rectangle([vs_box_x, vs_box_y, vs_box_x + SCORE_BOX_WIDTH, vs_box_y + BOX_HEIGHT - 1], fill=(0, 0, 0, 180))
            
            vs_text = "vs"
            vs_bbox = d.textbbox((0, 0), vs_text, font=score_font)
            vs_text_x = vs_box_x + (SCORE_BOX_WIDTH - (vs_bbox[2] - vs_bbox[0])) // 2
            vs_text_y = vs_box_y + (BOX_HEIGHT - (vs_bbox[3] - vs_bbox[1])) // 2 + visual_y_offset_correction
            d.text((vs_text_x, vs_text_y), vs_text, fill=(255, 255, 255), font=score_font)

            # ... (Team 2 Logic) ...
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
                line_height = line_bbox[3] - line_bbox[1]
                line_x = team_2_box_x + (TEAM_BOX_WIDTH - line_width) // 2
                d.text((line_x, current_line_y_team2), line, fill=(255, 255, 255), font=team_2_font)
                current_line_y_team2 += line_height + LINE_SPACING

            logo_2_x = team_2_box_x + TEAM_BOX_WIDTH + 2
            img.paste(logo_2, (logo_2_x, int(y_offset) + 1), logo_2)
            
            # Advance Y offset by the fixture height
            y_offset += BOX_HEIGHT
            
            is_first_fixture_in_division = False
        
        is_first_division_of_graphic = False 

    # Final Image Saving (This will save locally for testing)
    # Streamlit Cloud deployments generally don't use this output folder, 
    # but the image object 'img' is what you would pass to st.image()
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Ensure local save folder exists for testing
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
        
    output_file_path = os.path.join(save_folder, f"Fixtures_Part{part_number}_{current_time}.png")
    img.save(output_file_path)
    print(f"Graphic saved to: {output_file_path}")
    # img.show() # Uncomment if you want the image to pop up immediately


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
    
    cup_matches = parse_matches_from_file(file_path, "Cup")
    cup_groups = defaultdict(list)
    if cup_matches:
        for match in cup_matches:
            cup_name = match[4] if match[4] else "Unknown Cup"
            cup_groups[cup_name].append(match)
    
    # Sort cup groups (Hampshire Trophy Cup first, then alphabetical)
    sorted_cup_groups = sorted(cup_groups.items(), key=lambda x: (x[0] != "Hampshire Trophy Cup", x[0]))
    
    all_sections = []
    # Add sorted cup divisions
    for cup_name, matches in sorted_cup_groups:
        all_sections.append({
            'division': f"Cup - {cup_name}",
            'matches': matches,
        })

    # Add league divisions
    for div in divisions[1:]:
        matches = parse_matches_from_file(file_path, div)
        if matches:
            all_sections.append({
                'division': div,
                'matches': matches,
            })

    # --- 3. Generate Graphics (Height-based Packing) ---
    final_graphics_sections = []
    current_graphic = []
    current_height = 0
    is_first_division_of_graphic = True

    for div_data in all_sections:
        division_name = div_data['division']
        matches = div_data['matches']
        
        # Determine the section type for height calculation
        calc_div_name = "Cup" if division_name.lower().startswith("cup") else division_name
        
        # NOTE: Using 'True' here for the initial section height calculation is correct only for the very first item
        # We need to rely on the logic inside the function to track spacing accurately
        division_height = calculate_division_height(calc_div_name, matches, is_first_division_of_graphic)
        
        if current_height + division_height <= SAFE_CONTENT_HEIGHT_LIMIT or not current_graphic:
            # It fits, or it's the first section of a new graphic
            current_graphic.append((calc_div_name, matches))
            current_height += division_height
            is_first_division_of_graphic = False
        else:
            # Doesn't fit, finalize the current graphic and start a new one
            final_graphics_sections.append(current_graphic)
            
            # Recalculate the height of the current section, assuming it is now the FIRST on the NEW graphic
            division_height_new_start = calculate_division_height(calc_div_name, matches, is_first_division=True)
            
            # Start a new graphic with the current section
            current_graphic = [(calc_div_name, matches)]
            current_height = division_height_new_start
            is_first_division_of_graphic = False
            
    # Add the last graphic
    if current_graphic:
        final_graphics_sections.append(current_graphic)

    # --- 4. Render Graphics ---
    part_number = 1
    if final_graphics_sections:
        for sections_to_draw in final_graphics_sections:
            print(f"\n--- RENDERING GRAPHIC PART {part_number} ---")
            create_match_graphic_with_heading(sections_to_draw, logos_folder, save_folder, part_number, template_path, current_date)
            part_number += 1
    else:
        print("\n⚠️ No matches were found. No graphics generated.")

    print(f"\n✅ Completed generating {part_number-1} graphic(s)")

print("✅ All functions defined. Attempting to run main function.")
if __name__ == "__main__":
    generate_fixtures_graphics(FIXTURES_FILE_PATH, LOGOS_FOLDER, SAVE_FOLDER, TEMPLATE_PATH)