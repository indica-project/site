from flask import Flask, render_template, request
import os
import math

app = Flask(__name__)

IMAGE_FOLDER = 'static/images'
ITEMS_PER_PAGE = 20

def get_sorted_files():
    """Get sorted files"""
    files = []
    for filename in os.listdir(IMAGE_FOLDER):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.mp4', '.webm', '.mov', '.avi')):
            files.append(filename)
    
    # Sort by creation time (newest first)
    files.sort(key=lambda x: os.path.getctime(os.path.join(IMAGE_FOLDER, x)), reverse=True)
    return files

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
