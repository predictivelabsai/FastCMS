import json, secrets
from fasthtml.common import *

def new_block_id():
    return secrets.token_hex(4)

BLOCK_TYPES = {}

def register_block(type_name, label, icon, edit_fn, render_fn):
    BLOCK_TYPES[type_name] = {'label': label, 'icon': icon, 'edit_fn': edit_fn, 'render_fn': render_fn}

# ── Block edit forms ──────────────────────────────────────────────────

def _heading_edit(block, idx, field):
    v = block.get('value', {})
    return Div(
        Div(
            Select(
                Option("H2", value="2", selected=str(v.get('level', 2)) == '2'),
                Option("H3", value="3", selected=str(v.get('level', 2)) == '3'),
                Option("H4", value="4", selected=str(v.get('level', 2)) == '4'),
                name=f'{field}_block_{idx}_level',
                cls="px-2 py-1 border border-gray-300 rounded text-sm mr-2"
            ),
            Input(type='text', name=f'{field}_block_{idx}_text', value=v.get('text', ''),
                  placeholder='Heading text', cls="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg text-sm"),
            cls="flex items-center"
        ),
    )

def _paragraph_edit(block, idx, field):
    v = block.get('value', {})
    input_id = f'rt-{field}-block-{idx}'
    return Div(
        Input(type='hidden', id=input_id, name=f'{field}_block_{idx}_text', value=v.get('text', '')),
        NotStr(f'<trix-editor input="{input_id}" class="trix-content border border-gray-300 rounded-lg min-h-[120px] text-sm"></trix-editor>'),
    )

def _image_edit(block, idx, field):
    v = block.get('value', {})
    return Div(
        Div(
            Input(type='number', name=f'{field}_block_{idx}_image_id', value=str(v.get('image_id', 0)),
                  cls="w-20 px-2 py-1 border border-gray-300 rounded text-sm mr-2"),
            Button("Choose", type="button",
                   hx_get=f"/admin/images/chooser/?field={field}_block_{idx}_image_id",
                   hx_target="#modal-container", hx_swap="innerHTML",
                   cls="px-3 py-1 text-xs border border-gray-300 rounded hover:bg-gray-50"),
            cls="flex items-center mb-2"
        ),
        Input(type='text', name=f'{field}_block_{idx}_caption', value=v.get('caption', ''),
              placeholder='Caption', cls="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm mb-1"),
        Input(type='text', name=f'{field}_block_{idx}_alt', value=v.get('alt', ''),
              placeholder='Alt text', cls="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm"),
    )

def _embed_edit(block, idx, field):
    v = block.get('value', {})
    return Div(
        Input(type='url', name=f'{field}_block_{idx}_url', value=v.get('url', ''),
              placeholder='URL (YouTube, Vimeo, etc.)', cls="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm mb-2"),
        Textarea(v.get('html', ''), name=f'{field}_block_{idx}_html', rows=3,
                 placeholder='Embed HTML (paste from provider)',
                 cls="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm"),
    )

def _quote_edit(block, idx, field):
    v = block.get('value', {})
    return Div(
        Textarea(v.get('text', ''), name=f'{field}_block_{idx}_text', rows=3,
                 placeholder='Quote text', cls="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm mb-2"),
        Input(type='text', name=f'{field}_block_{idx}_attribution', value=v.get('attribution', ''),
              placeholder='Attribution', cls="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm"),
    )

def _code_edit(block, idx, field):
    v = block.get('value', {})
    return Div(
        Select(
            *[Option(lang, value=lang, selected=v.get('language', '') == lang)
              for lang in ['', 'python', 'javascript', 'html', 'css', 'bash', 'sql', 'json']],
            name=f'{field}_block_{idx}_language',
            cls="px-2 py-1 border border-gray-300 rounded text-sm mb-2"
        ),
        Textarea(v.get('code', ''), name=f'{field}_block_{idx}_code', rows=6,
                 cls="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm font-mono"),
    )

