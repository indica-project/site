from flask import Flask, render_template, request, jsonify
import os
import math
import time
import re

app = Flask(__name__)

# Абсолютный путь
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_FOLDER = os.path.join(BASE_DIR, r'C:\Users\callm\OneDrive\Indica\Site\v3\static\images')
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

def extract_tags_from_filename(filename):
    """
    Извлекает теги из названия файла.
    Пример: 'GenshinImpact_Varesa (10).png' → ['GenshinImpact', 'Varesa']
    Игнорирует: цифры, скобки (), фигурные скобки {}, квадратные скобки []
    """
    # Убираем расширение файла
    name_without_ext = os.path.splitext(filename)[0]
    
    # Убираем цифры и специальные символы в конце (включая скобки)
    # Регулярное выражение удаляет: любые символы, затем цифры в скобках или без
    name_clean = re.sub(r'[_\-\s]*[\[{(]?\d+[\]})]?$', '', name_without_ext)
    
    # Удаляем все скобки и их содержимое из середины строки
    name_clean = re.sub(r'[\[{(].*?[\]})]', '', name_clean)
    
    # Разделяем по подчеркиваниям, дефисам и пробелам
    parts = re.split(r'[_-]+', name_clean)
    
    # Фильтруем пустые строки и оставляем только слова с буквами
    tags = []
    for part in parts:
        if part and any(c.isalpha() for c in part):
            # Убираем все цифры и оставшиеся специальные символы
            clean_part = re.sub(r'[\d\[\]{}()]', '', part)
            # Убираем точки и другие спецсимволы в начале/конце
            clean_part = clean_part.strip('.,!?@#$%^&*+=')
            if clean_part:  # Проверяем, не пустая ли строка после очистки
                tags.append(clean_part)
    
    return tags

def get_sorted_files_with_tags():
    """Get sorted files by REAL creation/modification time with tags"""
    files_with_info = []
    
    for filename in os.listdir(IMAGE_FOLDER):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.mp4', '.webm', '.mov', '.avi')):
            filepath = os.path.join(IMAGE_FOLDER, filename)
            creation_time = get_file_creation_time(filepath)
            tags = extract_tags_from_filename(filename)
            
            files_with_info.append({
                'filename': filename,
                'creation_time': creation_time,
                'tags': tags,
                'display_name': ' '.join(tags) if tags else filename,
                'is_image': filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')),
                'is_video': filename.lower().endswith(('.mp4', '.webm', '.mov', '.avi'))
            })
    
    # Сортируем по времени (новые первыми)
    files_with_info.sort(key=lambda x: x['creation_time'], reverse=True)
    
    return files_with_info

def get_all_unique_tags(files):
    """Получает все уникальные теги из списка файлов"""
    all_tags = set()
    for file_info in files:
        all_tags.update(file_info['tags'])
    return sorted(list(all_tags))

def filter_files_by_tags(files, selected_tags):
    """Фильтрует файлы по выбранным тегам"""
    if not selected_tags:
        return files
    
    filtered_files = []
    for file_info in files:
        # Проверяем, содержит ли файл ВСЕ выбранные теги
        if all(tag in file_info['tags'] for tag in selected_tags):
            filtered_files.append(file_info)
    
    return filtered_files

def get_sorted_files():
    """Get sorted files by REAL creation/modification time (старая функция для обратной совместимости)"""
    files_with_info = get_sorted_files_with_tags()
    return [file_info['filename'] for file_info in files_with_info]

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/images')
def images():
    """Images only with tag filtering"""
    page = request.args.get('page', 1, type=int)
    selected_tags = request.args.getlist('tag')
    
    # Получаем все файлы с информацией
    all_files_info = get_sorted_files_with_tags()
    
    # Фильтруем только изображения
    images_info = [f for f in all_files_info if f['is_image']]
    
    # Применяем фильтр по тегам
    if selected_tags:
        images_info = filter_files_by_tags(images_info, selected_tags)
    
    # Получаем все уникальные теги для фильтров (только из изображений)
    all_tags = get_all_unique_tags(images_info)
    
    # Пагинация
    total_pages = math.ceil(len(images_info) / ITEMS_PER_PAGE)
    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    paginated_images = images_info[start_idx:end_idx]
    
    # Получаем только имена файлов для обратной совместимости
    paginated_filenames = [img['filename'] for img in paginated_images]
    
    return render_template('gallery.html', 
                         files=paginated_filenames,
                         files_info=paginated_images,  # Новая переменная с полной информацией
                         title="Images",
                         page_type="images",
                         current_page=page,
                         total_pages=total_pages,
                         total_items=len(images_info),
                         all_tags=all_tags,
                         selected_tags=selected_tags)

