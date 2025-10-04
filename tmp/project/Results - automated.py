import os
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from datetime import datetime
print("✅ STARTING RESULTS SCRIPT")
# --- Configuration Constants ---
# Paths
RESULTS_FILE_PATH = r"C:\Users\Matt\Desktop\Sunday Football\results.xlsx"
LOGOS_FOLDER = r"C:\Users\Matt\Desktop\Sunday Football\Logos"
SAVE_FOLDER = r"C:\Users\Matt\Desktop\Sunday Football\Graphics"
TEMPLATES_FOLDER = r"C:\Users\Matt\Desktop\Sunday Football\Templates"
RESULTS_TEMPLATE_PATH = os.path.join(TEMPLATES_FOLDER, "results_template.png")
FONT_PATH = r"C:\Users\Matt\AppData\Local\Microsoft\Windows\Fonts\BebasNeue Regular.ttf"
# Image Dimensions and Layout
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1350
CONTENT_HEIGHT_LIMIT = 1050 # Content area height within the template
CONTENT_START_Y = 251.97 # Start of the content area
# Match Box Dimensions and Spacing
LEFT_PADDING = 5
RIGHT_PADDING = 5
TEAM_BOX_WIDTH = 330
SCORE_BOX_WIDTH = 120
LOGO_WIDTH = 140
LOGO_HEIGHT = 120
BOX_HEIGHT = 120 # Height of each match box (including logos and text areas)
LINE_SPACING = 15 # Spacing between lines of wrapped text within a team name box
FIXTURE_SPACING = 15 # Default vertical spacing between individual matches
# Font Sizes
FONT_SIZE_NORMAL = 65 # For main team names
FONT_SIZE_SCORE = 55 # For scores (e.g., "5 - 3")
FONT_SIZE_HEADING = 64 # For division headings (e.g., "Division 1")
FONT_SIZE_CUP_NAME = 39 # For cup names (e.g., "Kelvin Cup")
FONT_SIZE_SMALL_TEAM_NAME = 50 # For specific long team names that need a smaller font
FONT_SIZE_DATE = 40 # Base font size for date text in circle
FONT_SIZE_DATE_MIN = 30 # Minimum font size for date if adjustment needed
FONT_SIZE_PENALTY_SCORE = 32 # Smaller font for penalty score
FONT_SIZE_PENALTIES_LABEL = 28 # Smaller font for "PENALTIES" label
# Visual Adjustments
VISUAL_Y_OFFSET_CORRECTION = -5 # Adjust text vertical centering
DATE_CIRCLE_SIZE = 142 # 142x142px circle for date
DATE_CIRCLE_X = 1080 - 138 - 142 # Right side, mirroring logo at X=138px
DATE_CIRCLE_Y = 95 # Same Y as logo
DATE_CIRCLE_STROKE = 3 # 3px black stroke for circle
HIGH_RES_SCALE = 2 # Scale for high-resolution circle drawing
DATE_TEXT_MAX_WIDTH = DATE_CIRCLE_SIZE - 20 # Max width for date text to fit in circle
DATE_TEXT_MAX_HEIGHT = DATE_CIRCLE_SIZE - 20 # Max height for date text
# Special Team Logo Mappings
SPECIAL_LOGO_MAPPING = {
    "afc aldermaston a": "AFC Aldermaston.png",
    "afc aldermaston b": "AFC Aldermaston.png",
    "eversley & california sunday": "Eversley & California.png",
}
# Teams that might need a smaller font
TEAMS_FOR_SMALLER_FONT = ["AFC Aldermaston A", "AFC Aldermaston B"]
# Pre-calculated spacing for headings and cup names
HEADING_FONT_TEMP = ImageFont.truetype(FONT_PATH, FONT_SIZE_HEADING)
CUP_NAME_FONT_TEMP = ImageFont.truetype(FONT_PATH, FONT_SIZE_CUP_NAME)
HEADING_SPACE = 20 + (HEADING_FONT_TEMP.getbbox("Cup")[3] - HEADING_FONT_TEMP.getbbox("Cup")[1]) + 20
CUP_NAME_SPACE = 5 + (CUP_NAME_FONT_TEMP.getbbox("Example Cup Name")[3] - CUP_NAME_FONT_TEMP.getbbox("Example Cup Name")[1]) + 10
print("✅ Configuration constants loaded.")
# --- Helper Functions ---
def get_logo(team_name: str, logos_folder: str) -> Image.Image:
    """
    Loads a team logo, handling specific variants and searching subfolders.
    Prioritizes exact matches, then "utd"/"united" and "&"/"and" variations, then generic.
    Falls back to a gray placeholder if generic logo is not found.
    """
    valid_extensions = ('.png', '.jpg', '.jpeg')
    team_name_lower = team_name.strip().lower()
    team_name_search_variants = [team_name_lower.replace(" ", "")]
    if "utd" in team_name_lower:
        team_name_search_variants.append(team_name_lower.replace("utd", "united").replace(" ", ""))
    if "united" in team_name_lower:
        team_name_search_variants.append(team_name_lower.replace("united", "utd").replace(" ", ""))
    if "&" in team_name_lower:
        team_name_search_variants.append(team_name_lower.replace("&", "and").replace(" ", ""))
    if "and" in team_name_lower:
        team_name_search_variants.append(team_name_lower.replace("and", "&").replace(" ", ""))
    team_name_search_variants = list(set(team_name_search_variants))
    for variant_key, logo_filename in SPECIAL_LOGO_MAPPING.items():
        if variant_key in team_name_lower:
            for subfolder in ['Current Teams', 'Old Teams', '']:
                search_path = os.path.join(logos_folder, subfolder, logo_filename)
                if os.path.exists(search_path):
                    try:
                        return Image.open(search_path).convert("RGBA")
                    except Exception as e:
                        print(f"Error loading mapped logo '{logo_filename}' for {team_name} from '{search_path}': {e}")
                        break
    for subfolder in ['Current Teams', 'Old Teams', '']:
        current_search_dir = os.path.join(logos_folder, subfolder)
        if not os.path.isdir(current_search_dir):
            continue
        for filename in os.listdir(current_search_dir):
            filename_clean_no_space = filename.strip().lower().replace(" ", "")
            if any(variant in filename_clean_no_space for variant in team_name_search_variants) and filename_clean_no_space.endswith(valid_extensions):
                logo_path = os.path.join(current_search_dir, filename)
                try:
                    return Image.open(logo_path).convert("RGBA")
                except Exception as e:
                    print(f"Error loading logo for {team_name} from '{logo_path}': {e}")
                    continue
    generic_logo_path = os.path.join(logos_folder, 'genericlogo.png')
    try:
        print(f"Warning: No specific logo found for {team_name}. Using generic logo.")
        return Image.open(generic_logo_path).convert("RGBA").resize((LOGO_WIDTH, LOGO_HEIGHT), Image.Resampling.LANCZOS)
    except Exception as e:
        print(f"Error loading generic logo: {e}. Using gray placeholder.")
        return Image.new("RGBA", (LOGO_WIDTH, LOGO_HEIGHT), (200, 200, 200, 255))
