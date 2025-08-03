
import os
from flask import Flask, request, render_template, send_file, redirect, url_for
from werkzeug.utils import secure_filename
from mapgen import render_map

app = Flask(__name__)
UPLOAD_FOLDER = 'static/gpx'
OUTPUT_FOLDER = 'static/output'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')



    basemap = request.form.get("basemap", "OpenStreetMap.Mapnik")
    image_files = render_map(gpx_paths, output_path=None, basemap=basemap)

    files = request.files.getlist('gpx_files')
    gpx_paths = []

    for file in files:
        if file and file.filename.endswith('.gpx'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            print(f"[DEBUG] Saved GPX file to: {filepath}")
            gpx_paths.append(filepath)

    if not gpx_paths:
        print("[ERROR] No valid GPX files uploaded.")
        return "No valid GPX files uploaded.", 400

    try:
        print(f"[DEBUG] Calling render_map with: {gpx_paths}")
        image_files = render_map(gpx_paths, output_path=None, basemap='OpenStreetMap.Mapnik')
        print(f"[DEBUG] Generated image files: {image_files}")
    except Exception as e:
        print(f"[ERROR] Map generation failed: {e}")
        return "Map generation failed.", 500

    if not image_files:
        return "No PNGs were generated from the provided GPX files.", 500

    image_filenames = [os.path.basename(path) for path in image_files]
    return render_template('result.html', image_files=image_filenames, back_url=url_for('index'))
@app.route('/upload', methods=['POST'])
def upload_gpx():
    files = request.files.getlist('gpx_files')
    gpx_paths = []
    
    # Get selected basemap from form
    basemap = request.form.get("basemap", "OpenStreetMap.Mapnik")

    for file in files:
        if file and file.filename.endswith('.gpx'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            print(f"[DEBUG] Saved GPX file to: {filepath}")
            gpx_paths.append(filepath)

    if not gpx_paths:
        print("[ERROR] No valid GPX files uploaded.")
        return "No valid GPX files uploaded.", 400

    try:
        print(f"[DEBUG] Calling render_map with: {gpx_paths}")
        image_files = render_map(gpx_paths, output_path=None, basemap=basemap)
        print(f"[DEBUG] Generated image files: {image_files}")
    except Exception as e:
        print(f"[ERROR] Map generation failed: {e}")
        return f"Map generation failed: {e}", 500

    if not image_files:
        return "No PNGs were generated from the provided GPX files.", 500

    image_filenames = [os.path.basename(path) for path in image_files]
    return render_template('result.html', image_files=image_filenames, back_url=url_for('index'))

@app.route('/zip-download', methods=['POST'])
def zip_download():
    from zipfile import ZipFile
    from io import BytesIO

    file_names = request.form.getlist('files')
    memory_file = BytesIO()

    with ZipFile(memory_file, 'w') as zf:
        for filename in file_names:
            path = os.path.join(OUTPUT_FOLDER, filename)
            if os.path.exists(path):
                zf.write(path, arcname=filename)

    memory_file.seek(0)
    return send_file(memory_file, download_name='maps.zip', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
