import os
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
from datetime import datetime
import glob # Needed for debugging

# --- Deployment Environment Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Configuration Constants ---
# Paths (using BASE_DIR which should resolve the path)
LEAGUE_TABLE_FILE_PATH = os.path.join(BASE_DIR, "table.xlsx")
LOGOS_FOLDER = os.path.join(BASE_DIR, "Logos")
SAVE_FOLDER = os.path.join(BASE_DIR, "Graphics")
TEMPLATES_FOLDER = os.path.join(BASE_DIR, "Templates")
FONT_PATH = os.path.join(BASE_DIR, "BebasNeue Regular.ttf") 

# ... (All other constants remain the same) ...

IMAGE_WIDTH = 1080
IMAGE_HEIGHT = 1350
TABLE_LEFT_OFFSET = 33
TABLE_TOP_OFFSET = 320
ROW_HEIGHT = 100
LOGO_SIZE = 80
DATE_CIRCLE_SIZE = 135
DATE_CIRCLE_X = 1080 - 91 - 142
DATE_CIRCLE_Y = 1212
DATE_CIRCLE_STROKE = 3
HIGH_RES_SCALE = 2
DATE_TEXT_MAX_WIDTH = DATE_CIRCLE_SIZE - 20
DATE_TEXT_MAX_HEIGHT = DATE_CIRCLE_SIZE - 20

COL_POS_WIDTH = 60
COL_TEAM_NAME_WIDTH = 400
COL_STAT_WIDTH = 80
COL_POSITIONS = {
    "Pos": 10,
    "Team": 10 + COL_POS_WIDTH + LOGO_SIZE + 10,
    "P": 10 + COL_POS_WIDTH + LOGO_SIZE + COL_TEAM_NAME_WIDTH + 20,
    "W": 10 + COL_POS_WIDTH + LOGO_SIZE + COL_TEAM_NAME_WIDTH + 20 + COL_STAT_WIDTH,
    "D": 10 + COL_POS_WIDTH + LOGO_SIZE + COL_TEAM_NAME_WIDTH + 20 + COL_STAT_WIDTH * 2,
    "L": 10 + COL_POS_WIDTH + LOGO_SIZE + COL_TEAM_NAME_WIDTH + 20 + COL_STAT_WIDTH * 3,
    "GD": 10 + COL_POS_WIDTH + LOGO_SIZE + COL_TEAM_NAME_WIDTH + 20 + COL_STAT_WIDTH * 4,
    "PTS": 10 + COL_POS_WIDTH + LOGO_SIZE + COL_TEAM_NAME_WIDTH + 20 + COL_STAT_WIDTH * 5,
}

FONT_SIZE_NORMAL = 50
FONT_SIZE_HEADER = 50
FONT_SIZE_DATE = 40
FONT_SIZE_DATE_MIN = 30

LINE_SPACING_TEAM_NAME = 10
VISUAL_Y_OFFSET_CORRECTION = -5
HEADER_TEXT_TOP_PADDING = 19

DIVISION_TEMPLATES = {
    "Division 1": "division_1_league_template.png",
    "Division 2": "division_2_league_template.png",
    "Division 3": "division_3_league_template.png",
    "Division 4": "division_4_league_template.png",
}

SPECIAL_LOGO_MAPPING = {
    "afc aldermaston a": "AFC Aldermaston.png",
    "afc aldermaston b": "AFC Aldermaston.png",
    "eversley & california sunday": "Eversley & California.png",
}

# --- Helper Functions (No changes needed here) ---

