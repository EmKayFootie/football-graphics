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
TEMPLATE_PATH = os.path.join(TEMPLATES_FOLDER, "results_template.png")
FONT_PATH = os.path.join(BASE_DIR, "BebasNeue Regular.ttf") 

# Image Dimensions and Layout (These are critical for height calculation)
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1350
CONTENT_START_Y = 251.97
# Using the SAFE_CONTENT_HEIGHT_LIMIT from the Fixtures logic for consistent packing
# Note: The limit was 950px in the fixtures, but your script error messages show 1050px 
# and 960px. I will default to 950px for safety, but make it easy to adjust.
SAFE_CONTENT_HEIGHT_LIMIT = 950 # Conservative height limit from fixtures.py
# The error message implied limits of 1050px/960px, but 950px is the safest from the original config
# We'll stick to 950px unless you tell me otherwise, as this controls the packing.

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
# ... (rest of layout constants)

# Font Sizes (Adjusted to what is typically needed for Results)
FONT_SIZE_NORMAL = 65
FONT_SIZE_SCORE = 75 # Larger for results score
FONT_SIZE_HEADING = 64
FONT_SIZE_CUP_NAME = 39
FONT_SIZE_SMALL_TEAM_NAME = 50

VISUAL_Y_OFFSET_CORRECTION = -5

# Special Team Logo Mappings
SPECIAL_LOGO_MAPPING = {
    "afc aldermaston a": "AFC Aldermaston.png",
    "afc aldermaston b": "AFC Aldermaston.png",
}
TEAMS_FOR_SMALLER_FONT = ["AFC Aldermaston A", "AFC Aldermaston B"]

# --- Pre-calculate spacing based on font (Copied from fixtures for accuracy) ---
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

# --- Helper Functions (Stubs for the logic) ---

# NOTE: The actual implementations of get_logo, parse_matches_from_file, 
# wrap_text, get_wrapped_text_block_height, and create_match_graphic_with_heading 
# from your previous successful runs must be present here. 
# I will define the critical ones for *height calculation* and use stubs for the rest.

def get_logo(team_name: str, logos_folder: str) -> Image.Image:
    # This is a stub. Use the full implementation from the fixtures script.
    # It must return a PIL Image object.
    generic_logo_path = os.path.join(logos_folder, 'genericlogo.png')
    try:
        if os.path.exists(generic_logo_path):
             return Image.open(generic_logo_path).convert("RGBA").resize((LOGO_WIDTH, LOGO_HEIGHT), Image.LANCZOS)
    except Exception:
        pass
    return Image.new("RGBA", (LOGO_WIDTH, LOGO_HEIGHT), (200, 200, 200, 255))

def parse_matches_from_file(file_path: str, division: str) -> list[tuple]:
    """Reads matches from the specified Excel sheet (stub)."""
    matches = []
    try:
        excel_data = pd.read_excel(file_path, sheet_name=division)
        for _, row in excel_data.iterrows():
            team_1_name = str(row['Team 1 name']).strip() if pd.notna(row['Team 1 name']) else ""
            team_1_score = str(row['Team 1 score']) if pd.notna(row['Team 1 score']) else "-"
            team_2_score = str(row['Team 2 score']) if pd.notna(row['Team 2 score']) else "-"
            team_2_name = str(row['Team 2 name']).strip() if pd.notna(row['Team 2 name']) else ""
            cup_name = None
            if 'Cup name' in row and pd.notna(row['Cup name']):
                cup_name = str(row['Cup name']).strip()
            if team_1_name and team_2_name:
                # Format: (team_1_name, team_1_score, team_2_score, team_2_name, cup_name)
                matches.append((team_1_name, team_1_score, team_2_score, team_2_name, cup_name))
    except Exception as e:
        # print(f"Could not load sheet {division}: {e}")
        pass
    return matches

# Stubs for text drawing (not needed for height calculation, but required for the full script)
def wrap_text(*args): return ["Text"]
def get_wrapped_text_block_height(*args): return 50

