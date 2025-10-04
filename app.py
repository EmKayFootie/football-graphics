import streamlit as st
import os
import shutil
import subprocess
import glob
import sys
import pandas as pd
import zipfile

# --- Configuration for Git Repository Files ---
GIT_FILES_TO_COPY = [
    "table.xlsx",
    "results.xlsx",
    "match of the day.xlsx",
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
        # Set file permissions for font
        if item.endswith((".ttf", ".otf")):
            try:
                os.chmod(dest_path, 0o777)
            except Exception as e:
                st.warning(f"Warning: Could not set permissions for font file. {e}")
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

# --- Excel File Editor ---
st.subheader("Edit Excel Files")
# Find all .xlsx files in the project directory
xlsx_files = [f for f in os.listdir(project_dir) if f.endswith('.xlsx')]
if not xlsx_files:
    st.warning("No Excel files found in the project directory.")
else:
    selected_xlsx = st.selectbox("Select Excel File to Edit", xlsx_files)
    if selected_xlsx:
        xlsx_path = os.path.join(project_dir, selected_xlsx)
        try:
            # Read all sheets from the selected Excel file
            xlsx_data = pd.read_excel(xlsx_path, sheet_name=None)
            sheet_names = list(xlsx_data.keys())
            selected_sheet = st.selectbox(f"Select Sheet from {selected_xlsx}", sheet_names)
            
            # Display and edit the selected sheet
            df = xlsx_data[selected_sheet]
            st.write(f"Editing {selected_sheet} from {selected_xlsx}")
            edited_df = st.data_editor(
                df,
                num_rows="dynamic",  # Allow adding/deleting rows
                key=f"editor_{selected_xlsx}_{selected_sheet}"
            )
            
            # Save changes button
            if st.button(f"Save Changes to {selected_xlsx}"):
                try:
                    # Update the selected sheet in the Excel file
                    with pd.ExcelWriter(xlsx_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                        for sheet_name, data in xlsx_data.items():
                            if sheet_name == selected_sheet:
                                edited_df.to_excel(writer, sheet_name=sheet_name, index=False)
                            else:
                                data.to_excel(writer, sheet_name=sheet_name, index=False)
                    st.success(f"Changes saved to {selected_xlsx} ({selected_sheet})")
                except Exception as e:
                    st.error(f"Error saving changes: {e}")
        except Exception as e:
            st.error(f"Error loading {selected_xlsx}: {e}")

# --- Graphic Generation ---
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