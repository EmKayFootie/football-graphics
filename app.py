import streamlit as st
import os
import zipfile
import shutil
import subprocess
import glob
import sys
import pandas as pd

# --- Configuration for Git Repository Files ---
# Define the project structure AS IT EXISTS in your Git repo root
# These files will be copied from the repo root to the temporary project_dir
GIT_FILES_TO_COPY = [
    "results.xlsx",
    "Fixtures - automated.py",
    "match of the day - automated.py",
    "Results - automated.py",
    "table - automated.py",
    "BebasNeue Regular.ttf",
]
GIT_DIRS_TO_COPY = [
    "Logos",
    "Templates",
]
# ----------------------------------------------

# Streamlit GUI
st.title("⚽ Football Graphics Generator")
st.write("Using files and scripts directly from the deployed GitHub repository.")

# --- File Setup Block: Copies Files from Git Repo to Tmp Folder ---
# This block copies the files from the Git repo root into a tmp folder
# where the rest of the script expects them (project_dir).

# Create and clean the project directory
project_dir = os.path.join("tmp", "project")
if os.path.exists(project_dir):
    shutil.rmtree(project_dir)
os.makedirs(project_dir, exist_ok=True)

# Define the root of the Streamlit application (where the Git repo contents are)
repo_root = os.getcwd() 

# Copy individual files from the repo root to the project_dir
all_files_present = True
for item in GIT_FILES_TO_COPY:
    source_path = os.path.join(repo_root, item)
    dest_path = os.path.join(project_dir, item)
    if os.path.exists(source_path):
        shutil.copy2(source_path, dest_path)
    else:
        st.error(f"FATAL ERROR: Required file not found in Git repository: {item}")
        all_files_present = False

# Copy folders from the repo root to the project_dir
for item in GIT_DIRS_TO_COPY:
    source_path = os.path.join(repo_root, item)
    dest_path = os.path.join(project_dir, item)
    if os.path.exists(source_path):
        # Use copytree to copy the folder contents
        shutil.copytree(source_path, dest_path)
    else:
        st.error(f"FATAL ERROR: Required directory not found in Git repository: {item}")
        all_files_present = False

if not all_files_present:
    st.stop()
else:
    st.success("Project files loaded successfully from the Git repository.")

# --- Continue with the rest of the logic ---

# Check for required files
if not os.path.exists(os.path.join(project_dir, "results.xlsx")):
    st.error("Error: results.xlsx not found in project folder!")
    st.stop()

# Ensure Graphics folder exists
graphics_dir = os.path.join(project_dir, "Graphics")
os.makedirs(graphics_dir, exist_ok=True)

# Mode selection dropdown
mode = st.selectbox("Select Graphic Type", ["Fixtures", "Match of the Day", "Results", "Table"])

# Map mode to script
script_map = {
    "Fixtures": "Fixtures - automated.py",
    "Match of the Day": "match of the day - automated.py",
    "Results": "Results - automated.py",
    "Table": "table - automated.py"
}
selected_script = script_map[mode]
script_path_in_project = os.path.join(project_dir, selected_script)

if not os.path.exists(script_path_in_project):
    st.error(f"Error: {selected_script} not found in project folder!")
    st.stop()

# Button to run the script
if st.button(f"Generate {mode} Graphics"):
    with st.spinner(f"Generating {mode} graphics..."):
        
        # --- PATH INJECTION FOR SUBPROCESS ---
        
        # 1. Define all absolute paths for injection
        absolute_project_dir = os.path.abspath(project_dir)
        absolute_excel_path = os.path.normpath(os.path.join(absolute_project_dir, "results.xlsx"))
        absolute_logos_folder = os.path.normpath(os.path.join(absolute_project_dir, "Logos"))
        absolute_save_folder = os.path.normpath(os.path.join(absolute_project_dir, "Graphics"))
        absolute_templates_folder = os.path.normpath(os.path.join(absolute_project_dir, "Templates"))
        # CRITICAL FIX: Absolute path for the font file
        absolute_font_path = os.path.normpath(os.path.join(absolute_project_dir, "BebasNeue Regular.ttf"))
        
        # 2. Read the script content
        script_content = open(script_path_in_project, 'r', encoding='utf-8').read()
        
        # 3. Perform Path Replacements
        # NOTE: The keys being replaced MUST match the EXACT string in your Fixtures/Results scripts.
        # We are replacing the old relative path with the new absolute path.
        script_content = script_content.replace(
            'RESULTS_FILE_PATH = "results.xlsx"',
            f'RESULTS_FILE_PATH = r"{absolute_excel_path}"'
        ).replace(
            'FIXTURES_FILE_PATH = "results.xlsx"', # For fixtures script
            f'FIXTURES_FILE_PATH = r"{absolute_excel_path}"'
        ).replace(
            'LOGOS_FOLDER = "Logos"',
            f'LOGOS_FOLDER = r"{absolute_logos_folder}"'
        ).replace(
            'SAVE_FOLDER = "Graphics"',
            f'SAVE_FOLDER = r"{absolute_save_folder}"'
        ).replace(
            'TEMPLATES_FOLDER = "Templates"',
            f'TEMPLATES_FOLDER = r"{absolute_templates_folder}"'
        ).replace(
            # This line specifically fixes the font loading issue by using the absolute path
            'FONT_PATH = "BebasNeue Regular.ttf"',
            f'FONT_PATH = r"{absolute_font_path}"'
        )
        
        # 4. Save modified script to a temp file (same name in the project directory)
        temp_script_path = os.path.join(project_dir, "temp_" + selected_script)
        with open(temp_script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
            
        # 5. Run the temporary script
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            # Run the temp script directly (it's in the project_dir, but we use its full path)
            result = subprocess.run([sys.executable, temp_script_path], capture_output=True, text=True, env=env)
            
            st.write("**Console Output:**")
            st.code(result.stdout)
            if result.stderr:
                st.error(f"**Errors:**\n{result.stderr}")
            else:
                st.success(f"{mode} graphics generated successfully!")
        except Exception as e:
            st.error(f"Error running script: {e}")
            
    # Provide download links for generated PNGs and ZIP (uses graphics_dir)
    if os.path.exists(graphics_dir):
        png_files = glob.glob(os.path.join(graphics_dir, "*.png"))
        
        if png_files:
            st.write("**Download Generated Graphics:**")
            # Individual PNG downloads
            for png in png_files:
                with open(png, "rb") as f:
                    st.download_button(
                        label=f"Download {os.path.basename(png)}",
                        data=f,
                        file_name=os.path.basename(png),
                        mime="image/png"
                    )
            # ZIP download for all PNGs
            zip_path = os.path.join("tmp", "graphics.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for png in png_files:
                    zipf.write(png, os.path.join("Graphics", os.path.basename(png)))
            with open(zip_path, "rb") as f:
                st.download_button(
                    label="Download All Graphics as ZIP",
                    data=f,
                    file_name="graphics.zip",
                    mime="application/zip"
                )
        else:
            st.warning("No PNGs found in Graphics folder.")
    else:
        st.error("Graphics folder not created. Check script errors.")