# --- CRITICAL HEIGHT CALCULATION FUNCTION (Copied/Modified from fixtures) ---
def calculate_division_height(division_name: str, matches: list, is_first_division: bool = True) -> int:
    """Calculate the height required for a division or cup group with accurate spacing"""
    
    # 1. Height of the main heading (Division X or Cup)
    total_height = HEADING_SPACE
    
    # 2. Add spacing before the first division/section if it's not the first one on the graphic
    if not is_first_division:
        total_height += FIXTURE_SPACING # 15px spacing between sections

    last_cup_name = None
    
    for j, match in enumerate(matches):
        # Base height for the match result box
        match_height = BOX_HEIGHT
        
        # Space for Cup Name header
        # The cup name is the 5th element in the tuple (index 4)
        cup_name = match[4]
        if division_name.lower().startswith("cup") and cup_name and cup_name != last_cup_name:
            match_height += CUP_NAME_SPACE
            last_cup_name = cup_name
        
        # Space *before* the fixture/result.
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


def create_match_graphic_with_heading(sections_to_draw: list[tuple], logos_folder: str, save_folder: str, part_number: int, template_path: str, current_date: datetime):
    """
    Stub for the graphic generation function.
    You must use the full, correct implementation from the Fixtures script here, 
    but with score-drawing logic instead of 'vs' text.
    """
    # Load Fonts (Using stubs here for brevity, use your full implementation)
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE_NORMAL)
        score_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_SCORE)
        heading_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_HEADING)
        cup_name_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_CUP_NAME)
        small_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_SMALL_TEAM_NAME)
    except IOError:
        font = score_font = heading_font = cup_name_font = small_font = ImageFont.load_default()

    # Create dummy image and draw object for text metrics (if needed)
    img = Image.new("RGBA", (IMAGE_WIDTH, IMAGE_HEIGHT), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # --- Draw Date Circle (Stub) ---
    # (Full implementation is needed here)

    # --- Draw Matches ---
    y_offset = CONTENT_START_Y
    is_first_division_of_graphic = True 
    
    for division_name, matches in sections_to_draw:
        
        # 1. Add extra spacing
        if not is_first_division_of_graphic:
            y_offset += FIXTURE_SPACING

        # 2. Draw Division/Cup Heading
        heading = "Cup Results" if division_name.lower().startswith("cup") else f"{division_name} Results"
        heading_bbox = d.textbbox((0, 0), heading, font=heading_font)
        heading_width = heading_bbox[2] - heading_bbox[0]
        heading_x = (IMAGE_WIDTH - heading_width) // 2
        d.text((heading_x, y_offset + 20), heading, fill=(255, 255, 255), font=heading_font)
        y_offset += HEADING_SPACE 
        
        last_cup_name = None
        is_first_fixture_in_section = True
        
        for match in matches:
            team_1_name, score_1, score_2, team_2_name, cup_name = match
            
            # 3. Draw Cup Name (if applicable and different from the last one)
            if division_name.lower().startswith("cup") and cup_name and cup_name != last_cup_name:
                cup_name_x = LEFT_PADDING
                d.text((cup_name_x, y_offset + 5), cup_name, fill=(255, 255, 0), font=cup_name_font)
                y_offset += CUP_NAME_SPACE 
                last_cup_name = cup_name
                is_first_fixture_in_section = True

            # 4. Add spacing between fixtures
            if not is_first_fixture_in_section:
                y_offset += FIXTURE_SPACING

            # 5. Draw Fixture Box and Content (Simplified for this example)
            
            # --- Draw Score Box with Actual Scores ---
            # Box structure is the same: Logo1 | Team1 | Score | Team2 | Logo2
            
            # This is where your drawing logic will go, replacing 'vs' with 'Score1 - Score2'
            
            # Example Score Box Drawing (CRITICAL CHANGE)
            vs_box_x = LEFT_PADDING + LOGO_WIDTH + TEAM_BOX_WIDTH + 2 + 5 
            vs_box_y = y_offset
            
            # Draw score background box
            d.rectangle([vs_box_x, vs_box_y, vs_box_x + SCORE_BOX_WIDTH, vs_box_y + BOX_HEIGHT - 1], fill=(100, 100, 100, 200)) # Changed to a darker color for results
            
            # Format and draw the score text
            score_text = f"{score_1} - {score_2}"
            score_bbox = d.textbbox((0, 0), score_text, font=score_font)
            score_text_x = vs_box_x + (SCORE_BOX_WIDTH - (score_bbox[2] - score_bbox[0])) // 2
            score_text_y = vs_box_y + (BOX_HEIGHT - (score_bbox[3] - score_bbox[1])) // 2 + VISUAL_Y_OFFSET_CORRECTION
            d.text((score_text_x, score_text_y), score_text, fill=(255, 255, 255), font=score_font)

            # ... (Rest of team/logo drawing logic is the same)
            
            # Advance Y offset by the fixture height
            y_offset += BOX_HEIGHT
            
            is_first_fixture_in_section = False
        
        is_first_division_of_graphic = False 

    # Final Image Saving (Full implementation is needed here)
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file_path = os.path.join(save_folder, f"Results_Part{part_number}_{current_time}.png")
    # img.save(output_file_path) # Uncomment in full script
    print(f"Graphic saved to: {output_file_path} (Stub - Actual save relies on full implementation)")


# --- MAIN LOGIC (Copied/Modified from fixtures) ---
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
        
        # Sort (Trophy Cup first, then by name)
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
    
    # 3a. Process cup matches first
    remaining_cup_divisions = cup_divisions
    part_number = 1
    
    trophy_cup_name = "Cup - Hampshire Trophy Cup"
    
    print("\n--- Starting Graphic Generation ---")
    
    # 3a-1. Handle remaining_cup_divisions
    while remaining_cup_divisions:
        sections_to_draw = []
        current_height = 0
        next_graphic_divisions = []
        is_first_division_of_graphic = True

        print(f"\n--- Processing graphic {part_number} ---")
        print(f"Remaining divisions (Cup): {[d['division'] for d in remaining_cup_divisions]}")
        
        i = 0
        while i < len(remaining_cup_divisions):
            div_data = remaining_cup_divisions[i]
            division_name = div_data['division']
            matches = div_data['matches']
            
            current_matches = matches
            remaining_matches = []
            
            # --- Determine which matches to include based on space and specific rules ---
            
            will_add_to_current = False
            
            if division_name == trophy_cup_name:
                # Rule: Include all Trophy Cup matches if space allows.
                temp_height = calculate_division_height("Cup", current_matches, is_first_division_of_graphic)
                if current_height + temp_height <= SAFE_CONTENT_HEIGHT_LIMIT or not sections_to_draw:
                    will_add_to_current = True
                else:
                    print(f"{division_name} ({temp_height}px) does not fit (Limit: {SAFE_CONTENT_HEIGHT_LIMIT}px).")
            
            elif division_name == "Cup - Hampshire Vase Cup":
                # Rule: Max 2 Vase Cup matches if Trophy Cup is on the *current* graphic (assuming part 1), otherwise up to 6
                trophy_cup_added_to_current_graphic = any(s[0] == "Cup" and s[1][0][4] == "Hampshire Trophy Cup" for s in sections_to_draw)
                
                max_matches = 2 if trophy_cup_added_to_current_graphic and part_number == 1 else 6
                
                if len(matches) > max_matches:
                    current_matches = matches[:max_matches]
                    remaining_matches = matches[max_matches:]
                
                temp_height = calculate_division_height("Cup", current_matches, is_first_division_of_graphic)
                
                if current_height + temp_height <= SAFE_CONTENT_HEIGHT_LIMIT or not sections_to_draw:
                    will_add_to_current = True
                else:
                    print(f"{division_name} ({temp_height}px for {len(current_matches)} matches) does not fit.")
            
            else:
                # Other cup types (treat as a single block)
                temp_height = calculate_division_height("Cup", current_matches, is_first_division_of_graphic)
                if current_height + temp_height <= SAFE_CONTENT_HEIGHT_LIMIT or not sections_to_draw:
                    will_add_to_current = True
                else:
                    # If this single block of other cup matches doesn't fit, it must be too big
                    # for the graphic, so we split it if possible.
                    if temp_height > SAFE_CONTENT_HEIGHT_LIMIT:
                        print(f"Warning: Single Cup Group '{division_name}' ({temp_height}px) is too large. Attempting to split.")
                        
                        # Find the max number of matches that *will* fit
                        max_fit_matches = 0
                        
                        # Start checking from 1 match
                        for k in range(1, len(matches) + 1):
                            test_matches = matches[:k]
                            test_height = calculate_division_height("Cup", test_matches, is_first_division_of_graphic)
                            if current_height + test_height <= SAFE_CONTENT_HEIGHT_LIMIT or (not sections_to_draw and test_height <= SAFE_CONTENT_HEIGHT_LIMIT):
                                max_fit_matches = k
                            else:
                                break
                        
                        if max_fit_matches > 0:
                            current_matches = matches[:max_fit_matches]
                            remaining_matches = matches[max_fit_matches:]
                            temp_height = calculate_division_height("Cup", current_matches, is_first_division_of_graphic)
                            will_add_to_current = True
                        else:
                            print(f"CRITICAL: First match in {division_name} is too big. Skipping/Error.")
                    # If it didn't fit, and we didn't split it, it stays False and moves to next graphic.
            
            # --- Execute inclusion or deferral ---

            if will_add_to_current and current_matches:
                sections_to_draw.append(("Cup", current_matches))
                current_height += temp_height
                is_first_division_of_graphic = False
                print(f" -> Added {division_name} ({len(current_matches)} matches). Total height: {current_height}px.")

                if remaining_matches:
                     next_graphic_divisions.append({
                        'division': division_name,
                        'matches': remaining_matches,
                        'original_div': "Cup"
                    })
                i += 1
            elif not will_add_to_current and sections_to_draw:
                # If it didn't fit (and it's not the first division), move the whole block to the next graphic
                next_graphic_divisions.append(div_data)
                i += 1
            elif not will_add_to_current and not sections_to_draw:
                 # It's the first division on the graphic and it's too big, and we couldn't split it (or it's an indivisible block that's too big)
                print(f"CRITICAL: {division_name} ({len(matches)} matches, {temp_height}px) is too tall to fit on a single graphic ({SAFE_CONTENT_HEIGHT_LIMIT}px). Skipping/Error.")
                i += 1 # Move past the un-packable division
                
        remaining_cup_divisions = next_graphic_divisions
        
        # 3b. Process league matches (Standard packing logic - ONLY if no cup matches remain)
        if not remaining_cup_divisions:
            league_divisions.extend(remaining_league_divisions) # Add back any unadded league matches
            remaining_league_divisions = [] # Clear the tracker
            
            i = 0
            while i < len(league_divisions):
                div_data = league_divisions[i]
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
                    # An entire league division is too big. This should not happen if data is sane.
                    print(f"CRITICAL: {division_name} ({len(matches)} matches, {division_height}px) is too tall to fit on a single graphic ({SAFE_CONTENT_HEIGHT_LIMIT}px). Skipping/Error.")
                    i += 1
                else:
                    # Move the rest of the league divisions to the next graphic's processing list
                    remaining_league_divisions.extend(league_divisions[i:])
                    break # Stop processing league divisions for this graphic

        # --- Post-loop graphic generation and cleanup ---

        if sections_to_draw:
            print(f"Final sections for graphic {part_number}: {[s[0] for s in sections_to_draw]}")
            print(f"Total height used: {current_height}px / {SAFE_CONTENT_HEIGHT_LIMIT}px")
            # This must use your full implementation of the result graphic function
            create_match_graphic_with_heading(sections_to_draw, logos_folder, save_folder, part_number, TEMPLATE_PATH, current_date)
            part_number += 1
        
        # Error check for infinite loop
        if not sections_to_draw and (remaining_cup_divisions or remaining_league_divisions):
             print("\nError: Remaining divisions are too large to fit on a single graphic, even the first one. Stopping processing.")
             break

    print(f"\n✅ Completed generating {part_number-1} graphic(s)")
    print("Results graphics generated successfully!")


# --- Execution ---
print("✅ All functions defined. Attempting to run main function.")
if __name__ == "__main__":
    generate_results_graphics(RESULTS_FILE_PATH, LOGOS_FOLDER, SAVE_FOLDER, TEMPLATE_PATH)
