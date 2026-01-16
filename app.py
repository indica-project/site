from flask import Flask, render_template
import os

app = Flask(__name__)

IMAGE_FOLDER = 'static/images'

@app.route('/')
def index():
    files = []
    for filename in os.listdir(IMAGE_FOLDER):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.mp4')):
            files.append(filename)
    
    # Сортируем по времени создания (новые сверху)
    files.sort(key=lambda x: os.path.getctime(os.path.join(IMAGE_FOLDER, x)), reverse=False)
    
    return render_template('index.html', files=files)

if __name__ == '__main__':
    app.run(debug=True)