def parse_matches_from_file(file_path: str, division: str) -> list[tuple]:
    """
    Parses match data from a specified Excel sheet.
    Returns a list of tuples: (team1_name, team1_score, team2_score, team2_name, cup_name, penalty_score)
    """
    matches = []
    try:
        excel_data = pd.read_excel(file_path, sheet_name=division)
        print(f"Loaded {len(excel_data)} matches from {division} tab in XLSX file.")
        for _, row in excel_data.iterrows():
            team_1_name = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
            team_1_score = str(row.iloc[1]) if pd.notna(row.iloc[1]) else "-"
            team_2_score = str(row.iloc[2]) if pd.notna(row.iloc[2]) else "-"
            team_2_name = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""
            cup_name = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) and division.lower() == "cup" else None
            # Read penalty score from column 6 (index 5) - only for Cup division
            penalty_score = None
            if division.lower() == "cup":
                penalty_score = str(row.iloc[5]).strip() if pd.notna(row.iloc[5]) else None
                if penalty_score and not ("-" in penalty_score and len(penalty_score.split("-")) == 2):
                    print(f"Warning: Invalid penalty score format '{row.iloc[5]}' for match {team_1_name} vs {team_2_name}. Expected format like '4-3'.")
                    penalty_score = None
            if team_1_name and team_2_name:
                matches.append((team_1_name, team_1_score, team_2_score, team_2_name, cup_name, penalty_score))
    except Exception as e:
        print(f"Error reading the file for {division}: {e}")
    return matches