@app.route('/videos')
def videos():
    """Videos only with tag filtering"""
    page = request.args.get('page', 1, type=int)
    selected_tags = request.args.getlist('tag')
    
    # Получаем все файлы с информацией
    all_files_info = get_sorted_files_with_tags()
    
    # Фильтруем только видео
    videos_info = [f for f in all_files_info if f['is_video']]
    
    # Применяем фильтр по тегам
    if selected_tags:
        videos_info = filter_files_by_tags(videos_info, selected_tags)
    
    # Получаем все уникальные теги для фильтров (только из видео)
    all_tags = get_all_unique_tags(videos_info)
    
    # Пагинация
    total_pages = math.ceil(len(videos_info) / ITEMS_PER_PAGE)
    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    paginated_videos = videos_info[start_idx:end_idx]
    
    # Получаем только имена файлов для обратной совместимости
    paginated_filenames = [vid['filename'] for vid in paginated_videos]
    
    return render_template('gallery.html', 
                         files=paginated_filenames,
                         files_info=paginated_videos,  # Новая переменная с полной информацией
                         title="Videos",
                         page_type="videos",
                         current_page=page,
                         total_pages=total_pages,
                         total_items=len(videos_info),
                         all_tags=all_tags,
                         selected_tags=selected_tags)

@app.route('/all')
def all_media():
    """All media (images + videos) with tag filtering"""
    page = request.args.get('page', 1, type=int)
    selected_tags = request.args.getlist('tag')
    
    # Получаем все файлы с информацией
    all_files_info = get_sorted_files_with_tags()
    
    # Применяем фильтр по тегам
    if selected_tags:
        all_files_info = filter_files_by_tags(all_files_info, selected_tags)
    
    # Получаем все уникальные теги для фильтров
    all_tags = get_all_unique_tags(all_files_info)
    
    # Пагинация
    total_pages = math.ceil(len(all_files_info) / ITEMS_PER_PAGE)
    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    paginated_files = all_files_info[start_idx:end_idx]
    
    # Получаем только имена файлов для обратной совместимости
    paginated_filenames = [file['filename'] for file in paginated_files]
    
    return render_template('gallery.html', 
                         files=paginated_filenames,
                         files_info=paginated_files,  # Новая переменная с полной информацией
                         title="All Media",
                         page_type="all",
                         current_page=page,
                         total_pages=total_pages,
                         total_items=len(all_files_info),
                         all_tags=all_tags,
                         selected_tags=selected_tags)

@app.route('/api/tags')
def api_tags():
    """API для получения всех тегов"""
    all_files_info = get_sorted_files_with_tags()
    all_tags = get_all_unique_tags(all_files_info)
    return jsonify({'tags': all_tags})

@app.route('/api/filter')
def api_filter():
    """API для фильтрации файлов по тегам"""
    selected_tags = request.args.getlist('tag')
    media_type = request.args.get('type', 'all')  # 'images', 'videos', 'all'
    
    all_files_info = get_sorted_files_with_tags()
    
    # Фильтруем по типу медиа
    if media_type == 'images':
        filtered_files = [f for f in all_files_info if f['is_image']]
    elif media_type == 'videos':
        filtered_files = [f for f in all_files_info if f['is_video']]
    else:
        filtered_files = all_files_info
    
    # Применяем фильтр по тегам
    if selected_tags:
        filtered_files = filter_files_by_tags(filtered_files, selected_tags)
    
    # Подготавливаем ответ
    result = []
    for file_info in filtered_files:
        result.append({
            'filename': file_info['filename'],
            'tags': file_info['tags'],
            'display_name': file_info['display_name'],
            'is_image': file_info['is_image'],
            'is_video': file_info['is_video']
        })
    
    return jsonify({
        'files': result[:100],  # Ограничиваем количество для производительности
        'total': len(filtered_files)
    })

if __name__ == '__main__':
    app.run(debug=True)
