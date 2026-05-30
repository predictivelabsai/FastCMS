// Tab switching
function switchTab(idx) {
    document.querySelectorAll('[data-tab]').forEach(btn => {
        btn.classList.toggle('border-accent', btn.dataset.tab == idx);
        btn.classList.toggle('text-accent', btn.dataset.tab == idx);
        btn.classList.toggle('border-transparent', btn.dataset.tab != idx);
        btn.classList.toggle('text-gray-500', btn.dataset.tab != idx);
    });
    document.querySelectorAll('[data-panel]').forEach(panel => {
        panel.classList.toggle('hidden', panel.dataset.panel != idx);
    });
}

// Unsaved changes detection
let formChanged = false;
document.addEventListener('input', () => { formChanged = true; });
document.addEventListener('change', () => { formChanged = true; });
window.addEventListener('beforeunload', (e) => {
    if (formChanged) { e.preventDefault(); e.returnValue = ''; }
});
document.addEventListener('submit', () => { formChanged = false; });

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        const form = document.querySelector('form[method="post"]');
        if (form) form.submit();
    }
});

// Toast auto-dismiss
const observer = new MutationObserver((mutations) => {
    mutations.forEach(m => {
        m.addedNodes.forEach(node => {
            if (node.nodeType === 1 && node.closest('#toast-container')) {
                setTimeout(() => {
                    node.classList.add('animate-fade-out');
                    setTimeout(() => node.remove(), 300);
                }, 4000);
            }
        });
    });
});
const toastContainer = document.getElementById('toast-container');
if (toastContainer) observer.observe(toastContainer, { childList: true });

// Search results visibility
document.addEventListener('htmx:afterSwap', (e) => {
    if (e.detail.target.id === 'search-results') {
        e.detail.target.classList.toggle('hidden', !e.detail.target.innerHTML.trim());
    }
});

// Close search results on outside click
document.addEventListener('click', (e) => {
    const sr = document.getElementById('search-results');
    if (sr && !e.target.closest('.relative')) sr.classList.add('hidden');
});
