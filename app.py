import streamlit as st
import os
import shutil
import subprocess
import glob
import sys
import pandas as pd
import zipfile
from datetime import datetime

# --- Configuration for Git Repository Files ---
GIT_FILES_TO_COPY = [
    "match of the day.xlsx",
    "results.xlsx",
    "table.xlsx",
    "Fixtures - automated.py",
    "match of the day - automated.py",
    "Results - automated.py",
    "table - automated.py",
    "BebasNeue Regular.ttf",
    "BebasKai.ttf",
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
        # Set file permissions for font and .xlsx files
        if item.endswith((".ttf", ".otf", ".xlsx")):
            try:
                os.chmod(dest_path, 0o777)
                st.write(f"DEBUG: Copied and set permissions for {item} to {dest_path}")
            except Exception as e:
                st.warning(f"Warning: Could not set permissions for {item}. {e}")
    else:
        st.error(f"FATAL ERROR: Required file not found in Git repository: {item}")
        all_files_present = False

# Copy folders
for item in GIT_DIRS_TO_COPY:
    source_path = os.path.join(repo_root, item)
    dest_path = os.path.join(project_dir, item)
    if os.path.exists(source_path):
        shutil.copytree(source_path, dest_path)
        st.write(f"DEBUG: Copied directory {item} to {dest_path}")
    else:
        st.error(f"FATAL ERROR: Required directory not found in Git repository: {item}")
        all_files_present = False

if not all_files_present:
    st.stop()
else:
    st.success("Project files loaded successfully from the Git repository.")

# --- Download Excel Files Section ---
st.subheader("Download Excel Files for Editing")
xlsx_files = [f for f in os.listdir(project_dir) if f.endswith('.xlsx')]
if not xlsx_files:
    st.warning("No Excel files found in the project directory.")
else:
    for xlsx in xlsx_files:
        xlsx_path = os.path.join(project_dir, xlsx)
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(xlsx_path))
            st.write(f"DEBUG: {xlsx} last modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            with open(xlsx_path, "rb") as f:
                st.download_button(
                    label=f"Download {xlsx}",
                    data=f,
                    file_name=xlsx,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        except Exception as e:
            st.error(f"Error providing download for {xlsx}: {e}")

# --- Upload Updated Excel Files Section ---
st.subheader("Upload Updated Excel Files")
uploaded_files = st.file_uploader("Upload edited .xlsx files (multiple allowed)", type=["xlsx"], accept_multiple_files=True)
if uploaded_files:
    for uploaded_file in uploaded_files:
        try:
            # Validate file name
            if uploaded_file.name not in ["match of the day.xlsx", "results.xlsx", "table.xlsx"]:
                st.warning(f"Warning: {uploaded_file.name} is not a recognized Excel file. It will still be saved.")
            # Save uploaded file to project_dir
            uploaded_path = os.path.join(project_dir, uploaded_file.name)
            with open(uploaded_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            # Set permissions
            os.chmod(uploaded_path, 0o777)
            mtime = datetime.fromtimestamp(os.path.getmtime(uploaded_path))
            st.success(f"Uploaded {uploaded_file.name} to {uploaded_path} (last modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
        except Exception as e:
            st.error(f"Error uploading {uploaded_file.name}: {e}")

# --- Graphic Generation ---
graphics_dir = os.path.join(project_dir, "Graphics")
os.makedirs(graphics_dir, exist_ok=True)
try:
    os.chmod(graphics_dir, 0o777)
    st.write(f"DEBUG: Set permissions for {graphics_dir} to 0o777")
except Exception as e:
    st.warning(f"Warning: Could not set permissions for Graphics folder. {e}")

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
        original_cwd = os.getcwd()
        os.chdir(project_dir)  # Change to tmp/project
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
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
            os.chdir(original_cwd)
    
    # Provide download links for generated PNGs and ZIP
    if os.path.exists(graphics_dir):
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
