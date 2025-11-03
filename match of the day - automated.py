from PIL import Image, ImageDraw, ImageFont, ImageColor
import os
from datetime import datetime
import pandas as pd # Import pandas for Excel reading

# --- Configuration Constants ---
# Paths
LOGOS_FOLDER = "Logos"
SAVE_FOLDER = "Graphics"
TEMPLATES_FOLDER = "Templates"
MATCH_OF_THE_DAY_TEMPLATE_PATH = os.path.join(TEMPLATES_FOLDER, "match_of_the_day_template.png")
# New template for results with many scorers (no footer)
MATCH_OF_THE_DAY_RESULT_TEMPLATE_NO_FOOTER_PATH = os.path.join(TEMPLATES_FOLDER, "match_of_the_day_result_template.png")
FONT_PATH = "BebasKai.ttf"  # In project root
MATCH_DATA_EXCEL_PATH = "match of the day.xlsx"

# Image Dimensions
IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1350

# Font Sizes
FONT_SIZE_DETAILS = 56       # For date, time, location, division
FONT_SIZE_FINAL_SCORE = 156  # For "FINAL SCORE"
FONT_SIZE_TEAM_NAME = 75     # For team names
FONT_SIZE_VS_SCORE = 110     # For "VS" or actual score (e.g., "6 - 0")
FONT_SIZE_SCORERS = 35       # Adjusted: Smaller font size for goalscorers to allow more text per line

# Colors
TEXT_COLOR = ImageColor.getrgb("#46474a")
GREEN_COLOR = ImageColor.getrgb("#4ba04f") # Updated green for FINAL SCORE
WHITE_COLOR = (119, 119, 119) # For scorers text

# Element Dimensions and Spacing
LOGO_DISPLAY_SIZE = (340, 340) # Size for team logos on the graphic
MAX_TEAM_NAME_WIDTH = 340      # Max width for wrapped team names (matches logo width)
TEAM_NAME_INTERNAL_PADDING = 20 # Padding inside team name wrapping area
TEAM_NAME_LINE_SPACING = 68    # Adjusted leading for team names (91 * 0.75 ≈ 68px from original comment) - This is used for vertical spacing between lines
SCORER_LINE_SPACING = 2        # Adjusted: Line spacing for wrapped scorer text, made much smaller for tighter fit
SCORER_TEXT_VERTICAL_OFFSET = 20 # Vertical offset for scorer text below team name

# Vertical Y-Positions (relative to the top of the 1350px image)
# These are the top-most Y-coordinates for each section.
Y_POS_DETAILS_OR_FINAL_SCORE = 344.25 # Y for "SUNDAY 27 APR | 10:30 | ..." or "FINAL SCORE"
Y_POS_DIVISION_BAR = 444              # Y for the division name bar
Y_POS_LOGOS = 520                     # Y for the top of the team logos
Y_POS_VS_OR_SCORE = 680.5             # Y for "VS" or the match score
Y_POS_TEAM_NAMES = 884.75             # Y for the top of the team names (first line)

# Horizontal X-Positions (fixed for elements)
HOME_TEAM_LOGO_X = 66
AWAY_TEAM_LOGO_X = 677

# Division Bar Styling
DIVISION_BAR_PADDING_X = 20
DIVISION_BAR_PADDING_Y = 10
DIVISION_BAR_OUTLINE_COLOR = "black"
DIVISION_BAR_OUTLINE_WIDTH = 1
DIVISION_TEXT_VERTICAL_ADJUSTMENT = -12 # Small upward adjustment for division text within its bar
DIVISION_BAR_RESULT_Y_OFFSET = 5 # Adjust this value to move the division bar down (positive) or up (negative) for result graphics

# Adjust this value (negative moves text up, positive moves text down)
# to fine-tune the vertical position of the "FINAL SCORE" text.
FINAL_SCORE_VERTICAL_ADJUSTMENT = -40 # Moved down by 10px from -50 to -40

