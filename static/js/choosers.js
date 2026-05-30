// Chooser modal helpers

function selectImage(field, imageId, title, url) {
    const input = document.getElementById('input-' + field) || document.querySelector(`[name="${field}"]`);
    if (input) input.value = imageId;
    const preview = document.getElementById('preview-' + field);
    if (preview) {
        preview.innerHTML = `
            <img src="${url}" alt="${title}" class="w-32 h-32 object-cover rounded-lg border">
            <p class="text-xs text-gray-500 mt-1">${title}</p>
        `;
    }
}

function selectDocument(field, docId, title) {
    const input = document.getElementById('input-' + field) || document.querySelector(`[name="${field}"]`);
    if (input) input.value = docId;
    const display = document.getElementById('display-' + field);
    if (display) display.textContent = title;
}

function selectPage(field, pageId, title) {
    const input = document.getElementById('input-' + field) || document.querySelector(`[name="${field}"]`);
    if (input) input.value = pageId;
    const display = document.getElementById('display-' + field);
    if (display) display.textContent = title;
}

// Close modal on Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.getElementById('modal-container').innerHTML = '';
    }
});
