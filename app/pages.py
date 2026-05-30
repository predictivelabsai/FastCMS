import json, re, secrets
from app.db import db, pages, revisions, now, log_action

PAGE_TYPES = {
    'RootPage':      {'icon': '🏠', 'allowed_children': ['HomePage', 'ContentPage', 'BlogIndexPage', 'FormPage']},
    'HomePage':      {'icon': '🏠', 'allowed_children': ['ContentPage', 'BlogIndexPage', 'FormPage']},
    'ContentPage':   {'icon': '📄', 'allowed_children': ['ContentPage', 'FormPage']},
    'BlogIndexPage': {'icon': '📋', 'allowed_children': ['BlogPage']},
    'BlogPage':      {'icon': '✏️', 'allowed_children': []},
    'FormPage':      {'icon': '📝', 'allowed_children': []},
}

EXTRA_FIELDS = {
    'BlogPage': [
        {'name': 'date', 'label': 'Date', 'type': 'date'},
        {'name': 'author', 'label': 'Author', 'type': 'text'},
        {'name': 'featured_image_id', 'label': 'Featured Image', 'type': 'image'},
        {'name': 'tags', 'label': 'Tags', 'type': 'text'},
    ],
    'BlogIndexPage': [
        {'name': 'intro', 'label': 'Introduction', 'type': 'richtext'},
    ],
    'FormPage': [
        {'name': 'intro', 'label': 'Introduction', 'type': 'richtext'},
        {'name': 'thank_you_text', 'label': 'Thank You Text', 'type': 'richtext'},
        {'name': 'from_email', 'label': 'From Email', 'type': 'email'},
        {'name': 'to_email', 'label': 'To Email', 'type': 'email'},
        {'name': 'subject', 'label': 'Subject', 'type': 'text'},
    ],
}

def slugify(title):
    s = title.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_]+', '-', s)
    s = re.sub(r'-+', '-', s).strip('-')
    return s or 'untitled'

def get_root_page():
    roots = pages(where="depth=1", limit=1)
    return roots[0] if roots else None

def get_children(page_id):
    p = pages[page_id]
    child_depth = p.depth + 1
    prefix = p.path
    return pages(where=f"depth=? AND path LIKE ? AND length(path)=?",
                 where_args=[child_depth, prefix + '%', len(prefix) + 4],
                 order_by='path')

def get_descendants(page_id):
    p = pages[page_id]
    return pages(where="path LIKE ? AND id != ?",
                 where_args=[p.path + '%', page_id],
                 order_by='path')

def get_ancestors(page_id):
    p = pages[page_id]
    ancestor_paths = []
    for i in range(4, len(p.path) + 1, 4):
        ancestor_paths.append(p.path[:i])
    if not ancestor_paths: return []
    placeholders = ','.join('?' * len(ancestor_paths))
    return pages(where=f"path IN ({placeholders})",
                 where_args=ancestor_paths,
                 order_by='depth')

def get_next_path(parent_path):
    existing = pages(where="path LIKE ? AND length(path)=?",
                     where_args=[parent_path + '%', len(parent_path) + 4],
                     order_by='path DESC', limit=1)
    if existing:
        last_segment = existing[0].path[-4:]
        next_num = int(last_segment) + 1
    else:
        next_num = 1
    return parent_path + f'{next_num:04d}'

def compute_url_path(page_path):
    ancestors = []
    for i in range(4, len(page_path) + 1, 4):
        seg_path = page_path[:i]
        matching = pages(where="path=?", where_args=[seg_path], limit=1)
        if matching:
            ancestors.append(matching[0].slug)
    if len(ancestors) <= 1:
        return '/'
    return '/' + '/'.join(ancestors[1:]) + '/'

def create_page(parent_id, title, slug, content_type='ContentPage', body_json='[]', extra_json='{}', owner_id=0):
    parent = pages[parent_id]
    path = get_next_path(parent.path)
    depth = parent.depth + 1
    page = pages.insert(
        title=title, slug=slug, content_type=content_type,
        path=path, depth=depth, numchild=0,
        url_path='', live=False, has_unpublished_changes=True,
        owner_id=owner_id, body_json=body_json, extra_json=extra_json,
        created_at=now(), updated_at=now()
    )
    url_path = compute_url_path(path)
    pages.update(id=page.id, url_path=url_path)
    pages.update(id=parent_id, numchild=parent.numchild + 1)
    page = pages[page.id]
    create_revision(page.id, owner_id, comment='Created')
    return page

def update_page(page_id, user_id, **kwargs):
    kwargs['updated_at'] = now()
    kwargs['has_unpublished_changes'] = True
    if 'title' in kwargs or 'slug' in kwargs:
        pages.update(id=page_id, **kwargs)
        p = pages[page_id]
        url_path = compute_url_path(p.path)
        pages.update(id=page_id, url_path=url_path)
    else:
        pages.update(id=page_id, **kwargs)
    create_revision(page_id, user_id, comment='Edited')
    return pages[page_id]

def publish_page(page_id, user_id):
    ts = now()
    p = pages[page_id]
    update = dict(live=True, has_unpublished_changes=False, last_published_at=ts)
    if not p.first_published_at:
        update['first_published_at'] = ts
    pages.update(id=page_id, **update)
    create_revision(page_id, user_id, is_published=True, comment='Published')
    log_action(user_id, 'publish', 'page', page_id, p.title)
    return pages[page_id]

def unpublish_page(page_id, user_id):
    p = pages[page_id]
    pages.update(id=page_id, live=False)
    log_action(user_id, 'unpublish', 'page', page_id, p.title)
    return pages[page_id]

