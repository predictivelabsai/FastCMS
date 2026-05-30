import os, json
from PIL import Image as PILImage
from app.db import db, images, renditions, documents, collections, now, file_hash, log_action

MEDIA_PATH = os.getenv('MEDIA_PATH', 'media')
os.makedirs(f'{MEDIA_PATH}/images', exist_ok=True)
os.makedirs(f'{MEDIA_PATH}/renditions', exist_ok=True)
os.makedirs(f'{MEDIA_PATH}/documents', exist_ok=True)

async def save_uploaded_image(file, title, user_id, collection_id=1, alt_text='', tags=''):
    content = await file.read()
    ext = os.path.splitext(file.filename)[1].lower() or '.jpg'
    fhash = file_hash(content)
    fname = f'{fhash}{ext}'
    fpath = f'{MEDIA_PATH}/images/{fname}'
    with open(fpath, 'wb') as f:
        f.write(content)

    img = PILImage.open(fpath)
    w, h = img.size

    return images.insert(
        title=title, file_path=fname, file_hash=fhash,
        file_size=len(content), width=w, height=h,
        alt_text=alt_text, collection_id=collection_id,
        uploaded_by_id=user_id, tags=tags, created_at=now()
    )

async def save_uploaded_document(file, title, user_id, collection_id=1, tags=''):
    content = await file.read()
    ext = os.path.splitext(file.filename)[1].lower()
    fhash = file_hash(content)
    fname = f'{fhash}{ext}'
    fpath = f'{MEDIA_PATH}/documents/{fname}'
    with open(fpath, 'wb') as f:
        f.write(content)

    return documents.insert(
        title=title, file_path=fname, file_hash=fhash,
        file_size=len(content), file_ext=ext,
        collection_id=collection_id, uploaded_by_id=user_id,
        tags=tags, created_at=now()
    )

def generate_rendition(image_id, filter_spec):
    existing = renditions(where="image_id=? AND filter_spec=?", where_args=[image_id, filter_spec])
    if existing:
        return existing[0]

    img_record = images[image_id]
    src_path = f'{MEDIA_PATH}/images/{img_record.file_path}'
    if not os.path.exists(src_path):
        return None

    pil_img = PILImage.open(src_path)
    if pil_img.mode in ('RGBA', 'P'):
        pil_img = pil_img.convert('RGB')

    op, w, h = parse_filter_spec(filter_spec)
    pil_img = apply_filter(pil_img, op, w, h, img_record.focal_point_x, img_record.focal_point_y)

    ext = os.path.splitext(img_record.file_path)[1] or '.jpg'
    rend_fname = f'{img_record.file_hash}_{filter_spec}{ext}'
    rend_path = f'{MEDIA_PATH}/renditions/{rend_fname}'
    pil_img.save(rend_path, quality=85)

    rw, rh = pil_img.size
    return renditions.insert(
        image_id=image_id, filter_spec=filter_spec,
        file_path=rend_fname, width=rw, height=rh
    )

def get_rendition_url(image_id, filter_spec):
    rend = generate_rendition(image_id, filter_spec)
    if rend:
        return f'/media/renditions/{rend.file_path}'
    img = images[image_id]
    return f'/media/images/{img.file_path}'

def parse_filter_spec(spec):
    if spec.startswith('width-'):
        return ('width', int(spec[6:]), 0)
    elif spec.startswith('height-'):
        return ('height', 0, int(spec[7:]))
    elif spec.startswith('fill-'):
        parts = spec[5:].split('x')
        return ('fill', int(parts[0]), int(parts[1]))
    elif spec.startswith('max-'):
        parts = spec[4:].split('x')
        return ('max', int(parts[0]), int(parts[1]))
    return ('width', 400, 0)

def apply_filter(pil_img, op, w, h, focal_x=0.5, focal_y=0.5):
    orig_w, orig_h = pil_img.size
    if op == 'width' and w:
        ratio = w / orig_w
        new_h = int(orig_h * ratio)
        pil_img = pil_img.resize((w, new_h), PILImage.LANCZOS)
    elif op == 'height' and h:
        ratio = h / orig_h
        new_w = int(orig_w * ratio)
        pil_img = pil_img.resize((new_w, h), PILImage.LANCZOS)
    elif op == 'fill' and w and h:
        target_ratio = w / h
        orig_ratio = orig_w / orig_h
        if orig_ratio > target_ratio:
            new_h = orig_h
            new_w = int(new_h * target_ratio)
        else:
            new_w = orig_w
            new_h = int(new_w / target_ratio)
        left = int((orig_w - new_w) * focal_x)
        top = int((orig_h - new_h) * focal_y)
        left = max(0, min(left, orig_w - new_w))
        top = max(0, min(top, orig_h - new_h))
        pil_img = pil_img.crop((left, top, left + new_w, top + new_h))
        pil_img = pil_img.resize((w, h), PILImage.LANCZOS)
    elif op == 'max' and w and h:
        pil_img.thumbnail((w, h), PILImage.LANCZOS)
    return pil_img

def delete_image(image_id, user_id=0):
    img = images[image_id]
    fpath = f'{MEDIA_PATH}/images/{img.file_path}'
    if os.path.exists(fpath):
        os.remove(fpath)
    for rend in renditions(where="image_id=?", where_args=[image_id]):
        rpath = f'{MEDIA_PATH}/renditions/{rend.file_path}'
        if os.path.exists(rpath):
            os.remove(rpath)
        renditions.delete(rend.id)
    images.delete(image_id)
    log_action(user_id, 'delete', 'image', image_id, img.title)

def delete_document(doc_id, user_id=0):
    doc = documents[doc_id]
    fpath = f'{MEDIA_PATH}/documents/{doc.file_path}'
    if os.path.exists(fpath):
        os.remove(fpath)
    documents.delete(doc_id)
    log_action(user_id, 'delete', 'document', doc_id, doc.title)

def get_image_usage(image_id):
    from app.db import pages
    usage = []
    for p in pages():
        if str(image_id) in (p.body_json or '') or str(image_id) in (p.extra_json or ''):
            usage.append(p)
    return usage

def get_collection_tree():
    return collections(order_by='path')

def create_collection(name, parent_id=0):
    if parent_id:
        parent = collections[parent_id]
        path_prefix = parent.path
        depth = parent.depth + 1
    else:
        path_prefix = ''
        depth = 1
    existing = collections(where="path LIKE ? AND length(path)=?",
                           where_args=[path_prefix + '%', len(path_prefix) + 4],
                           order_by='path DESC', limit=1)
    if existing:
        next_num = int(existing[0].path[-4:]) + 1
    else:
        next_num = 1
    path = path_prefix + f'{next_num:04d}'
    return collections.insert(name=name, path=path, depth=depth, parent_id=parent_id)
