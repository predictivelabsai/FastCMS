// Block editor: add, remove, reorder

function addBlock(field, blockType) {
    const list = document.getElementById('block-list-' + field);
    if (!list) return;
    const count = list.querySelectorAll('[data-block]').length;
    // Update block count
    const countInput = document.querySelector(`[name="${field}_block_count"]`);
    if (countInput) countInput.value = count + 1;
    // Fetch new block HTML via HTMX
    htmx.ajax('GET', `/admin/pages/block/add/?field=${field}&type=${blockType}&idx=${count}`, {
        target: list,
        swap: 'beforeend'
    });
    // Close the chooser menu
    const menu = list.parentElement.querySelector('.hidden');
    if (menu) menu.classList.add('hidden');
}

// Initialize Sortable on block lists
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[id^="block-list-"]').forEach(list => {
        new Sortable(list, {
            handle: '.drag-handle',
            animation: 150,
            ghostClass: 'sortable-ghost',
            chosenClass: 'sortable-chosen',
            onEnd: () => reindexBlocks(list)
        });
    });
});

// Re-initialize after HTMX swaps
document.addEventListener('htmx:afterSwap', () => {
    document.querySelectorAll('[id^="block-list-"]').forEach(list => {
        if (!list._sortable) {
            list._sortable = new Sortable(list, {
                handle: '.drag-handle',
                animation: 150,
                ghostClass: 'sortable-ghost',
                chosenClass: 'sortable-chosen',
                onEnd: () => reindexBlocks(list)
            });
        }
    });
});

function reindexBlocks(list) {
    const field = list.dataset.field;
    const blocks = list.querySelectorAll('[data-block]');
    blocks.forEach((block, i) => {
        block.dataset.block = i;
        // Update all input names within this block
        block.querySelectorAll('[name]').forEach(input => {
            input.name = input.name.replace(/_block_\d+_/, `_block_${i}_`);
        });
        // Update trix editor input IDs
        block.querySelectorAll('[id]').forEach(el => {
            el.id = el.id.replace(/-block-\d+/, `-block-${i}`);
        });
    });
    const countInput = document.querySelector(`[name="${field}_block_count"]`);
    if (countInput) countInput.value = blocks.length;
}
