const gallery = document.querySelector('.gallery');

gallery.addEventListener('click', e => {
    if(e.target.tagName === 'IMG' || e.target.tagName === 'VIDEO'){
        const overlay = document.createElement('div');
        overlay.className = 'overlay';
        if(e.target.tagName === 'IMG'){
            overlay.innerHTML = `<img src="${e.target.src}">`;
        } else {
            overlay.innerHTML = `<video src="${e.target.src}" controls autoplay></video>`;
        }
        document.body.appendChild(overlay);

        overlay.addEventListener('click', () => overlay.remove());
    }
});
