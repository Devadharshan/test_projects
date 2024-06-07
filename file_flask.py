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