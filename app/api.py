import json
from fasthtml.common import *
from starlette.responses import JSONResponse
from app.db import pages, images, documents
from app.search import search as fts_search
from app.media import get_rendition_url

def _cors_json(data, status=200):
    return JSONResponse(data, status_code=status,
                       headers={'Access-Control-Allow-Origin': '*',
                                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                                'Access-Control-Allow-Headers': 'Content-Type'})

def api_pages_list(child_of: int = 0, type: str = '', search: str = '',
                   fields: str = '', order: str = '-first_published_at',
                   limit: int = 20, offset: int = 0):
    where_parts = ["live=1"]
    args = []

    if child_of:
        try:
            parent = pages[child_of]
            where_parts.append("path LIKE ? AND depth=?")
            args.extend([parent.path + '%', parent.depth + 1])
        except:
            pass

    if type:
        where_parts.append("content_type=?")
        args.append(type)

    if search:
        where_parts.append("title LIKE ?")
        args.append(f'%{search}%')

    where = ' AND '.join(where_parts)
    order_by = order.lstrip('-')
    if order.startswith('-'):
        order_by += ' DESC'

    all_pages = pages(where=where, where_args=args, order_by=order_by)
    total = len(all_pages)
    items = all_pages[offset:offset + limit]

    result_items = []
    for p in items:
        item = {
            'id': p.id,
            'meta': {
                'type': p.content_type,
                'detail_url': f'/api/v1/pages/{p.id}/',
                'html_url': p.url_path,
                'first_published_at': p.first_published_at,
                'slug': p.slug,
            },
            'title': p.title,
        }
        if not fields or 'body' in fields:
            try: item['body'] = json.loads(p.body_json)
            except: item['body'] = []
        if not fields or 'extra' in fields:
            try: item['extra'] = json.loads(p.extra_json)
            except: item['extra'] = {}
        result_items.append(item)

    return _cors_json({'meta': {'total_count': total}, 'items': result_items})

def api_page_detail(page_id: int):
    try:
        p = pages[page_id]
    except:
        return _cors_json({'error': 'Not found'}, 404)
    if not p.live:
        return _cors_json({'error': 'Not found'}, 404)

    try: body = json.loads(p.body_json)
    except: body = []
    try: extra = json.loads(p.extra_json)
    except: extra = {}

    return _cors_json({
        'id': p.id,
        'meta': {
            'type': p.content_type,
            'html_url': p.url_path,
            'first_published_at': p.first_published_at,
            'last_published_at': p.last_published_at,
            'slug': p.slug,
        },
        'title': p.title,
        'seo_title': p.seo_title,
        'search_description': p.search_description,
        'body': body,
        'extra': extra,
    })

def api_images_list(collection: int = 0, tags: str = '', search: str = '',
                    limit: int = 20, offset: int = 0):
    where_parts = []
    args = []
    if collection:
        where_parts.append("collection_id=?")
        args.append(collection)
    if tags:
        where_parts.append("tags LIKE ?")
        args.append(f'%{tags}%')
    if search:
        where_parts.append("title LIKE ?")
        args.append(f'%{search}%')

    where = ' AND '.join(where_parts) if where_parts else None
    all_imgs = images(where=where, where_args=args if args else None, order_by='created_at DESC')
    total = len(all_imgs)
    items = all_imgs[offset:offset + limit]

    return _cors_json({
        'meta': {'total_count': total},
        'items': [{
            'id': img.id,
            'title': img.title,
            'alt_text': img.alt_text,
            'width': img.width,
            'height': img.height,
            'file_url': f'/media/images/{img.file_path}',
            'renditions': {
                'thumbnail': get_rendition_url(img.id, 'fill-150x150'),
                'medium': get_rendition_url(img.id, 'width-400'),
                'large': get_rendition_url(img.id, 'width-800'),
            },
            'tags': img.tags,
            'created_at': img.created_at,
        } for img in items]
    })

def api_image_detail(image_id: int):
    try:
        img = images[image_id]
    except:
        return _cors_json({'error': 'Not found'}, 404)
    return _cors_json({
        'id': img.id,
        'title': img.title,
        'alt_text': img.alt_text,
        'width': img.width,
        'height': img.height,
        'file_url': f'/media/images/{img.file_path}',
        'file_size': img.file_size,
        'renditions': {
            'thumbnail': get_rendition_url(img.id, 'fill-150x150'),
            'medium': get_rendition_url(img.id, 'width-400'),
            'large': get_rendition_url(img.id, 'width-800'),
        },
        'tags': img.tags,
        'created_at': img.created_at,
    })

def api_documents_list(collection: int = 0, search: str = '',
                       limit: int = 20, offset: int = 0):
    where_parts = []
    args = []
    if collection:
        where_parts.append("collection_id=?")
        args.append(collection)
    if search:
        where_parts.append("title LIKE ?")
        args.append(f'%{search}%')

    where = ' AND '.join(where_parts) if where_parts else None
    all_docs = documents(where=where, where_args=args if args else None, order_by='created_at DESC')
    total = len(all_docs)
    items = all_docs[offset:offset + limit]

    return _cors_json({
        'meta': {'total_count': total},
        'items': [{
            'id': doc.id,
            'title': doc.title,
            'file_url': f'/media/documents/{doc.file_path}',
            'file_ext': doc.file_ext,
            'file_size': doc.file_size,
            'tags': doc.tags,
            'created_at': doc.created_at,
        } for doc in items]
    })

def api_document_detail(doc_id: int):
    try:
        doc = documents[doc_id]
    except:
        return _cors_json({'error': 'Not found'}, 404)
    return _cors_json({
        'id': doc.id,
        'title': doc.title,
        'file_url': f'/media/documents/{doc.file_path}',
        'file_ext': doc.file_ext,
        'file_size': doc.file_size,
        'tags': doc.tags,
        'created_at': doc.created_at,
    })

def api_search(query: str = '', type: str = '', limit: int = 20, offset: int = 0):
    results = fts_search(query, content_type=type or None, limit=limit, offset=offset)
    return _cors_json({'meta': {'total_count': len(results)}, 'items': results})