def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """
    Wraps text to fit within a maximum width, returning a list of lines.
    """
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
    """
    Calculates the total height of a block of wrapped text, including line spacing.
    """
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
def calculate_division_height(division_name: str, matches: list, is_first_division: bool = True, previous_was_cup: bool = False) -> int:
    """Calculate the height required for a division with accurate spacing"""
    # Heading space (always included)
    division_height = HEADING_SPACE
   
    # Extra spacing if this is not the first division
    if not is_first_division:
        division_height += 15 # Extra spacing between divisions
   
    last_cup_name = None
    for j, match in enumerate(matches):
        fixture_height = BOX_HEIGHT
       
        # Add spacing before this fixture (except for first fixture)
        if j > 0:
            fixture_height += FIXTURE_SPACING
       
        # Add cup name space if needed
        cup_name = match[4]
        if division_name.lower() == "cup" and cup_name and cup_name != last_cup_name:
            fixture_height += CUP_NAME_SPACE
            last_cup_name = cup_name
       
        division_height += fixture_height
   
    return division_height
# --- Main Graphic Generation Function ---
def create_match_graphic_with_heading(sections_to_draw: list[tuple], logos_folder: str, save_folder: str, part_number: int, template_path: str, current_date: datetime):
    """
    Creates a single graphic image for a set of matches with division headings and a smooth date circle.
    """
    try:
        template = Image.open(template_path).convert("RGBA")
        if template.size != (IMAGE_WIDTH, IMAGE_HEIGHT):
            raise ValueError(f"Template must be exactly {IMAGE_WIDTH}x{IMAGE_HEIGHT} pixels.")
    except Exception as e:
        print(f"Error loading template: {e}. Using transparent background instead.")
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
        penalty_score_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_PENALTY_SCORE)
        penalties_label_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_PENALTIES_LABEL)
    except IOError:
        print(f"Warning: Could not load font from {FONT_PATH}. Using default font.")
        font = score_font = heading_font = cup_name_font = small_font = penalty_score_font = penalties_label_font = ImageFont.load_default()
    # Draw date circle on a high-resolution temporary image
    high_res_size = DATE_CIRCLE_SIZE * HIGH_RES_SCALE
    circle_img = Image.new("RGBA", (high_res_size, high_res_size), (0, 0, 0, 0))
    circle_draw = ImageDraw.Draw(circle_img)
    day_text = current_date.strftime("%d")
    month_text = current_date.strftime("%B")
    year_text = current_date.strftime("%Y")
    circle_center_x = high_res_size // 2
    circle_center_y = high_res_size // 2
    circle_radius = (DATE_CIRCLE_SIZE * HIGH_RES_SCALE) // 2
    # Dynamic font size adjustment
    font_size = FONT_SIZE_DATE
    while font_size >= FONT_SIZE_DATE_MIN:
        date_font = ImageFont.truetype(FONT_PATH, int(font_size * HIGH_RES_SCALE))
        day_bbox = circle_draw.textbbox((0, 0), day_text, font=date_font)
        month_bbox = circle_draw.textbbox((0, 0), month_text, font=date_font)
        year_bbox = circle_draw.textbbox((0, 0), year_text, font=date_font)
        max_text_width = max(day_bbox[2] - day_bbox[0], month_bbox[2] - month_bbox[0], year_bbox[2] - year_bbox[0])
        total_text_height = (day_bbox[3] - day_bbox[1]) + (month_bbox[3] - month_bbox[1]) + (year_bbox[3] - year_bbox[1]) + 10 * HIGH_RES_SCALE
        if max_text_width <= DATE_TEXT_MAX_WIDTH * HIGH_RES_SCALE and total_text_height <= DATE_TEXT_MAX_HEIGHT * HIGH_RES_SCALE:
            break
        font_size -= 2 # Decrease font size and try again
    if font_size < FONT_SIZE_DATE_MIN:
        print(f"Warning: Font size reduced to {FONT_SIZE_DATE_MIN} for date text to fit in circle.")
    circle_draw.ellipse(
        [0, 0, high_res_size, high_res_size],
        fill=(255, 255, 255, 255),
        outline=(0, 0, 0, 255),
        width=DATE_CIRCLE_STROKE * HIGH_RES_SCALE
    )
    # Draw date text
    day_y = circle_center_y - total_text_height // 2
    month_y = day_y + (day_bbox[3] - day_bbox[1]) + 5 * HIGH_RES_SCALE
    year_y = month_y + (month_bbox[3] - month_bbox[1]) + 5 * HIGH_RES_SCALE
    circle_draw.text((circle_center_x - (day_bbox[2] - day_bbox[0]) // 2, day_y), day_text, fill=(0, 0, 0, 255), font=date_font)
    circle_draw.text((circle_center_x - (month_bbox[2] - month_bbox[0]) // 2, month_y), month_text, fill=(0, 0, 0, 255), font=date_font)
    circle_draw.text((circle_center_x - (year_bbox[2] - year_bbox[0]) // 2, year_y), year_text, fill=(0, 0, 0, 255), font=date_font)
    # Resize back to original size
    circle_img = circle_img.resize((DATE_CIRCLE_SIZE, DATE_CIRCLE_SIZE), Image.Resampling.LANCZOS)
    img.paste(circle_img, (DATE_CIRCLE_X, DATE_CIRCLE_Y), circle_img)
    y_offset = CONTENT_START_Y
    max_content_height = 0
    visual_y_offset_correction = VISUAL_Y_OFFSET_CORRECTION
    for division_name, matches in sections_to_draw:
        heading = division_name
        heading_bbox = d.textbbox((0, 0), heading, font=heading_font)
        heading_width = heading_bbox[2] - heading_bbox[0]
        heading_height = heading_bbox[3] - heading_bbox[1]
        heading_x = (IMAGE_WIDTH - heading_width) // 2
        d.text((heading_x, y_offset + 20), heading, fill=(255, 255, 255), font=heading_font)
        y_offset += 20 + heading_height + 20
        last_cup_name = None
        for match in matches:
            team_1_name, team_1_score, team_2_score, team_2_name, cup_name, penalty_score = match
            if division_name.lower() == "cup" and cup_name and cup_name != last_cup_name:
                cup_name_bbox = d.textbbox((0, 0), cup_name, font=cup_name_font)
                cup_name_height = cup_name_bbox[3] - cup_name_bbox[1]
                cup_name_x = LEFT_PADDING
                cup_name_y = y_offset + 5
                d.text((cup_name_x, cup_name_y), cup_name, fill=(255, 255, 0), font=cup_name_font)
                y_offset = cup_name_y + cup_name_height + 10
                last_cup_name = cup_name
            else:
                y_offset += FIXTURE_SPACING
            logo_1 = get_logo(team_1_name, logos_folder)
            logo_2 = get_logo(team_2_name, logos_folder)
            if not logo_1 or not logo_2:
                print(f"Error loading logos for {team_1_name} or {team_2_name}. Skipping match.")
                continue
            logo_1 = logo_1.resize((LOGO_WIDTH, LOGO_HEIGHT))
            logo_2 = logo_2.resize((LOGO_WIDTH, LOGO_HEIGHT))
            logo_1_x = LEFT_PADDING + 1
            img.paste(logo_1, (logo_1_x, int(y_offset) + 1), logo_1)
            team_1_box_x = logo_1_x + LOGO_WIDTH + 2
            team_1_box_y = y_offset
            d.rectangle([team_1_box_x, team_1_box_y, team_1_box_x + TEAM_BOX_WIDTH, team_1_box_y + BOX_HEIGHT - 1], fill=(0, 0, 0, 180))
            team_1_font_to_use = small_font if team_1_name in TEAMS_FOR_SMALLER_FONT else font
            team_1_lines = wrap_text(team_1_name, team_1_font_to_use, TEAM_BOX_WIDTH - 20, d)
            team_1_total_text_block_height = get_wrapped_text_block_height(team_1_lines, team_1_font_to_use, LINE_SPACING, d)
            team_1_start_y_text = team_1_box_y + (BOX_HEIGHT - team_1_total_text_block_height) // 2 + visual_y_offset_correction
            current_line_y_team1 = team_1_start_y_text
            for line in team_1_lines:
                line_bbox = d.textbbox((0, 0), line, font=team_1_font_to_use)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = team_1_box_x + (TEAM_BOX_WIDTH - line_width) // 2
                d.text((line_x, current_line_y_team1), line, fill=(255, 255, 255), font=team_1_font_to_use)
                current_line_y_team1 += (line_bbox[3] - line_bbox[1]) + LINE_SPACING
            # Score - Enhanced for penalty display
            score_box_x = team_1_box_x + TEAM_BOX_WIDTH + 5
            score_box_y = y_offset
            d.rectangle([score_box_x, score_box_y, score_box_x + SCORE_BOX_WIDTH, score_box_y + BOX_HEIGHT - 1], fill=(0, 0, 0, 180))
            
            # Regular score text
            regular_score_text = f"{team_1_score} - {team_2_score}" if team_1_score and team_2_score else (team_1_score if team_1_score else team_2_score if team_2_score else "- -")
            regular_score_bbox = d.textbbox((0, 0), regular_score_text, font=score_font)
            regular_score_text_x = score_box_x + (SCORE_BOX_WIDTH - (regular_score_bbox[2] - regular_score_bbox[0])) // 2
            regular_score_text_y = score_box_y + 8  # Moved up more from center (was 15)
            
            # Check if this is a penalty match (only for Cup division)
            is_penalty_match = division_name.lower() == "cup" and penalty_score
            
            if is_penalty_match:
                # Draw regular score higher up
                d.text((regular_score_text_x, regular_score_text_y), regular_score_text, fill=(255, 255, 255), font=score_font)
                
                # Draw "PENALTIES" label with more gap
                penalties_label = "PENALTIES"
                penalties_bbox = d.textbbox((0, 0), penalties_label, font=penalties_label_font)
                penalties_text_x = score_box_x + (SCORE_BOX_WIDTH - (penalties_bbox[2] - penalties_bbox[0])) // 2
                penalties_text_y = regular_score_text_y + regular_score_bbox[3] - regular_score_bbox[1] + 12  # Increased gap (was 5)
                d.text((penalties_text_x, penalties_text_y), penalties_label, fill=(255, 255, 0), font=penalties_label_font)  # Yellow for "PENALTIES"
                
                # Draw penalty score with more gap
                penalty_score_text = penalty_score
                penalty_score_bbox = d.textbbox((0, 0), penalty_score_text, font=penalty_score_font)
                penalty_score_text_x = score_box_x + (SCORE_BOX_WIDTH - (penalty_score_bbox[2] - penalty_score_bbox[0])) // 2
                penalty_score_text_y = penalties_text_y + penalties_bbox[3] - penalties_bbox[1] + 8  # Increased gap (was 2)
                d.text((penalty_score_text_x, penalty_score_text_y), penalty_score_text, fill=(255, 255, 255), font=penalty_score_font)
            else:
                # Normal score display (centered)
                score_text_x = score_box_x + (SCORE_BOX_WIDTH - (regular_score_bbox[2] - regular_score_bbox[0])) // 2
                score_text_y = score_box_y + (BOX_HEIGHT - (regular_score_bbox[3] - regular_score_bbox[1])) // 2
                d.text((score_text_x, score_text_y), regular_score_text, fill=(255, 255, 255), font=score_font)
            
            team_2_box_x = score_box_x + SCORE_BOX_WIDTH + 5
            team_2_box_y = y_offset
            d.rectangle([team_2_box_x, team_2_box_y, team_2_box_x + TEAM_BOX_WIDTH, team_2_box_y + BOX_HEIGHT - 1], fill=(0, 0, 0, 180))
            team_2_font_to_use = small_font if team_2_name in TEAMS_FOR_SMALLER_FONT else font
            team_2_lines = wrap_text(team_2_name, team_2_font_to_use, TEAM_BOX_WIDTH - 20, d)
            team_2_total_text_block_height = get_wrapped_text_block_height(team_2_lines, team_2_font_to_use, LINE_SPACING, d)
            team_2_start_y_text = team_2_box_y + (BOX_HEIGHT - team_2_total_text_block_height) // 2 + visual_y_offset_correction
            current_line_y_team2 = team_2_start_y_text
            for line in team_2_lines:
                line_bbox = d.textbbox((0, 0), line, font=team_2_font_to_use)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = team_2_box_x + (TEAM_BOX_WIDTH - line_width) // 2
                d.text((line_x, current_line_y_team2), line, fill=(255, 255, 255), font=team_2_font_to_use)
                current_line_y_team2 += (line_bbox[3] - line_bbox[1]) + LINE_SPACING
            logo_2_x = team_2_box_x + TEAM_BOX_WIDTH + 2
            img.paste(logo_2, (logo_2_x, int(y_offset) + 1), logo_2)
            y_offset += BOX_HEIGHT
            max_content_height = max(max_content_height, y_offset - CONTENT_START_Y)
        if max_content_height > CONTENT_HEIGHT_LIMIT:
            max_content_height = CONTENT_HEIGHT_LIMIT
    final_img = Image.new("RGBA", (IMAGE_WIDTH, IMAGE_HEIGHT), (0, 0, 0, 0))
    final_img.paste(img, (0, 0))
    content_img = img.crop((0, int(CONTENT_START_Y), IMAGE_WIDTH, int(CONTENT_START_Y + CONTENT_HEIGHT_LIMIT)))
    final_img.paste(content_img, (0, int(CONTENT_START_Y)))
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file_path = os.path.join(save_folder, f"Results_Part{part_number}_{current_time}.png")
    final_img.save(output_file_path)
    print(f"Graphic saved to: {output_file_path}")
    final_img.show()
# --- Updated Results Splitting Logic with Conservative Height Limits ---
def generate_results_graphics(file_path: str, logos_folder: str, save_folder: str, template_path: str):
    """
    Main function with robust logic for splitting content across multiple graphics.
    Uses conservative height limits to prevent footer overflow.
    """
    # Read date from Excel 'Date' sheet
    try:
        date_df = pd.read_excel(file_path, sheet_name='Date')
        if not date_df.empty and 'Date' in date_df.columns:
            date_str = str(date_df['Date'].iloc[0]).strip()
            # Try multiple date formats
            date_formats = ['%d/%m/%Y', '%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%d-%m-%Y']
            current_date = None
            for fmt in date_formats:
                try:
                    current_date = pd.to_datetime(date_str, format=fmt, errors='raise')
                    print(f"Date {date_str} read from 'Date' sheet in {file_path} using format {fmt}")
                    break
                except ValueError:
                    continue
            if current_date is None:
                # Try parsing without a specific format (handles Excel timestamps)
                current_date = pd.to_datetime(date_str, errors='coerce')
                if pd.isna(current_date):
                    raise ValueError(f"Invalid date format: {date_str}")
                print(f"Date {date_str} parsed as timestamp from 'Date' sheet in {file_path}")
        else:
            print(f"Error: 'Date' sheet empty or missing 'Date' column in {file_path}. Using current date.")
            current_date = datetime.now()
    except Exception as e:
        print(f"Error reading 'Date' sheet from {file_path}: {e}. Using current date.")
        current_date = datetime.now()
   
    divisions = ["Cup", "Division 1", "Division 2", "Division 3", "Division 4"]
    all_divisions_data = [{'division': div, 'matches': parse_matches_from_file(file_path, div), 'idx': 0} for div in divisions]
  
    remaining_divisions = [d for d in all_divisions_data if d['matches']]
    part_number = 1
  
    # Use a more conservative height limit to prevent footer overlap
    SAFE_CONTENT_HEIGHT_LIMIT = 960 # Reduced from 1050 to leave buffer
   
    while remaining_divisions:
        sections_to_draw = []
        current_height = 0
        next_graphic_divisions = []
       
        print(f"\n--- Processing graphic {part_number} ---")
        print(f"Remaining divisions: {[d['division'] for d in remaining_divisions]}")
       
        for div_data in remaining_divisions:
            division_name = div_data['division']
            matches = div_data['matches']
           
            # Calculate height for this division based on current state
            is_first = len(sections_to_draw) == 0
            division_height = calculate_division_height(division_name, matches, is_first)
           
            print(f"{division_name}: {len(matches)} matches, height needed: {division_height}px")
           
            # Special case: If we have Div 1 + Div 2 already and this is Div 4, be extra conservative
            if (len(sections_to_draw) == 2 and
                sections_to_draw[0][0] == "Division 1" and
                sections_to_draw[1][0] == "Division 2" and
                division_name == "Division 4"):
               
                # Use even more conservative limit for this specific case
                CONSERVATIVE_LIMIT = 850
                total_height_with_div4 = current_height + division_height
                print(f" -> Div 1+2+4 total height would be: {total_height_with_div4}px (using conservative limit: {CONSERVATIVE_LIMIT}px)")
               
                if total_height_with_div4 > CONSERVATIVE_LIMIT:
                    print(f" -> Div 4 ({division_height}px) won't fit with Div 1+2 (current: {current_height}px). Moving to next graphic.")
                    next_graphic_divisions.append(div_data)
                    continue
           
            # Standard fit check with safe limit
            total_height = current_height + division_height
            if total_height <= SAFE_CONTENT_HEIGHT_LIMIT or is_first:
                print(f" -> Adding {division_name} to current graphic")
                sections_to_draw.append((division_name, matches))
                current_height = total_height
            else:
                print(f" -> {division_name} ({division_height}px) doesn't fit (current: {current_height}px, safe limit: {SAFE_CONTENT_HEIGHT_LIMIT}px). Moving to next graphic.")
                next_graphic_divisions.append(div_data)
       
        if sections_to_draw:
            print(f"Final sections for graphic {part_number}: {[section[0] for section in sections_to_draw]}")
            print(f"Total height used: {current_height}px / {SAFE_CONTENT_HEIGHT_LIMIT}px")
            create_match_graphic_with_heading(sections_to_draw, logos_folder, save_folder, part_number, template_path, current_date)
            part_number += 1
       
        remaining_divisions = next_graphic_divisions
       
        if not next_graphic_divisions and sections_to_draw:
            break
        if not sections_to_draw and remaining_divisions:
            print("Error: Remaining divisions are too large to fit on a single graphic.")
            break
   
    print(f"\n✅ Completed generating {part_number-1} graphic(s)")
print("✅ All functions defined. Attempting to run main function.")
# Example usage
if __name__ == "__main__":
    generate_results_graphics(RESULTS_FILE_PATH, LOGOS_FOLDER, SAVE_FOLDER, RESULTS_TEMPLATE_PATH)
