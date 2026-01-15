from flask import Flask, render_template
import os

app = Flask(__name__)

IMAGE_FOLDER = r'D:\Site\v3\static\images'

@app.route('/')
def index():
    files = os.listdir(IMAGE_FOLDER)
    files = [
        f for f in files
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.mp4'))
    ]
    return render_template('index.html', files=files)

if __name__ == '__main__':
    app.run(debug=True)