def _list_edit(block, idx, field):
    v = block.get('value', {})
    items = v.get('items', [''])
    return Div(
        Select(
            Option("Unordered", value="ul", selected=v.get('style', 'ul') == 'ul'),
            Option("Ordered", value="ol", selected=v.get('style', 'ul') == 'ol'),
            name=f'{field}_block_{idx}_style',
            cls="px-2 py-1 border border-gray-300 rounded text-sm mb-2"
        ),
        Textarea('\n'.join(items), name=f'{field}_block_{idx}_items', rows=4,
                 placeholder='One item per line',
                 cls="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm"),
    )

def _table_edit(block, idx, field):
    v = block.get('value', {})
    headers = '|'.join(v.get('headers', []))
    rows_text = '\n'.join('|'.join(row) for row in v.get('rows', []))
    return Div(
        Input(type='text', name=f'{field}_block_{idx}_headers', value=headers,
              placeholder='Headers (pipe-separated: Col1|Col2|Col3)',
              cls="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm mb-2"),
        Textarea(rows_text, name=f'{field}_block_{idx}_rows', rows=4,
                 placeholder='Rows (pipe-separated, one row per line)',
                 cls="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm"),
    )

def _document_edit(block, idx, field):
    v = block.get('value', {})
    return Div(
        Input(type='number', name=f'{field}_block_{idx}_document_id', value=str(v.get('document_id', 0)),
              cls="w-20 px-2 py-1 border border-gray-300 rounded text-sm mr-2"),
        Input(type='text', name=f'{field}_block_{idx}_description', value=v.get('description', ''),
              placeholder='Description', cls="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg text-sm"),
        cls="flex items-center gap-2"
    )

def _raw_html_edit(block, idx, field):
    v = block.get('value', {})
    return Div(
        Textarea(v.get('html', ''), name=f'{field}_block_{idx}_html', rows=6,
                 placeholder='Raw HTML', cls="w-full px-3 py-1.5 border border-gray-300 rounded-lg text-sm font-mono"),
    )

# ── Block renderers (public) ─────────────────────────────────────────

def _heading_render(v):
    level = int(v.get('level', 2))
    tag = {2: H2, 3: H3, 4: H4}.get(level, H2)
    return tag(v.get('text', ''), cls="font-semibold mt-6 mb-3")

def _paragraph_render(v):
    return Div(NotStr(v.get('text', '')), cls="prose mb-4")

def _image_render(v):
    from app.db import images as img_table
    try:
        img = img_table[int(v.get('image_id', 0))]
        return Figure(
            Img(src=f'/media/images/{img.file_path}', alt=v.get('alt', img.alt_text), cls="rounded-lg w-full"),
            Figcaption(v.get('caption', ''), cls="text-sm text-gray-500 mt-2 text-center") if v.get('caption') else '',
            cls="my-6"
        )
    except:
        return ''

def _embed_render(v):
    html = v.get('html', '')
    if html:
        return Div(NotStr(html), cls="my-6 aspect-video")
    return ''

def _quote_render(v):
    return Blockquote(
        P(v.get('text', ''), cls="text-lg italic"),
        Cite(f"— {v['attribution']}", cls="text-sm text-gray-500 mt-2 block") if v.get('attribution') else '',
        cls="border-l-4 border-accent pl-4 my-6"
    )

def _code_render(v):
    lang = v.get('language', '')
    return Pre(Code(v.get('code', ''), cls=f"language-{lang}" if lang else ''),
               cls="bg-gray-900 text-gray-100 rounded-lg p-4 my-6 overflow-x-auto text-sm")

def _list_render(v):
    items = v.get('items', [])
    tag = Ul if v.get('style', 'ul') == 'ul' else Ol
    return tag(*[Li(item) for item in items], cls="list-disc ml-6 my-4 space-y-1" if v.get('style') == 'ul' else "list-decimal ml-6 my-4 space-y-1")

