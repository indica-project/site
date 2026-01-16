from flask import Flask, render_template
import os

app = Flask(__name__)

IMAGE_FOLDER = 'static/images'

def get_sorted_files():
    """Получает отсортированные файлы"""
    files = []
    for filename in os.listdir(IMAGE_FOLDER):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.mp4', '.webm', '.mov', '.avi')):
            files.append(filename)
    
    # Сортируем по времени создания (новые сверху)
    files.sort(key=lambda x: os.path.getctime(os.path.join(IMAGE_FOLDER, x)), reverse=True)
    return files

@app.route('/')
def index():
    """Главная страница с навигацией"""
    return render_template('index.html')

@app.route('/images')
def images():
    """Страница только с изображениями"""
    all_files = get_sorted_files()
    images = [f for f in all_files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    return render_template('gallery.html', 
                         files=images, 
                         title="Изображения",
                         page_type="images")

@app.route('/videos')
def videos():
    """Страница только с видео"""
    all_files = get_sorted_files()
    videos = [f for f in all_files if f.lower().endswith(('.mp4', '.webm', '.mov', '.avi'))]
    return render_template('gallery.html', 
                         files=videos, 
                         title="Видео",
                         page_type="videos")

@app.route('/all')
def all_content():
    """Все медиа вместе (как было раньше)"""
    files = get_sorted_files()
    return render_template('gallery.html', 
                         files=files, 
                         title="Вся галерея",
                         page_type="all")

if __name__ == '__main__':
    app.run(debug=True)
