import os
from flask import Flask, render_template, request, send_file

app = Flask(__name__)

def list_files(directory):
    files = []
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):
            files.append(filename)
    return files

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    selected_files = request.form.getlist('file')

    for file in selected_files:
        filepath = os.path.join(request.form['folder'], file)
        return send_file(filepath, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)





new changes

from flask import Flask, render_template, request, send_from_directory
import os

app = Flask(__name__)

# Function to list files in a directory
def list_files(directory):
    return [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        nas_path = request.form['nas_path']
        selected_files = request.form.getlist('files')

        # Logic to download files from NAS path
        # You'll need to implement this part based on your NAS setup
        
        # For demonstration, let's assume we have the list of files selected by the user
        files_to_download = selected_files

        # Move files to Windows download folder
        for file in files_to_download:
            src = os.path.join(nas_path, file)
            dst = os.path.join(os.path.expanduser('~'), 'Downloads', file)
            os.system(f'copy "{src}" "{dst}"')

    # Get list of files in NAS path (for demonstration)
    nas_files = list_files('/path/to/nas')  # Update with your NAS path

    return render_template('index.html', nas_files=nas_files)

if __name__ == '__main__':
    app.run(debug=True)