def _table_render(v):
    headers = v.get('headers', [])
    rows = v.get('rows', [])
    return Div(
        Table(
            Thead(Tr(*[Th(h, cls="px-4 py-2 text-left text-sm font-medium text-gray-700 bg-gray-50") for h in headers])) if headers else '',
            Tbody(*[Tr(*[Td(cell, cls="px-4 py-2 text-sm border-t") for cell in row]) for row in rows]),
            cls="w-full border border-gray-200 rounded-lg overflow-hidden"
        ),
        cls="my-6 overflow-x-auto"
    )

def _document_render(v):
    from app.db import documents as doc_table
    try:
        doc = doc_table[int(v.get('document_id', 0))]
        return Div(
            A(f"📎 {doc.title}", href=f'/media/documents/{doc.file_path}', target="_blank",
              cls="text-accent hover:underline"),
            P(v.get('description', ''), cls="text-sm text-gray-500") if v.get('description') else '',
            cls="my-4 p-3 bg-gray-50 rounded-lg"
        )
    except:
        return ''

def _raw_html_render(v):
    return Div(NotStr(v.get('html', '')), cls="my-4")

# ── Register all block types ─────────────────────────────────────────

register_block('heading', 'Heading', 'H', _heading_edit, _heading_render)
register_block('paragraph', 'Paragraph', '¶', _paragraph_edit, _paragraph_render)
register_block('image', 'Image', '🖼', _image_edit, _image_render)
register_block('embed', 'Embed', '▶', _embed_edit, _embed_render)
register_block('quote', 'Quote', '"', _quote_edit, _quote_render)
register_block('code', 'Code', '<>', _code_edit, _code_render)
register_block('list', 'List', '≡', _list_edit, _list_render)
register_block('table', 'Table', '⊞', _table_edit, _table_render)
register_block('document', 'Document', '📎', _document_edit, _document_render)
register_block('raw_html', 'Raw HTML', '{}', _raw_html_edit, _raw_html_render)

# ── Block editor composite ───────────────────────────────────────────

def block_edit_form(block, idx, field):
    btype = block.get('type', 'paragraph')
    info = BLOCK_TYPES.get(btype)
    if not info: return ''
    return Div(
        Div(
            Span('⋮⋮', cls="cursor-grab text-gray-300 mr-2 drag-handle"),
            Span(info['icon'], cls="mr-1 text-xs"),
            Span(info['label'], cls="text-xs font-medium text-gray-500"),
            Button('✕', type='button',
                   onclick=f"this.closest('[data-block]').remove()",
                   cls="ml-auto text-gray-300 hover:text-red-500 text-sm"),
            cls="flex items-center px-3 py-2 bg-gray-50 rounded-t-lg border-b border-gray-200"
        ),
        Div(
            Input(type='hidden', name=f'{field}_block_{idx}_type', value=btype),
            Input(type='hidden', name=f'{field}_block_{idx}_id', value=block.get('id', new_block_id())),
            info['edit_fn'](block, idx, field),
            cls="p-3"
        ),
        cls="border border-gray-200 rounded-lg mb-2",
        data_block=str(idx),
    )

def blocks_editor(field, blocks_json_str):
    try:
        blocks = json.loads(blocks_json_str) if blocks_json_str else []
    except:
        blocks = []

    block_forms = [block_edit_form(b, i, field) for i, b in enumerate(blocks)]

    chooser_items = [
        Button(
            Span(info['icon'], cls="mr-2"),
            info['label'],
            type='button',
            onclick=f"addBlock('{field}', '{btype}')",
            cls="block w-full text-left px-3 py-2 text-sm hover:bg-accent-dim rounded transition-colors"
        )
        for btype, info in BLOCK_TYPES.items()
    ]

    return Div(
        Label("Body", cls="block text-sm font-medium text-gray-700 mb-2"),
        Input(type='hidden', name=f'{field}_block_count', value=str(len(blocks))),
        Div(*block_forms, cls="space-y-0", id=f"block-list-{field}", data_field=field),
        Div(
            Button("+ Add Block", type="button",
                   onclick="this.nextElementSibling.classList.toggle('hidden')",
                   cls="px-4 py-2 text-sm border border-dashed border-gray-300 rounded-lg w-full hover:border-accent hover:text-accent transition-colors"),
            Div(*chooser_items, cls="hidden mt-1 bg-white border border-gray-200 rounded-lg shadow-lg p-2 max-h-64 overflow-y-auto"),
            cls="mt-2"
        ),
        cls="mb-6"
    )

