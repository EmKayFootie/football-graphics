import streamlit as st
import os
import zipfile
import shutil
import subprocess
import glob
import sys # <-- NEW: Import sys to get the correct Python executable path

# Streamlit GUI
st.title("Football Graphics Generator")
st.write("Upload a ZIP file containing results.xlsx, Templates/, Logos/, BebasNeue Regular.ttf, and your scripts (Fixtures - automated.py, match of the day - automated.py, Results - automated.py, table - automated.py).")

# File uploader for ZIP
uploaded_file = st.file_uploader("Choose ZIP file", type="zip")

if uploaded_file:
    # Create project directory
    project_dir = os.path.join("tmp", "project")
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)
    os.makedirs(project_dir, exist_ok=True)

    # Save and unzip the uploaded file
    zip_path = os.path.join(project_dir, "input.zip")
    try:
        with open(zip_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(project_dir)
        st.success("ZIP file uploaded and extracted successfully!")
    except Exception as e:
        st.error(f"Error extracting ZIP: {e}")
        st.stop()

    # Search for scripts and excel in project_dir and subdirectories
    script_paths = {}
    excel_path = None
    script_names = [
        "Fixtures - automated.py",
        "match of the day - automated.py",
        "Results - automated.py",
        "table - automated.py"
    ]
    for root, _, files in os.walk(project_dir):
        if "results.xlsx" in files:
            excel_path = os.path.join(root, "results.xlsx")
        for script_name in script_names:
            if script_name in files:
                script_paths[script_name] = os.path.join(root, script_name)
    if not excel_path:
        st.error("Error: results.xlsx not found in ZIP or its subfolders!")
        st.stop()
    if not any(script_paths.values()):
        st.error("Error: No scripts found in ZIP! Expected: Fixtures - automated.py, match of the day - automated.py, Results - automated.py, table - automated.py.")
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
        st.error(f"Error: {selected_script} not found in ZIP!")
        st.stop()

    # Button to run the script
    if st.button(f"Generate {mode} Graphics"):
        with st.spinner(f"Generating {mode} graphics..."):
            script_path = script_paths[selected_script]
            # Update paths in script dynamically
            script_content = open(script_path, 'r', encoding='utf-8').read()
            # Use raw strings with os.path.join for paths
            script_content = script_content.replace(
                'FIXTURES_FILE_PATH = r"C:\\Users\\Matt\\Desktop\\Sunday Football\\results.xlsx"',
                f'FIXTURES_FILE_PATH = r"{os.path.normpath(excel_path)}"'
            ).replace(
                'LOGOS_FOLDER = r"C:\\Users\\Matt\\Desktop\\Sunday Football\\Logos"',
                f'LOGOS_FOLDER = r"{os.path.normpath(os.path.join(project_dir, "Logos"))}"'
            ).replace(
                'SAVE_FOLDER = r"C:\\Users\\Matt\\Desktop\\Sunday Football\\Graphics"',
                f'SAVE_FOLDER = r"{os.path.normpath(graphics_dir)}"'
            ).replace(
                'TEMPLATES_FOLDER = r"C:\\Users\\Matt\\Desktop\\Sunday Football\\Templates"',
                f'TEMPLATES_FOLDER = r"{os.path.normpath(os.path.join(project_dir, "Templates"))}"'
            ).replace(
                'FONT_PATH = r"C:\\Users\\Matt\\AppData\\Local\\Microsoft\\Windows\\Fonts\\BebasNeue Regular.ttf"',
                f'FONT_PATH = r"{os.path.normpath(os.path.join(project_dir, "BebasNeue Regular.ttf"))}"'
            ).replace(
                'TEMPLATE_PATH = os.path.join(TEMPLATES_FOLDER, "fixtures_template.png")',
                f'TEMPLATE_PATH = r"{os.path.normpath(os.path.join(project_dir, "Templates", "fixtures_template.png"))}"'
            )
            # Save modified script
            temp_script = os.path.join("tmp", "temp_script.py")
            with open(temp_script, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # Run the script with UTF-8 encoding
            try:
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                
                # *** FIX HERE: Use sys.executable to run Python from the Streamlit virtual environment ***
                result = subprocess.run([sys.executable, temp_script], capture_output=True, text=True, env=env)
                
                st.write("**Console Output:**")
                st.code(result.stdout)
                if result.stderr:
                    st.error(f"**Errors:**\n{result.stderr}")
                else:
                    st.success(f"{mode} graphics generated successfully!")
            except Exception as e:
                st.error(f"Error running script: {e}")

        # Provide download links for generated PNGs and ZIP
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

st.write("Note: Ensure your ZIP contains results.xlsx, Templates/, Logos/, BebasNeue Regular.ttf, and all scripts.")