# Special Team Logo Mappings (e.g., variants pointing to a single logo file)
SPECIAL_LOGO_MAPPING = {
    "afc aldermaston a": "AFC Aldermaston.png",
    "afc aldermaston b": "AFC Aldermaston.png",
    "eversley & california sunday": "Eversley & California.png",
}

# --- Helper Functions (Copied and improved from previous Canvas) ---

def get_logo(team_name: str, logos_folder: str) -> Image.Image:
    """
    Loads a team logo, handling specific variants and searching subfolders.
    Prioritizes exact matches, then "utd"/"united" and "&"/"and" variations, then generic.
    Falls back to a gray placeholder if generic logo is not found.
    """
    valid_extensions = ('.png', '.jpg', '.jpeg')
    team_name_lower = team_name.strip().lower()

    # Create search variations
    team_name_search_variants = [team_name_lower.replace(" ", "")]

    # Handle "utd" and "united" variations
    if "utd" in team_name_lower:
        team_name_search_variants.append(team_name_lower.replace("utd", "united").replace(" ", ""))
    if "united" in team_name_lower:
        team_name_search_variants.append(team_name_lower.replace("united", "utd").replace(" ", ""))

    # Handle "&" and "and" variations
    if "&" in team_name_lower:
        team_name_search_variants.append(team_name_lower.replace("&", "and").replace(" ", ""))
    if "and" in team_name_lower:
        team_name_search_variants.append(team_name_lower.replace("and", "&").replace(" ", ""))

    # Ensure unique variants
    team_name_search_variants = list(set(team_name_search_variants))

    # 1. Check for special logo mappings first (e.g., AFC Aldermaston A/B, Eversley & California Sunday)
    for variant_key, logo_filename in SPECIAL_LOGO_MAPPING.items():
        if variant_key in team_name_lower:
            for subfolder in ['Current Teams', 'Old Teams', '']: # Search subfolders and root
                search_path = os.path.join(logos_folder, subfolder, logo_filename)
                if os.path.exists(search_path):
                    try:
                        return Image.open(search_path).convert("RGBA")
                    except Exception as e:
                        print(f"Error loading mapped logo '{logo_filename}' for {team_name} from '{search_path}': {e}")
                        break # Stop trying this mapped logo if it fails

    # 2. General search for logo files based on name variations
    for subfolder in ['Current Teams', 'Old Teams', '']: # Search subfolders and root
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
                    continue # Try next file in the same directory

    # 3. Use generic logo as a last resort
    generic_logo_path = os.path.join(logos_folder, 'genericlogo.png')
    try:
        print(f"Warning: No specific logo found for {team_name}. Using generic logo.")
        # Ensure generic logo is resized to the expected size for MOTD
        return Image.open(generic_logo_path).convert("RGBA").resize(LOGO_DISPLAY_SIZE, Image.Resampling.LANCZOS)
    except Exception as e:
        print(f"Error loading generic logo: {e}. Using gray placeholder.")
        return Image.new("RGBA", LOGO_DISPLAY_SIZE, (200, 200, 200, 255))


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
        elif not current_line and word_width <= max_width: # First word in a line
            current_line.append(word)
            current_width += word_width
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

# Function to create a silver gradient
def create_silver_gradient(width: int, height: int) -> Image.Image:
    """
    Creates a silver linear gradient image.
    """
    gradient = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(gradient)
    for x in range(width):
        # Linear gradient from light silver (#D3D3D3) to darker silver (#A9A9A9)
        r = int(211 - (x / width) * (211 - 169))
        g = int(211 - (x / width) * (211 - 169))
        b = int(211 - (x / width) * (211 - 169))
        draw.line((x, 0, x, height), fill=(r, g, b))
    return gradient