def block_add_html(field, block_type, idx):
    block = {'type': block_type, 'value': {}, 'id': new_block_id()}
    return block_edit_form(block, idx, field)

# ── Parse blocks from form submission ─────────────────────────────────

def parse_blocks_from_form(form_data, field):
    count = int(form_data.get(f'{field}_block_count', 0))
    blocks = []
    for i in range(count):
        btype = form_data.get(f'{field}_block_{i}_type')
        if not btype: continue
        block_id = form_data.get(f'{field}_block_{i}_id', new_block_id())
        value = _parse_block_value(btype, i, field, form_data)
        blocks.append({'type': btype, 'value': value, 'id': block_id})
    return json.dumps(blocks)

def _parse_block_value(btype, idx, field, data):
    prefix = f'{field}_block_{idx}_'
    if btype == 'heading':
        return {'text': data.get(prefix + 'text', ''), 'level': int(data.get(prefix + 'level', 2))}
    elif btype == 'paragraph':
        return {'text': data.get(prefix + 'text', '')}
    elif btype == 'image':
        return {'image_id': int(data.get(prefix + 'image_id', 0)),
                'caption': data.get(prefix + 'caption', ''), 'alt': data.get(prefix + 'alt', '')}
    elif btype == 'embed':
        return {'url': data.get(prefix + 'url', ''), 'html': data.get(prefix + 'html', '')}
    elif btype == 'quote':
        return {'text': data.get(prefix + 'text', ''), 'attribution': data.get(prefix + 'attribution', '')}
    elif btype == 'code':
        return {'code': data.get(prefix + 'code', ''), 'language': data.get(prefix + 'language', '')}
    elif btype == 'list':
        items_text = data.get(prefix + 'items', '')
        return {'items': [l.strip() for l in items_text.split('\n') if l.strip()],
                'style': data.get(prefix + 'style', 'ul')}
    elif btype == 'table':
        headers = [h.strip() for h in data.get(prefix + 'headers', '').split('|') if h.strip()]
        rows_text = data.get(prefix + 'rows', '')
        rows = [[c.strip() for c in line.split('|')] for line in rows_text.split('\n') if line.strip()]
        return {'headers': headers, 'rows': rows}
    elif btype == 'document':
        return {'document_id': int(data.get(prefix + 'document_id', 0)),
                'description': data.get(prefix + 'description', '')}
    elif btype == 'raw_html':
        return {'html': data.get(prefix + 'html', '')}
    return {}

# ── Render blocks (public) ───────────────────────────────────────────

def render_blocks(blocks_json_str):
    try:
        blocks = json.loads(blocks_json_str) if blocks_json_str else []
    except:
        blocks = []
    rendered = []
    for block in blocks:
        btype = block.get('type')
        info = BLOCK_TYPES.get(btype)
        if info:
            result = info['render_fn'](block.get('value', {}))
            if result:
                rendered.append(result)
    return rendered

def extract_text_from_blocks(blocks_json_str):
    import re
    try:
        blocks = json.loads(blocks_json_str) if blocks_json_str else []
    except:
        return ''
    texts = []
    for block in blocks:
        v = block.get('value', {})
        for key in ('text', 'code', 'description', 'html'):
            if key in v and v[key]:
                clean = re.sub(r'<[^>]+>', '', str(v[key]))
                texts.append(clean)
        if 'items' in v:
            texts.extend(v['items'])
    return ' '.join(texts)
