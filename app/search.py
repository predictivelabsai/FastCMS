import re
from app.db import db, pages, images, documents
from app.blocks import extract_text_from_blocks

def index_page(page):
    body_text = extract_text_from_blocks(page.body_json)
    remove_from_index('page', page.id)
    db.execute(
        "INSERT INTO search_index (title, body, content_type, object_id) VALUES (?, ?, 'page', ?)",
        [page.title, body_text, str(page.id)]
    )

def index_image(image):
    remove_from_index('image', image.id)
    body = f"{image.alt_text} {image.tags}"
    db.execute(
        "INSERT INTO search_index (title, body, content_type, object_id) VALUES (?, ?, 'image', ?)",
        [image.title, body, str(image.id)]
    )

def index_document(document):
    remove_from_index('document', document.id)
    db.execute(
        "INSERT INTO search_index (title, body, content_type, object_id) VALUES (?, ?, 'document', ?)",
        [document.title, document.tags, str(document.id)]
    )

def remove_from_index(content_type, object_id):
    db.execute(
        "DELETE FROM search_index WHERE content_type=? AND object_id=?",
        [content_type, str(object_id)]
    )

def search(query, content_type=None, limit=20, offset=0):
    if not query: return []
    clean_q = re.sub(r'[^\w\s]', '', query).strip()
    if not clean_q: return []
    fts_query = ' '.join(f'"{w}"*' for w in clean_q.split())
    where = ""
    args = [fts_query]
    if content_type:
        where = " AND content_type=?"
        args.append(content_type)
    args.extend([limit, offset])
    rows = db.execute(
        f"""SELECT title, body, content_type, object_id, rank
            FROM search_index WHERE search_index MATCH ?{where}
            ORDER BY rank LIMIT ? OFFSET ?""",
        args
    ).fetchall()
    return [{'title': r[0], 'body': r[1][:200], 'content_type': r[2],
             'object_id': int(r[3]), 'rank': r[4]} for r in rows]

def search_autocomplete(query, limit=5):
    return search(query, limit=limit)

def reindex_all():
    db.execute("DELETE FROM search_index")
    for p in pages(where="live=1"):
        index_page(p)
    for img in images():
        index_image(img)
    for doc in documents():
        index_document(doc)
