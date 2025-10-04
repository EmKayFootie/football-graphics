import streamlit as st
import os
import zipfile
import shutil
import subprocess
import glob
import sys
import pandas as pd # Used to check for results.xlsx existence

# --- Configuration for Git Repository Files ---
# Define the project structure AS IT EXISTS in your Git repo root
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
st.title("Football Graphics Generator")
st.write("Using files and scripts directly from the deployed GitHub repository.")

# --- File Setup Block: Replaces the ZIP Uploader ---
# This block copies the files from the Git repo root into a tmp folder
# where the rest of the script expects them (project_dir).

# Create and clean the project directory
project_dir = os.path.join("tmp", "project")
if os.path.exists(project_dir):
    shutil.rmtree(project_dir)
os.makedirs(project_dir, exist_ok=True)

# Define the root of the Streamlit application (where the Git repo contents are)
repo_root = os.getcwd() # The current working directory is the repo root on Streamlit Cloud

# Copy individual files from the repo root to the project_dir
all_files_present = True
for item in GIT_FILES_TO_COPY:
    source_path = os.path.join(repo_root, item)
    dest_path = os.path.join(project_dir, item)
    if os.path.exists(source_path):
        # We need to explicitly check if 'results.xlsx' is present
        if item == "results.xlsx":
            excel_path = dest_path # Set excel_path here for later use
        shutil.copy2(source_path, dest_path)
    else:
        st.error(f"FATAL ERROR: Required file not found in Git repository: {item}")
        all_files_present = False

# Copy folders from the repo root to the project_dir
for item in GIT_DIRS_TO_COPY:
    source_path = os.path.join(repo_root, item)
    dest_path = os.path.join(project_dir, item)
    if os.path.exists(source_path):
        shutil.copytree(source_path, dest_path)
    else:
        st.error(f"FATAL ERROR: Required directory not found in Git repository: {item}")
        all_files_present = False

if not all_files_present:
    st.stop() # Stop execution if any critical file/folder is missing
else:
    st.success("Project files loaded successfully from the Git repository.")

# --- Continue with the rest of the logic, which now runs directly ---

# Search for scripts and excel in project_dir and subdirectories
# Note: Since we copied everything to the root of project_dir, this search is simpler now.
script_paths = {}
script_names = [
    "Fixtures - automated.py",
    "match of the day - automated.py",
    "Results - automated.py",
    "table - automated.py"
]
# Search only in the root of project_dir
for script_name in script_names:
    path = os.path.join(project_dir, script_name)
    if os.path.exists(path):
        script_paths[script_name] = path

# The rest of the script remains largely the same, using the project_dir structure

if not os.path.exists(os.path.join(project_dir, "results.xlsx")):
    st.error("Error: results.xlsx not found in project folder!")
    st.stop()

if not any(script_paths.values()):
    st.error("Error: No scripts found in project folder!")
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
if selected_script not in script_paths:
    st.error(f"Error: {selected_script} not found in project folder!")
    st.stop()

# Button to run the script
if st.button(f"Generate {mode} Graphics"):
    with st.spinner(f"Generating {mode} graphics..."):
        script_path = script_paths[selected_script]
        
        # NOTE: The path replacement logic below is highly specific and likely needs
        # to be run against all four scripts' content, not just the selected one.
        # Since your scripts now use relative paths, you can simplify the logic
        # OR ensure the scripts are run from the correct directory.
        
        # --- Simplified Execution for Relative Paths ---
        # The complex string replacements are typically not needed if your
        # scripts use relative paths correctly, but since you had them, 
        # let's keep the environment setup simple:
        
        # Change CWD to the project_dir before running the script
        original_cwd = os.getcwd()
        os.chdir(project_dir) 
        
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            # Run the script directly using its relative path within the project_dir
            # (The script's name is the command, as CWD is set to project_dir)
            result = subprocess.run([sys.executable, selected_script], capture_output=True, text=True, env=env)
            
            st.write("**Console Output:**")
            st.code(result.stdout)
            if result.stderr:
                st.error(f"**Errors:**\n{result.stderr}")
            else:
                st.success(f"{mode} graphics generated successfully!")
        except Exception as e:
            st.error(f"Error running script: {e}")
        finally:
            # IMPORTANT: Change the working directory back
            os.chdir(original_cwd)

    # Provide download links for generated PNGs and ZIP (unchanged logic)
    if os.path.exists(graphics_dir):
        # The glob needs to be run from the CWD that the app.py is running in, 
        # so we use the full graphics_dir path.
        png_files = glob.glob(os.path.join(graphics_dir, "*.png"))
        
        # ... (Download logic remains the same) ...
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
                    # Write the file *inside* the zip with a clean path ("Graphics/...")
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