def get_logo(team_name: str, logos_folder: str) -> Image.Image:
    """
    Loads a team logo, handling specific variants and searching subfolders.
    Returns a resized PIL Image object.
    """
    valid_extensions = ('.png', '.jpg', '.jpeg')
    team_name_lower = team_name.strip().lower()
    
    logo_filename = None
    for variant_key, filename in SPECIAL_LOGO_MAPPING.items():
        if variant_key in team_name_lower:
            logo_filename = filename
            break

    search_names = [logo_filename] if logo_filename else [f'{team_name_lower}.png', f'{team_name_lower}.jpg']
    
    if not logo_filename:
        base_name = team_name.strip().replace(' ', '')
        search_names.extend([f'{base_name}.png', f'{base_name}.jpg', f'{base_name.replace("united", "utd")}.png'])
    
    
    for name in search_names:
        for subfolder in ['Current Teams', 'Old Teams', '']:
            search_path = os.path.join(logos_folder, subfolder, name)
            if os.path.exists(search_path) and search_path.lower().endswith(valid_extensions):
                try:
                    img = Image.open(search_path).convert("RGBA").resize((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS)
                    return img
                except Exception as e:
                    print(f"Error loading logo for {team_name} from '{search_path}': {e}")
                
    generic_logo_path = os.path.join(logos_folder, 'genericlogo.png')
    try:
        return Image.open(generic_logo_path).convert("RGBA").resize((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS)
    except Exception as e:
        print(f"Error loading generic logo: {e}. Using gray placeholder.")
        return Image.new("RGBA", (LOGO_SIZE, LOGO_SIZE), (200, 200, 200, 255))

def parse_league_table_from_file(file_path: str, division: str) -> pd.DataFrame:
    """
    Parses league table data from a specified Excel sheet.
    Returns a pandas DataFrame.
    """
    try:
        if not os.path.exists(file_path):
             # NOTE: This FileNotFoundError will now only be raised after the debugging check.
             raise FileNotFoundError(f"File not found: {file_path}")
             
        excel_data = pd.read_excel(file_path, sheet_name=division)
        print(f"Loaded {len(excel_data)} rows from {division} tab in XLSX file.")
        return excel_data
    except FileNotFoundError as e:
        print(f"Error reading the file for {division}: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Error reading the sheet for {division}: {e}")
        return pd.DataFrame()

def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """
    Wraps text to fit within a maximum width, returning a list of lines.
    """
    words = text.split()
    lines = []
    current_line = []
    
    def get_text_width(txt, f):
        return draw.textbbox((0, 0), txt, font=f)[2] - draw.textbbox((0, 0), txt, font=f)[0]
    
    
    for word in words:
        test_line = " ".join(current_line + [word])
        test_width = get_text_width(test_line, font)
        
        if test_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            
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

# --- Main Graphic Generation Function (No changes needed here) ---
def create_league_table_graphic(league_data: pd.DataFrame, logos_folder: str, save_folder: str, division_name: str, current_date: datetime):
    """
    Creates a league table graphic for a specific division with a date circle.
    """
    template_filename = DIVISION_TEMPLATES.get(division_name, "division_1_league_template.png")
    template_path = os.path.join(TEMPLATES_FOLDER, template_filename)
    try:
        img = Image.open(template_path).convert("RGBA")
        if img.size != (IMAGE_WIDTH, IMAGE_HEIGHT):
            print(f"Warning: Template '{template_filename}' is not {IMAGE_WIDTH}x{IMAGE_HEIGHT}. Resizing might occur or layout issues may arise.")
    except Exception as e:
        print(f"Error loading template for {division_name} from '{template_path}': {e}. Skipping graphic generation.")
        return

    # Load fonts
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE_NORMAL)
        header_font = ImageFont.truetype(FONT_PATH, FONT_SIZE_HEADER)
    except IOError:
        font = header_font = ImageFont.load_default()

    # Draw date circle on a high-resolution temporary image
    high_res_size = DATE_CIRCLE_SIZE * HIGH_RES_SCALE
    circle_img = Image.new("RGBA", (high_res_size, high_res_size), (0, 0, 0, 0))
    circle_draw = ImageDraw.Draw(circle_img)
    day_text = current_date.strftime("%d")
    month_text = current_date.strftime("%b").upper()
    year_text = current_date.strftime("%Y")
    circle_center_x = high_res_size // 2
    circle_center_y = high_res_size // 2

    # Dynamic font size adjustment
    font_size = FONT_SIZE_DATE
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
    day_y = circle_center_y - text_height_half
    month_y = day_y + day_height + 5 * HIGH_RES_SCALE
    year_y = month_y + month_height + 5 * HIGH_RES_SCALE
    
    circle_draw.text((circle_center_x - (day_bbox[2] - day_bbox[0]) // 2, day_y), day_text, fill=(0, 0, 0, 255), font=date_font)
    circle_draw.text((circle_center_x - (month_bbox[2] - month_bbox[0]) // 2, month_y), month_text, fill=(0, 0, 0, 255), font=date_font)
    circle_draw.text((circle_center_x - (year_bbox[2] - year_bbox[0]) // 2, year_y), year_text, fill=(0, 0, 0, 255), font=date_font)
    
    circle_img = circle_img.resize((DATE_CIRCLE_SIZE, DATE_CIRCLE_SIZE), Image.LANCZOS)
    img.paste(circle_img, (DATE_CIRCLE_X, DATE_CIRCLE_Y), circle_img)

    # Create table content
    table_content_height = HEADER_TEXT_TOP_PADDING + FONT_SIZE_HEADER + (len(league_data) * ROW_HEIGHT) + 20
    table_img = Image.new("RGBA", (IMAGE_WIDTH, int(table_content_height) + TABLE_TOP_OFFSET), (0, 0, 0, 0))
    d = ImageDraw.Draw(table_img)

    # Draw column headers
    headers = ["Pos", "Team", "P", "W", "D", "L", "GD", "PTS"]
    header_y = HEADER_TEXT_TOP_PADDING
    
    for header in headers:
        header_bbox = d.textbbox((0, 0), header, font=header_font)
        header_width_actual = header_bbox[2] - header_bbox[0]
        col_width = COL_POS_WIDTH if header == "Pos" else COL_TEAM_NAME_WIDTH if header == "Team" else COL_STAT_WIDTH
        
        header_x = COL_POSITIONS[header] + (col_width - header_width_actual) // 2
        d.text((header_x, header_y), header, fill=(255, 255, 255), font=header_font)

    # Calculate row content start
    header_height_actual = d.textbbox((0, 0), "POS", font=header_font)[3] - d.textbbox((0, 0), "POS", font=header_font)[1]
    row_content_start_y_offset = 20
    current_row_y = HEADER_TEXT_TOP_PADDING + header_height_actual + row_content_start_y_offset

    # Loop through teams
    for _, row in league_data.iterrows():
        pos = str(row.get('Pos', ''))
        team_name = str(row.get('Team', ''))
        played = str(row.get('P', ''))
        won = str(row.get('W', ''))
        drawn = str(row.get('D', ''))
        lost = str(row.get('L', ''))
        gd = str(row.get('GD', ''))
        points = str(row.get('PTS', ''))
        
        centerline_y = current_row_y + (ROW_HEIGHT // 2)

        # Draw logo
        logo = get_logo(team_name, logos_folder)
        if logo:
            logo_x = COL_POSITIONS["Pos"] + COL_POS_WIDTH + (COL_POSITIONS["Team"] - (COL_POSITIONS["Pos"] + COL_POS_WIDTH) - LOGO_SIZE) // 2
            logo_y = int(centerline_y - (LOGO_SIZE // 2))
            table_img.paste(logo, (logo_x, logo_y), logo)

        # Position text
        pos_bbox = d.textbbox((0, 0), pos, font=font)
        pos_width_actual = pos_bbox[2] - pos_bbox[0]
        pos_height_actual = pos_bbox[3] - pos_bbox[1]
        pos_x = COL_POSITIONS["Pos"] + (COL_POS_WIDTH - pos_width_actual) // 2
        pos_y = centerline_y - (pos_height_actual // 2) + VISUAL_Y_OFFSET_CORRECTION
        d.text((pos_x, pos_y), pos, fill=(255, 255, 255), font=font)

        # Team name with wrapping
        team_lines = wrap_text(team_name, font, COL_TEAM_NAME_WIDTH - 20, d)
        team_total_text_block_height = get_wrapped_text_block_height(team_lines, font, LINE_SPACING_TEAM_NAME, d)
        team_start_y_text = centerline_y - (team_total_text_block_height // 2) + VISUAL_Y_OFFSET_CORRECTION
        current_line_y_team = team_start_y_text
        
        for line in team_lines:
            line_bbox = d.textbbox((0, 0), line, font=font)
            line_width_actual = line_bbox[2] - line_bbox[0]
            line_x = COL_POSITIONS["Team"] + (COL_TEAM_NAME_WIDTH - line_width_actual) // 2
            d.text((line_x, current_line_y_team), line, fill=(255, 255, 255), font=font)
            current_line_y_team += (line_bbox[3] - line_bbox[1]) + LINE_SPACING_TEAM_NAME

        # Stats
        stats_data = [played, won, drawn, lost, gd, points]
        stat_cols = ["P", "W", "D", "L", "GD", "PTS"]
        for stat, col_name in zip(stats_data, stat_cols):
            stat_bbox = d.textbbox((0, 0), stat, font=font)
            stat_width_actual = stat_bbox[2] - stat_bbox[0]
            stat_height_actual = stat_bbox[3] - stat_bbox[1]
            stat_x = COL_POSITIONS[col_name] + (COL_STAT_WIDTH - stat_width_actual) // 2
            stat_y = centerline_y - (stat_height_actual // 2) + VISUAL_Y_OFFSET_CORRECTION
            d.text((stat_x, stat_y), stat, fill=(255, 255, 255), font=font)
            
        current_row_y += ROW_HEIGHT

    # Paste table onto template
    img.paste(table_img, (TABLE_LEFT_OFFSET, TABLE_TOP_OFFSET), table_img)

    # Save the image
    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
        
    output_file_path = os.path.join(save_folder, f"{division_name}_League_Table_{current_time}.png")
    img.save(output_file_path)
    print(f"Graphic saved to: {output_file_path}")

# --- Main function to process all divisions (FIXED WITH DEBUGGING) ---
def generate_league_table_graphics(file_path: str, logos_folder: str, save_folder: str):
    """
    Main function to process all divisions and generate league table graphics.
    Includes debugging to show the actual path and file listing.
    """
    
    # ----------------------------------------------------
    # 🛑 CRITICAL DEBUGGING SECTION 🛑
    # ----------------------------------------------------
    print("\n--- DEBUGGING FILE PATH START ---")
    
    # 1. Print the determined file path
    print(f"DEBUG: Attempting to access file at: {file_path}")
    
    # 2. Print the script's current working directory (BASE_DIR)
    base_dir_used = os.path.dirname(os.path.abspath(__file__))
    print(f"DEBUG: BASE_DIR (Script Directory) is: {base_dir_used}")
    
    # 3. List all files in the script directory (BASE_DIR)
    print(f"DEBUG: Files visible in {base_dir_used}:")
    try:
        visible_files = os.listdir(base_dir_used)
        for item in visible_files:
            # Highlight table.xlsx if it's found
            if item.lower() == 'table.xlsx':
                print(f"   --> ✅ FOUND: {item}")
            else:
                print(f"   - {item}")
    except Exception as e:
        print(f"   - Failed to list directory contents: {e}")
        
    print("--- DEBUGGING FILE PATH END ---\n")
    # ----------------------------------------------------
    
    current_date = datetime.now()
    try:
        # Check if file exists based on the path
        if not os.path.exists(file_path):
             # This confirms if os.path.exists() can see the file at the generated path
             raise FileNotFoundError(f"File not found by os.path.exists(): {file_path}")
             
        # Attempt to read the date
        date_df = pd.read_excel(file_path, sheet_name='Division 1', header=None)
        
        if date_df.shape[0] > 1 and date_df.shape[1] > 8:
            date_data = date_df.iloc[1, 8]
            date_str = str(date_data).strip()
            
            # ... (Date parsing logic remains the same) ...
            date_formats = ['%d/%m/%Y', '%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%d-%m-%Y']
            parsed_date = None
            
            for fmt in date_formats:
                try:
                    parsed_date = pd.to_datetime(date_str, format=fmt, errors='raise')
                    print(f"Date {date_str} read from 'Division 1' sheet, cell R2C9 in {file_path} using format {fmt}")
                    break
                except ValueError:
                    continue
            
            if parsed_date is None:
                parsed_date = pd.to_datetime(date_str, errors='coerce')
                if pd.isna(parsed_date):
                    raise ValueError(f"Invalid date format in 'Division 1' sheet, cell R2C9: {date_str}")
                print(f"Date {date_str} parsed as timestamp from 'Division 1' sheet, cell R2C9 in {file_path}")
            
            current_date = parsed_date
        else:
            print(f"Warning: 'Division 1' sheet too small or missing cell R2C9 in {file_path}. Using current date.")
            
    except FileNotFoundError as e:
        # This is where the error surfaces if the file is truly invisible
        print(f"CRITICAL ERROR (File System/Permissions): {e}. Using current date.")
    except Exception as e:
        # This catches errors like sheet name not found, or pandas read issues
        print(f"CRITICAL ERROR (Pandas/Data): Error reading 'Division 1' sheet: {e}. Using current date.")
        
    divisions_to_generate = ["Division 1", "Division 2", "Division 3", "Division 4"]
    for division in divisions_to_generate:
        print(f"Processing {division}...")
        league_data = parse_league_table_from_file(file_path, division)
        if not league_data.empty:
            required_cols = ['Pos', 'Team', 'P', 'W', 'D', 'L', 'GD', 'PTS']
            if all(col in league_data.columns for col in required_cols):
                create_league_table_graphic(
                    league_data,
                    logos_folder,
                    save_folder,
                    division,
                    current_date
                )
            else:
                print(f"Skipping {division}: Data is missing one or more required columns ({required_cols}).")
        else:
            print(f"No data found for {division}.")

    print("Table graphics generation finished.")

# Example usage
if __name__ == "__main__":
    generate_league_table_graphics(LEAGUE_TABLE_FILE_PATH, LOGOS_FOLDER, SAVE_FOLDER)