# --- New function to read match data from Excel ---
def read_match_data_from_excel(file_path: str) -> dict:
    """
    Reads match data from a two-column Excel spreadsheet.
    Column A contains labels, Column B contains values.
    Handles specific formatting for scorer lists.
    """
    match_data = {}
    try:
        # Read only the first two columns (A and B)
        df = pd.read_excel(file_path, header=None, usecols="A:B")

        # Map the labels to their corresponding values
        # Assuming labels are in A1:A9 and values in B1:B9
        labels = df.iloc[0:9, 0].tolist()
        values = df.iloc[0:9, 1].tolist()

        for i, label in enumerate(labels):
            # Clean label to create a dictionary key (e.g., "Home Team" -> "home_team")
            key = str(label).strip().lower().replace(" ", "_")
            value = values[i]

            if pd.isna(value): # Handle NaN values (empty cells)
                if key in ["home_scorers", "away_scorers"]:
                    match_data[key] = [] # Empty list for blank scorers
                else:
                    match_data[key] = "" # Empty string for other blank fields
            elif key in ["home_scorers", "away_scorers"]:
                # Split scorers string by comma and strip whitespace from each name
                match_data[key] = [s.strip() for s in str(value).split(',') if s.strip()]
            else:
                match_data[key] = str(value).strip() # Ensure all other values are strings

    except Exception as e:
        print(f"Error reading match data from Excel file '{file_path}': {e}")
        # Return a default structure if reading fails, to prevent further errors
        match_data = {
            "home_team": "N/A", "away_team": "N/A", "date": "N/A", "time": "N/A",
            "location": "N/A", "division": "N/A", "score": "N/A",
            "home_scorers": [], "away_scorers": []
        }
    return match_data


# --- Main Graphic Generation Function ---

