from flask import Flask, render_template, request
import os
import math
import time

app = Flask(__name__)

# Абсолютный путь
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_FOLDER = os.path.join(BASE_DIR, 'static/images')
ITEMS_PER_PAGE = 20

# Создаем папку если не существует
os.makedirs(IMAGE_FOLDER, exist_ok=True)

def get_file_creation_time(filepath):
    """Получаем реальное время создания файла"""
    try:
        stat = os.stat(filepath)
        
        # Метод 1: st_birthtime - настоящее время создания (если файловая система поддерживает)
        if hasattr(stat, 'st_birthtime'):
            return stat.st_birthtime
        
        # Метод 2: st_mtime - время последнего изменения содержимого
        # Лучше чем st_ctime для сортировки по "когда файл был добавлен"
        return stat.st_mtime
        
    except Exception as e:
        print(f"Ошибка получения времени для {filepath}: {e}")
        return time.time()

def get_sorted_files():
    """Get sorted files by REAL creation/modification time"""
    files_with_time = []
    
    for filename in os.listdir(IMAGE_FOLDER):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.mp4', '.webm', '.mov', '.avi')):
            filepath = os.path.join(IMAGE_FOLDER, filename)
            creation_time = get_file_creation_time(filepath)
            files_with_time.append((filename, creation_time))
    
    # Сортируем по времени (новые первыми)
    files_with_time.sort(key=lambda x: x[1], reverse=True)
    
    # Возвращаем только имена файлов
    return [filename for filename, _ in files_with_time]

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/images')
def images():
    """Images only"""
    page = request.args.get('page', 1, type=int)
    all_files = get_sorted_files()
    images = [f for f in all_files if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
    
    total_pages = math.ceil(len(images) / ITEMS_PER_PAGE)
    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    paginated_images = images[start_idx:end_idx]
    
    return render_template('gallery.html', 
                         files=paginated_images,
                         title="Images",
                         page_type="images",
                         current_page=page,
                         total_pages=total_pages,
                         total_items=len(images))

@app.route('/videos')
def videos():
    """Videos only"""
    page = request.args.get('page', 1, type=int)
    all_files = get_sorted_files()
    videos = [f for f in all_files if f.lower().endswith(('.mp4', '.webm', '.mov', '.avi'))]
    
    total_pages = math.ceil(len(videos) / ITEMS_PER_PAGE)
    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    paginated_videos = videos[start_idx:end_idx]
    
    return render_template('gallery.html', 
                         files=paginated_videos,
                         title="Videos",
                         page_type="videos",
                         current_page=page,
                         total_pages=total_pages,
                         total_items=len(videos))

if __name__ == '__main__':
    app.run(debug=True)
