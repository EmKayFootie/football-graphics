import streamlit as st
import os
import shutil
import subprocess
import glob
import sys
import pandas as pd

# --- Configuration for Git Repository Files ---
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

# Create and clean the project directory
project_dir = os.path.join("tmp", "project")
if os.path.exists(project_dir):
    shutil.rmtree(project_dir)
os.makedirs(project_dir, exist_ok=True)

repo_root = os.getcwd() 

# Copy individual files
all_files_present = True
for item in GIT_FILES_TO_COPY:
    source_path = os.path.join(repo_root, item)
    dest_path = os.path.join(project_dir, item)
    
    if os.path.exists(source_path):
        shutil.copy2(source_path, dest_path)
        
        # --- CRITICAL FIX: SET FILE PERMISSIONS for font ---
        if item.endswith((".ttf", ".otf")):
            # Set the file permission to be globally readable (0o777 grants max access)
            try:
                os.chmod(dest_path, 0o777)
            except Exception as e:
                st.warning(f"Warning: Could not set permissions for font file. {e}")
        # --------------------------------------------------
        
    else:
        st.error(f"FATAL ERROR: Required file not found in Git repository: {item}")
        all_files_present = False

# Copy folders
for item in GIT_DIRS_TO_COPY:
    source_path = os.path.join(repo_root, item)
    dest_path = os.path.join(project_dir, item)
    if os.path.exists(source_path):
        shutil.copytree(source_path, dest_path)
    else:
        st.error(f"FATAL ERROR: Required directory not found in Git repository: {item}")
        all_files_present = False

if not all_files_present:
    st.stop()
else:
    st.success("Project files loaded successfully from the Git repository.")

# --- Continue with the rest of the logic ---

if not os.path.exists(os.path.join(project_dir, "results.xlsx")):
    st.error("Error: results.xlsx not found in project folder!")
    st.stop()

graphics_dir = os.path.join(project_dir, "Graphics")
os.makedirs(graphics_dir, exist_ok=True)

mode = st.selectbox("Select Graphic Type", ["Fixtures", "Match of the Day", "Results", "Table"])

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

if st.button(f"Generate {mode} Graphics"):
    with st.spinner(f"Generating {mode} graphics..."):
        
        # --- CRITICAL FIX: Change CWD to the project folder ---
        original_cwd = os.getcwd()
        os.chdir(project_dir) # Change CWD to the folder containing the font and excel file
        
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            
            # --- FINAL FIX: Use the simple filename (selected_script)
            # This avoids the duplicated path error since CWD is already set to project_dir
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
        # We must use the full path to graphics_dir here as CWD is back to original
        png_files = glob.glob(os.path.join(graphics_dir, "*.png"))
        
        if png_files:
            st.write("**Download Generated Graphics:**")
            for png in png_files:
                with open(png, "rb") as f:
                    st.download_button(
                        label=f"Download {os.path.basename(png)}",
                        data=f,
                        file_name=os.path.basename(png),
                        mime="image/png"
                    )
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