def delete_page(page_id, user_id):
    p = pages[page_id]
    descendants = get_descendants(page_id)
    for d in reversed(descendants):
        revisions_for = revisions(where="page_id=?", where_args=[d.id])
        for r in revisions_for:
            revisions.delete(r.id)
        pages.delete(d.id)
    revisions_for = revisions(where="page_id=?", where_args=[page_id])
    for r in revisions_for:
        revisions.delete(r.id)
    parent_path = p.path[:-4]
    parents = pages(where="path=?", where_args=[parent_path], limit=1)
    pages.delete(page_id)
    if parents:
        parent = parents[0]
        pages.update(id=parent.id, numchild=max(0, parent.numchild - 1))
    log_action(user_id, 'delete', 'page', page_id, p.title)

def copy_page(page_id, new_parent_id, new_title=None, new_slug=None, user_id=0):
    orig = pages[page_id]
    title = new_title or f'{orig.title} (copy)'
    slug = new_slug or f'{orig.slug}-copy'
    return create_page(new_parent_id, title, slug, orig.content_type,
                       orig.body_json, orig.extra_json, user_id)

def move_page(page_id, new_parent_id, user_id=0):
    p = pages[page_id]
    old_parent_path = p.path[:-4]
    old_parents = pages(where="path=?", where_args=[old_parent_path], limit=1)

    new_path = get_next_path(pages[new_parent_id].path)
    old_path = p.path
    new_depth = pages[new_parent_id].depth + 1
    depth_diff = new_depth - p.depth

    pages.update(id=page_id, path=new_path, depth=new_depth)
    descendants = get_descendants(page_id)
    for d in descendants:
        d_new_path = new_path + d.path[len(old_path):]
        pages.update(id=d.id, path=d_new_path, depth=d.depth + depth_diff)

    if old_parents:
        op = old_parents[0]
        pages.update(id=op.id, numchild=max(0, op.numchild - 1))
    np = pages[new_parent_id]
    pages.update(id=new_parent_id, numchild=np.numchild + 1)

    _recompute_url_paths(page_id)
    log_action(user_id, 'move', 'page', page_id, p.title)

def _recompute_url_paths(page_id):
    p = pages[page_id]
    url_path = compute_url_path(p.path)
    pages.update(id=page_id, url_path=url_path)
    for d in get_descendants(page_id):
        url_path = compute_url_path(d.path)
        pages.update(id=d.id, url_path=url_path)

def lock_page(page_id, user_id):
    pages.update(id=page_id, locked=True, locked_by_id=user_id, locked_at=now())
    log_action(user_id, 'lock', 'page', page_id)

def unlock_page(page_id, user_id):
    pages.update(id=page_id, locked=False, locked_by_id=0, locked_at='')
    log_action(user_id, 'unlock', 'page', page_id)

# ── Revisions ─────────────────────────────────────────────────────────

def create_revision(page_id, user_id, is_published=False, comment=''):
    p = pages[page_id]
    content = json.dumps({
        'title': p.title, 'slug': p.slug, 'content_type': p.content_type,
        'seo_title': p.seo_title, 'search_description': p.search_description,
        'show_in_menus': p.show_in_menus, 'body_json': p.body_json,
        'extra_json': p.extra_json, 'go_live_at': p.go_live_at,
        'expire_at': p.expire_at,
    })
    ts = now()
    return revisions.insert(
        page_id=page_id, content_json=content, created_at=ts,
        created_by_id=user_id, is_published=is_published,
        published_at=ts if is_published else '', comment=comment,
    )

def get_revisions(page_id):
    return revisions(where="page_id=?", where_args=[page_id], order_by='created_at DESC')

def restore_revision(revision_id, user_id):
    rev = revisions[revision_id]
    content = json.loads(rev.content_json)
    pages.update(id=rev.page_id,
        title=content['title'], slug=content['slug'],
        seo_title=content.get('seo_title', ''),
        search_description=content.get('search_description', ''),
        show_in_menus=content.get('show_in_menus', False),
        body_json=content.get('body_json', '[]'),
        extra_json=content.get('extra_json', '{}'),
        go_live_at=content.get('go_live_at', ''),
        expire_at=content.get('expire_at', ''),
        has_unpublished_changes=True, updated_at=now(),
    )
    _recompute_url_paths(rev.page_id)
    create_revision(rev.page_id, user_id, comment=f'Restored from revision {revision_id}')
    return pages[rev.page_id]

def diff_revisions(rev_a_id, rev_b_id):
    a = json.loads(revisions[rev_a_id].content_json)
    b = json.loads(revisions[rev_b_id].content_json)
    changes = {}
    all_keys = set(list(a.keys()) + list(b.keys()))
    for k in all_keys:
        va, vb = a.get(k), b.get(k)
        if va != vb:
            changes[k] = {'old': va, 'new': vb}
    return changes

# ── URL resolution ────────────────────────────────────────────────────

def resolve_page_by_url(url_path):
    matching = pages(where="url_path=? AND live=1", where_args=[url_path], order_by='depth DESC', limit=1)
    return matching[0] if matching else None

# ── Scheduled publishing ──────────────────────────────────────────────

def check_scheduled_pages():
    ts = now()
    to_publish = pages(where="go_live_at != '' AND go_live_at <= ? AND live = 0", where_args=[ts])
    for p in to_publish:
        pages.update(id=p.id, live=True, has_unpublished_changes=False,
                     last_published_at=ts, go_live_at='')
        if not p.first_published_at:
            pages.update(id=p.id, first_published_at=ts)

    to_expire = pages(where="expire_at != '' AND expire_at <= ? AND live = 1", where_args=[ts])
    for p in to_expire:
        pages.update(id=p.id, live=False, expired=True, expire_at='')
