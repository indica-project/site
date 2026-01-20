from flask import Flask, render_template, request, jsonify
import os
import math
import time
import re
import json
from datetime import datetime, timedelta

app = Flask(__name__)

# Абсолютный путь
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_FOLDER = os.path.join(BASE_DIR, 'static/images')
ITEMS_PER_PAGE = 20

# Файл для хранения лайков
LIKES_FILE = os.path.join(BASE_DIR, 'likes.json')

# Создаем папку если не существует
os.makedirs(IMAGE_FOLDER, exist_ok=True)

def load_likes():
    """Загружает данные о лайках из файла"""
    try:
        if os.path.exists(LIKES_FILE):
            with open(LIKES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading likes: {e}")
    return {"likes": {}, "ip_timestamps": {}}

def save_likes(data):
    """Сохраняет данные о лайках в файл"""
    try:
        with open(LIKES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving likes: {e}")
        return False

def can_like(ip_address):
    """Проверяет может ли IP поставить лайк (только 1 в час)"""
    likes_data = load_likes()
    ip_timestamps = likes_data.get("ip_timestamps", {})
    
    if ip_address in ip_timestamps:
        last_like_time = datetime.fromisoformat(ip_timestamps[ip_address])
        if datetime.now() - last_like_time < timedelta(minutes=5):
            return False
    return True

def get_file_likes(filename):
    """Получает количество лайков у файла"""
    likes_data = load_likes()
    return likes_data.get("likes", {}).get(filename, 0)

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
    auto_open = request.args.get('auto_open', None)
    
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
                         selected_tags=selected_tags,
                         auto_open=auto_open)

@app.route('/videos')
def videos():
    """Videos only with tag filtering"""
    page = request.args.get('page', 1, type=int)
    selected_tags = request.args.getlist('tag')
    auto_open = request.args.get('auto_open', None)
    
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
                         selected_tags=selected_tags,
                         auto_open=auto_open)

@app.route('/all')
def all_media():
    """All media (images + videos) with tag filtering"""
    page = request.args.get('page', 1, type=int)
    selected_tags = request.args.getlist('tag')
    auto_open = request.args.get('auto_open', None)
    
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
                         selected_tags=selected_tags,
                         auto_open=auto_open)

@app.route('/view/<filename>')
def view_file(filename):
    """Прямая ссылка на конкретный файл"""
    # Проверяем существует ли файл
    filepath = os.path.join(IMAGE_FOLDER, filename)
    if not os.path.exists(filepath):
        return "File not found", 404
    
    # Получаем информацию о файле
    all_files_info = get_sorted_files_with_tags()
    file_info = next((f for f in all_files_info if f['filename'] == filename), None)
    
    if not file_info:
        return "File not found", 404
    
    # Определяем тип страницы (images, videos, all)
    page_type = 'images' if file_info['is_image'] else 'videos'
    
    # Получаем индекс файла в общем списке
    if page_type == 'images':
        all_files_of_type = [f for f in all_files_info if f['is_image']]
    elif page_type == 'videos':
        all_files_of_type = [f for f in all_files_info if f['is_video']]
    else:
        all_files_of_type = all_files_info
    
    # Находим индекс файла
    try:
        file_index = next(i for i, f in enumerate(all_files_of_type) if f['filename'] == filename)
    except StopIteration:
        file_index = 0
    
    # Вычисляем страницу, на которой находится файл
    page = (file_index // ITEMS_PER_PAGE) + 1
    
    # Получаем файлы для этой страницы
    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    paginated_files = all_files_of_type[start_idx:end_idx]
    paginated_filenames = [f['filename'] for f in paginated_files]
    
    # Получаем все теги
    all_tags = get_all_unique_tags(all_files_of_type)
    
    # Рендерим галерею с указанием конкретного файла для авто-открытия
    return render_template('gallery.html', 
                         files=paginated_filenames,
                         files_info=paginated_files,
                         title=f"View: {filename}",
                         page_type=page_type,
                         current_page=page,
                         total_pages=math.ceil(len(all_files_of_type) / ITEMS_PER_PAGE),
                         total_items=len(all_files_of_type),
                         all_tags=all_tags,
                         selected_tags=[],
                         auto_open=filename)

# API endpoints
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

@app.route('/api/like', methods=['POST'])
def like_file():
    """API для постановки лайка файлу"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'Filename is required'}), 400
        
        # Проверяем существует ли файл
        filepath = os.path.join(IMAGE_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        # Получаем IP адрес
        ip_address = request.remote_addr
        
        # Проверяем может ли пользователь поставить лайк
        if not can_like(ip_address):
            return jsonify({
                'error': 'You can only like one file per hour',
                'can_like': False
            }), 429
        
        # Загружаем текущие лайки
        likes_data = load_likes()
        
        # Обновляем количество лайков для файла
        if filename not in likes_data["likes"]:
            likes_data["likes"][filename] = 1
        else:
            likes_data["likes"][filename] += 1
        
        # Обновляем временную метку для IP
        likes_data["ip_timestamps"][ip_address] = datetime.now().isoformat()
        
        # Сохраняем изменения
        if save_likes(likes_data):
            return jsonify({
                'success': True,
                'likes': likes_data["likes"][filename],
                'can_like': False,
                'message': 'Liked successfully!'
            })
        else:
            return jsonify({'error': 'Failed to save like'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/like/status')
def like_status():
    """API для проверки состояния лайка для файла"""
    filename = request.args.get('filename')
    ip_address = request.remote_addr
    
    if not filename:
        return jsonify({'error': 'Filename is required'}), 400
    
    can_user_like = can_like(ip_address)
    likes_count = get_file_likes(filename)
    
    return jsonify({
        'can_like': can_user_like,
        'likes': likes_count,
        'filename': filename
    })

@app.route('/api/likes/batch', methods=['POST'])
def batch_likes():
    """API для получения информации о лайках для нескольких файлов"""
    try:
        data = request.get_json()
        filenames = data.get('filenames', [])
        
        if not isinstance(filenames, list):
            return jsonify({'error': 'filenames must be a list'}), 400
        
        likes_data = load_likes()
        ip_address = request.remote_addr
        can_user_like = can_like(ip_address)
        
        result = {}
        for filename in filenames:
            result[filename] = {
                'likes': likes_data.get("likes", {}).get(filename, 0),
                'can_like': can_user_like
            }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)


