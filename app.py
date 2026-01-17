from flask import Flask, render_template, request
import os
import math

app = Flask(__name__)

IMAGE_FOLDER = 'static/images'
ITEMS_PER_PAGE = 20

def get_sorted_files():
    """Get sorted files by REAL creation time"""
    files_with_time = []
    
    for filename in os.listdir(IMAGE_FOLDER):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.mp4', '.webm', '.mov', '.avi')):
            filepath = os.path.join(IMAGE_FOLDER, filename)
            
            # Пытаемся получить настоящее время создания
            try:
                stat = os.stat(filepath)
                
                if hasattr(stat, 'st_birthtime'):
                    creation_time = stat.st_birthtime
                else:
                    creation_time = stat.st_mtime
                    
                files_with_time.append((filename, creation_time))
                
            except Exception as e:
                # Если ошибка, используем текущее время
                print(f"Error for {filename}: {e}")
                files_with_time.append((filename, time.time()))
    
    # Сортируем по времени создания (новые первыми)
    files_with_time.sort(key=lambda x: x[1], reverse=True)
    
    # Возвращаем только имена файлов, отсортированные
    return [filename for filename, _ in files_with_time]

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