def create_match_of_the_day_graphic(match_data: dict, logos_folder: str, save_folder: str, is_result: bool = False):
    """
    Creates the Match of the Day graphic, either as a preview or a result.
    """
    # Initialize drawing context with fontmode="L" for smooth rendering
    # This needs to be done early to calculate text dimensions for template selection.
    # We create a dummy image and draw object just for text measurement.
    dummy_img = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    dummy_draw = ImageDraw.Draw(dummy_img)

    # Load fonts for text measurement
    try:
        font_details_for_measure = ImageFont.truetype(FONT_PATH, FONT_SIZE_DETAILS)
        font_scorers_for_measure = ImageFont.truetype(FONT_PATH, FONT_SIZE_SCORERS)
        font_final_score_for_measure = ImageFont.truetype(FONT_PATH, FONT_SIZE_FINAL_SCORE)
    except IOError as e:
        print(f"Error loading font from {FONT_PATH} for measurement: {e}. Using default font.")
        font_details_for_measure = font_scorers_for_measure = font_final_score_for_measure = ImageFont.load_default()

    # Match data extraction for template selection
    home_scorers = match_data.get("home_scorers", [])
    away_scorers = match_data.get("away_scorers", [])

    # Determine template to use based on scorer lines for result graphic
    template_to_load = MATCH_OF_THE_DAY_TEMPLATE_PATH
    if is_result:
        home_scorers_text_combined = ", ".join(home_scorers)
        away_scorers_text_combined = ", ".join(away_scorers)

        home_scorers_lines = wrap_text(home_scorers_text_combined, font_scorers_for_measure, MAX_TEAM_NAME_WIDTH - TEAM_NAME_INTERNAL_PADDING, dummy_draw)
        away_scorers_lines = wrap_text(away_scorers_text_combined, font_scorers_for_measure, MAX_TEAM_NAME_WIDTH - TEAM_NAME_INTERNAL_PADDING, dummy_draw)

        if len(home_scorers_lines) >= 3 or len(away_scorers_lines) >= 3:
            template_to_load = MATCH_OF_THE_DAY_RESULT_TEMPLATE_NO_FOOTER_PATH

    # Load the determined template (1080x1350)
    try:
        img = Image.open(template_to_load).convert("RGBA")
        if img.size != (IMAGE_WIDTH, IMAGE_HEIGHT):
            print(f"Warning: Template '{template_to_load}' is not {IMAGE_WIDTH}x{IMAGE_HEIGHT}. Resizing might occur or layout issues may arise.")
    except Exception as e:
        print(f"Error loading template: {e}. Skipping graphic generation.")
        return

    # Initialize drawing context for the actual image
    draw = ImageDraw.Draw(img)
    draw.fontmode = "L"  # Enable anti-aliased text rendering

    # Load fonts for actual drawing
    try:
        font_details = ImageFont.truetype(FONT_PATH, FONT_SIZE_DETAILS)
        font_final_score = ImageFont.truetype(FONT_PATH, FONT_SIZE_FINAL_SCORE)
        font_team = ImageFont.truetype(FONT_PATH, FONT_SIZE_TEAM_NAME)
        font_vs = ImageFont.truetype(FONT_PATH, FONT_SIZE_VS_SCORE)
        font_scorers = ImageFont.truetype(FONT_PATH, FONT_SIZE_SCORERS)
    except IOError as e:
        print(f"Error loading font from {FONT_PATH}: {e}. Using default font.")
        font_details = font_team = font_vs = font_final_score = font_scorers = ImageFont.load_default()

    # Match data extraction (repeated for clarity, could be passed as argument)
    home_team = match_data.get("home_team", "HOME TEAM")
    away_team = match_data.get("away_team", "AWAY TEAM")
    date = match_data.get("date", "DATE")
    time = match_data.get("time", "TIME")
    location = match_data.get("location", "LOCATION")
    division = match_data.get("division", "DIVISION")
    score = match_data.get("score", "0-0")
    home_scorers = match_data.get("home_scorers", [])
    away_scorers = match_data.get("away_scorers", [])

    # Calculate base_y_shift for elements below the top section if FINAL SCORE is used
    OLD_FINAL_SCORE_FONT_SIZE = 76 # This was the original font size for FINAL SCORE
    try:
        old_final_score_font = ImageFont.truetype(FONT_PATH, OLD_FINAL_SCORE_FONT_SIZE)
    except IOError:
        old_final_score_font = ImageFont.load_default()

    old_final_score_bbox = draw.textbbox((0, 0), "FINAL SCORE", font=old_final_score_font)
    new_final_score_bbox = draw.textbbox((0, 0), "FINAL SCORE", font=font_final_score)
    old_final_score_height = old_final_score_bbox[3] - old_final_score_bbox[1]
    new_final_score_height = new_final_score_bbox[3] - new_final_score_bbox[1]
    base_y_shift = new_final_score_height - old_final_score_height

    # --- Draw Match Details or Final Score ---
    if is_result:
        # Show "FINAL SCORE" for result graphic
        final_score_text = "FINAL SCORE"
        final_score_bbox = draw.textbbox((0, 0), final_score_text, font=font_final_score)
        final_score_width = final_score_bbox[2] - final_score_bbox[0]
        final_score_x = (IMAGE_WIDTH - final_score_width) // 2  # Center horizontally
        
        # Apply the adjustment for FINAL SCORE vertical position
        final_score_y = Y_POS_DETAILS_OR_FINAL_SCORE + FINAL_SCORE_VERTICAL_ADJUSTMENT # Adjusted Y-position for FINAL SCORE
        draw.text((final_score_x, final_score_y), final_score_text, fill=GREEN_COLOR, font=font_final_score)
    else:
        # Show date, time, location for preview graphic
        details_text = f"{date} | {time} | {location}"
        details_bbox = draw.textbbox((0, 0), details_text, font=font_details)
        details_width = details_bbox[2] - details_bbox[0]
        details_x = (IMAGE_WIDTH - details_width) // 2  # Center horizontally
        draw.text((details_x, Y_POS_DETAILS_OR_FINAL_SCORE), details_text, fill=TEXT_COLOR, font=font_details)

    # --- Competition (Division) with Silver Gradient Bar ---
    division_text = division
    division_bbox = draw.textbbox((0, 0), division_text, font=font_details)
    division_width = division_bbox[2] - division_bbox[0]
    division_height = division_bbox[3] - division_bbox[1]

    # Dynamic silver box with padding
    division_box_width = division_width + 2 * DIVISION_BAR_PADDING_X
    division_box_height = division_height + 2 * DIVISION_BAR_PADDING_Y
    division_box_x = (IMAGE_WIDTH - division_box_width) // 2  # Center the box
    
    # Adjust division_box_y based on whether it's a result or preview
    # This ensures the division bar is correctly positioned for both cases.
    if is_result:
        # Calculate division_box_y relative to the adjusted final_score_y
        # It should be 65 pixels below the bottom of the FINAL SCORE text as per user's last adjustment
        final_score_bottom_y = final_score_y + new_final_score_height
        division_box_y = final_score_bottom_y + 65 # Updated to 65px below FINAL SCORE text
    else:
        # For preview, calculate distance from details_text
        details_height_actual = draw.textbbox((0, 0), details_text, font=font_details)[3] - draw.textbbox((0, 0), details_text, font=font_details)[1]
        # This calculation aims to maintain a consistent visual gap between the details/final score and the division bar
        # Adjusting this multiplier (0.75) can fine-tune the gap for preview graphics.
        division_box_y = Y_POS_DETAILS_OR_FINAL_SCORE + details_height_actual + (Y_POS_DIVISION_BAR - (Y_POS_DETAILS_OR_FINAL_SCORE + details_height_actual)) * 0.75


    # Create silver gradient background for the bar
    gradient = create_silver_gradient(division_box_width, division_box_height)
    img.paste(gradient, (division_box_x, int(division_box_y)))

    # Draw 1px black stroke outline
    draw.rectangle(
        [division_box_x, division_box_y, division_box_x + division_box_width, division_box_y + division_box_height],
        outline=DIVISION_BAR_OUTLINE_COLOR,
        width=DIVISION_BAR_OUTLINE_WIDTH
    )
    
    # Center division text in the box, applying vertical adjustment
    division_x = division_box_x + (division_box_width - division_width) // 2
    division_y = division_box_y + (division_box_height - division_height) // 2 + DIVISION_TEXT_VERTICAL_ADJUSTMENT
    draw.text((division_x, division_y), division_text, fill=TEXT_COLOR, font=font_details)

    # --- Team Logos ---
    home_logo = get_logo(home_team, logos_folder).resize(LOGO_DISPLAY_SIZE, Image.Resampling.LANCZOS)
    away_logo = get_logo(away_team, logos_folder).resize(LOGO_DISPLAY_SIZE, Image.Resampling.LANCZOS)
    
    # Logos are positioned at fixed X, and calculated Y to align with Y_POS_LOGOS, applying base_y_shift for results
    logo_y = Y_POS_LOGOS + (base_y_shift if is_result else 0)
    img.paste(home_logo, (HOME_TEAM_LOGO_X, int(logo_y)), home_logo)
    img.paste(away_logo, (AWAY_TEAM_LOGO_X, int(logo_y)), away_logo)

    # --- "VS" or Score ---
    if is_result:
        vs_text = score.replace("-", " - ")  # Add space around the dash
    else:
        vs_text = "VS"
    
    vs_bbox = draw.textbbox((0, 0), vs_text, font=font_vs)
    vs_width = vs_bbox[2] - vs_bbox[0]
    vs_x = (IMAGE_WIDTH - vs_width) // 2  # Center horizontally
    vs_y = Y_POS_VS_OR_SCORE + (base_y_shift if is_result else 0)
    draw.text((vs_x, vs_y), vs_text, fill=TEXT_COLOR, font=font_vs)

    # --- Team Names with Wrapping ---
    home_team_lines = wrap_text(home_team, font_team, MAX_TEAM_NAME_WIDTH - TEAM_NAME_INTERNAL_PADDING, draw)
    away_team_lines = wrap_text(away_team, font_team, MAX_TEAM_NAME_WIDTH - TEAM_NAME_INTERNAL_PADDING, draw)
    
    # Home Team Name
    current_y_home_team = Y_POS_TEAM_NAMES + (base_y_shift if is_result else 0)
    for line in home_team_lines:
        line_bbox = draw.textbbox((0, 0), line, font=font_team)
        line_width = line_bbox[2] - line_bbox[0]
        line_x = HOME_TEAM_LOGO_X + (LOGO_DISPLAY_SIZE[0] - line_width) // 2  # Center under logo
        draw.text((line_x, current_y_home_team), line, fill=TEXT_COLOR, font=font_team)
        current_y_home_team += TEAM_NAME_LINE_SPACING

    # Away Team Name
    current_y_away_team = Y_POS_TEAM_NAMES + (base_y_shift if is_result else 0)
    for line in away_team_lines:
        line_bbox = draw.textbbox((0, 0), line, font=font_team)
        line_width = line_bbox[2] - line_bbox[0]
        line_x = AWAY_TEAM_LOGO_X + (LOGO_DISPLAY_SIZE[0] - line_width) // 2  # Center under logo
        draw.text((line_x, current_y_away_team), line, fill=TEXT_COLOR, font=font_team)
        current_y_away_team += TEAM_NAME_LINE_SPACING

    # --- Result: Goal Scorers Under Respective Teams ---
    if is_result:
        # Home Scorers
        if home_scorers: # This check allows the box to be blank if the list is empty
            home_scorers_text_combined = ", ".join(home_scorers) # Join into a single line for wrapping
            home_scorers_lines = wrap_text(home_scorers_text_combined, font_scorers, MAX_TEAM_NAME_WIDTH - TEAM_NAME_INTERNAL_PADDING, draw)
            
            # Position below the last line of the team name, using current_y_home_team after team name drawing
            scorer_y_start_home = current_y_home_team + SCORER_TEXT_VERTICAL_OFFSET

            current_line_y_scorer_home = scorer_y_start_home
            for line in home_scorers_lines:
                line_bbox = draw.textbbox((0, 0), line, font=font_scorers)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = HOME_TEAM_LOGO_X + (LOGO_DISPLAY_SIZE[0] - line_width) // 2 # Center under logo
                draw.text((line_x, current_line_y_scorer_home), line, fill=WHITE_COLOR, font=font_scorers)
                # Use the actual height of the drawn text line plus the defined line spacing
                current_line_y_scorer_home += (line_bbox[3] - line_bbox[1]) + SCORER_LINE_SPACING

        # Away Scorers
        if away_scorers: # This check allows the box to be blank if the list is empty
            away_scorers_text_combined = ", ".join(away_scorers) # Join into a single line for wrapping
            away_scorers_lines = wrap_text(away_scorers_text_combined, font_scorers, MAX_TEAM_NAME_WIDTH - TEAM_NAME_INTERNAL_PADDING, draw)

            # Position below the last line of the team name, using current_y_away_team after team name drawing
            scorer_y_start_away = current_y_away_team + SCORER_TEXT_VERTICAL_OFFSET
            
            current_line_y_scorer_away = scorer_y_start_away
            for line in away_scorers_lines:
                line_bbox = draw.textbbox((0, 0), line, font=font_scorers)
                line_width = line_bbox[2] - line_bbox[0]
                line_x = AWAY_TEAM_LOGO_X + (LOGO_DISPLAY_SIZE[0] - line_width) // 2 # Center under logo
                draw.text((line_x, current_line_y_scorer_away), line, fill=WHITE_COLOR, font=font_scorers)
                # Use the actual height of the drawn text line plus the defined line spacing
                current_line_y_scorer_away += (line_bbox[3] - line_bbox[1]) + SCORER_LINE_SPACING

    # Save the image
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    suffix = "result" if is_result else "preview"
    output_file_path = os.path.join(save_folder, f"match_of_the_day_{suffix}_{current_time}.png")
    img.save(output_file_path)
    print(f"Graphic saved to: {output_file_path}")
    img.show()

# Example usage
if __name__ == "__main__":
    # Load match data from Excel
    loaded_match_data = read_match_data_from_excel(MATCH_DATA_EXCEL_PATH)

    if loaded_match_data:
        # Generate preview graphic
        create_match_of_the_day_graphic(
            loaded_match_data,
            LOGOS_FOLDER,
            SAVE_FOLDER,
            is_result=False
        )

        # Generate result graphic
        create_match_of_the_day_graphic(
            loaded_match_data,
            LOGOS_FOLDER,
            SAVE_FOLDER,
            is_result=True
        )
    else:
        print("Could not load match data from Excel. Please check the file path and format.")
