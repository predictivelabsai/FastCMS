import json
from fasthtml.common import *
from starlette.responses import RedirectResponse
from app.db import pages, users, images, now
from app.pages import (
    create_page, update_page, publish_page, unpublish_page, delete_page,
    copy_page, move_page, lock_page, unlock_page, get_revisions, restore_revision,
    diff_revisions, get_ancestors, get_children, slugify, PAGE_TYPES, EXTRA_FIELDS
)
from app.blocks import blocks_editor, parse_blocks_from_form
from admin.components import (
    admin_page, field_panel, rich_text_panel, image_chooser_panel,
    tab_panel, action_menu, status_badge, confirm_dialog, toast
)

def page_add_form(auth, parent_id: int = 1, content_type: str = 'ContentPage'):
    parent = pages[parent_id]
    ancestors = get_ancestors(parent_id)
    bc = [('Pages', '/admin/pages/')]
    for a in ancestors:
        bc.append((a.title, f'/admin/pages/{a.id}/'))
    bc.append((parent.title, f'/admin/pages/{parent_id}/'))
    bc.append(('New page', None))

    extra_fields = EXTRA_FIELDS.get(content_type, [])
    extra_panels = []
    for f in extra_fields:
        if f['type'] == 'richtext':
            extra_panels.append(rich_text_panel(f'extra_{f["name"]}', f['label']))
        elif f['type'] == 'image':
            extra_panels.append(image_chooser_panel(f'extra_{f["name"]}', f['label']))
        else:
            extra_panels.append(field_panel(f'extra_{f["name"]}', f['label'], field_type=f['type']))

    content_tab = Div(
        field_panel('title', 'Title', required=True,
                    hx_get='/admin/pages/slugify/', hx_trigger='keyup changed delay:500ms',
                    hx_target='#slug-field', hx_swap='outerHTML', hx_include='[name=title]'),
        Div(field_panel('slug', 'Slug'), id='slug-field'),
        *extra_panels,
        blocks_editor('body', '[]'),
    )

    promote_tab = Div(
        field_panel('seo_title', 'SEO Title', help_text='Override the page title in search results'),
        field_panel('search_description', 'Search Description', field_type='textarea',
                    help_text='Shown in search engine results'),
    )

    settings_tab = Div(
        field_panel('go_live_at', 'Go Live Date/Time', field_type='datetime',
                    help_text='Schedule when this page goes live'),
        field_panel('expire_at', 'Expiry Date/Time', field_type='datetime',
                    help_text='Schedule when this page is unpublished'),
        field_panel('show_in_menus', 'Show in Menus', field_type='checkbox'),
    )

    tabs = tab_panel([
        ('Content', content_tab),
        ('Promote', promote_tab),
        ('Settings', settings_tab),
    ])

    return admin_page(
        f'New {content_type}', auth=auth, active='pages', breadcrumbs=bc, body=[

        Form(
            Input(type='hidden', name='parent_id', value=str(parent_id)),
            Input(type='hidden', name='content_type', value=content_type),

            Div(
                H1(f"New {content_type}", cls="text-2xl font-semibold"),
                cls="mb-6"
            ),
            Div(tabs, cls="bg-white rounded-xl border border-gray-200 p-6 mb-20"),
            action_menu(
                'Save Draft', f'/admin/pages/add/',
                ('Publish', f'/admin/pages/add/?action=publish', ''),
            ),
            method='post', action='/admin/pages/add/',
        ),
    ])

def page_add_submit(auth, parent_id: int = 1, content_type: str = 'ContentPage',
                    title: str = '', slug: str = '', action: str = '',
                    seo_title: str = '', search_description: str = '',
                    go_live_at: str = '', expire_at: str = '', show_in_menus: str = '', **kwargs):
    if not slug:
        slug = slugify(title)

    extra = {}
    for k, v in kwargs.items():
        if k.startswith('extra_'):
            extra[k[6:]] = v
    body_json = parse_blocks_from_form(kwargs, 'body')

    page = create_page(parent_id, title, slug, content_type,
                       body_json=body_json, extra_json=json.dumps(extra),
                       owner_id=auth.id)

    updates = {}
    if seo_title: updates['seo_title'] = seo_title
    if search_description: updates['search_description'] = search_description
    if go_live_at: updates['go_live_at'] = go_live_at
    if expire_at: updates['expire_at'] = expire_at
    if show_in_menus: updates['show_in_menus'] = True
    if updates:
        update_page(page.id, auth.id, **updates)

    if action == 'publish' or kwargs.get('action') == 'publish':
        publish_page(page.id, auth.id)

    return RedirectResponse(f'/admin/pages/{page.id}/edit/', status_code=303)

def page_edit_form(page_id, auth):
    p = pages[page_id]
    ancestors = get_ancestors(page_id)
    bc = [('Pages', '/admin/pages/')]
    for a in ancestors:
        if a.id != page_id:
            bc.append((a.title, f'/admin/pages/{a.id}/'))
    bc.append((p.title, None))

    extra = json.loads(p.extra_json) if p.extra_json else {}
    extra_fields = EXTRA_FIELDS.get(p.content_type, [])
    extra_panels = []
    for f in extra_fields:
        val = extra.get(f['name'], '')
        if f['type'] == 'richtext':
            extra_panels.append(rich_text_panel(f'extra_{f["name"]}', f['label'], value=val))
        elif f['type'] == 'image':
            img = None
            if val:
                try: img = images[int(val)]
                except: pass
            extra_panels.append(image_chooser_panel(f'extra_{f["name"]}', f['label'], current_image=img))
        else:
            extra_panels.append(field_panel(f'extra_{f["name"]}', f['label'], value=val, field_type=f['type']))

    content_tab = Div(
        field_panel('title', 'Title', value=p.title, required=True,
                    hx_get='/admin/pages/slugify/', hx_trigger='keyup changed delay:500ms',
                    hx_target='#slug-field', hx_swap='outerHTML', hx_include='[name=title]'),
        Div(field_panel('slug', 'Slug', value=p.slug), id='slug-field'),
        *extra_panels,
        blocks_editor('body', p.body_json),
    )

    promote_tab = Div(
        field_panel('seo_title', 'SEO Title', value=p.seo_title),
        field_panel('search_description', 'Search Description', value=p.search_description, field_type='textarea'),
    )

    settings_tab = Div(
        field_panel('go_live_at', 'Go Live Date/Time', value=p.go_live_at, field_type='datetime'),
        field_panel('expire_at', 'Expiry Date/Time', value=p.expire_at, field_type='datetime'),
        field_panel('show_in_menus', 'Show in Menus', value=p.show_in_menus, field_type='checkbox'),
        Div(
            H3("Page Info", cls="text-sm font-semibold text-gray-700 mb-3 mt-6"),
            P(f"Type: {p.content_type}", cls="text-sm text-gray-500"),
            P(f"URL: {p.url_path}", cls="text-sm text-gray-500"),
            P(f"Created: {p.created_at[:16].replace('T', ' ') if p.created_at else '—'}", cls="text-sm text-gray-500"),
            P(f"Status: {'Live' if p.live else 'Draft'}", cls="text-sm text-gray-500"),
            cls="border-t border-gray-200 pt-4"
        ),
    )

    tabs = tab_panel([
        ('Content', content_tab),
        ('Promote', promote_tab),
        ('Settings', settings_tab),
    ])

    lock_info = ''
    if p.locked and p.locked_by_id != auth.id:
        try:
            locker = users[p.locked_by_id]
            lock_info = Div(
                P(f"⚠️ This page is locked by {locker.name}.", cls="text-sm text-amber-700"),
                cls="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4"
            )
        except:
            pass

    secondary = [
        ('Publish', f'/admin/pages/{page_id}/publish/', '') if not p.live else
        ('Unpublish', f'/admin/pages/{page_id}/unpublish/', 'text-amber-600'),
    ]
    secondary.append(('View Revisions', f'/admin/pages/{page_id}/revisions/', ''))
    if p.locked:
        secondary.append(('Unlock', f'/admin/pages/{page_id}/unlock/', ''))
    else:
        secondary.append(('Lock', f'/admin/pages/{page_id}/lock/', ''))
    secondary.append(('Delete', f'/admin/pages/{page_id}/delete/', 'text-red-600'))

    return admin_page(
        f'Edit — {p.title}', auth=auth, active='pages', breadcrumbs=bc, body=[

        lock_info,

        Form(
            Div(
                Div(
                    H1(p.title, cls="text-2xl font-semibold"),
                    status_badge(p),
                    cls="flex items-center gap-3"
                ),
                cls="mb-6"
            ),
            Div(tabs, cls="bg-white rounded-xl border border-gray-200 p-6 mb-20"),
            action_menu('Save Draft', f'/admin/pages/{page_id}/edit/', *secondary),
            method='post', action=f'/admin/pages/{page_id}/edit/',
        ),
    ])

def page_edit_submit(page_id, auth, title: str = '', slug: str = '', action: str = '',
                     seo_title: str = '', search_description: str = '',
                     go_live_at: str = '', expire_at: str = '', show_in_menus: str = '', **kwargs):
    if not slug:
        slug = slugify(title)

    extra = {}
    for k, v in kwargs.items():
        if k.startswith('extra_'):
            extra[k[6:]] = v
    body_json = parse_blocks_from_form(kwargs, 'body')

    update_page(page_id, auth.id,
                title=title, slug=slug, seo_title=seo_title,
                search_description=search_description,
                go_live_at=go_live_at, expire_at=expire_at,
                show_in_menus=bool(show_in_menus),
                body_json=body_json, extra_json=json.dumps(extra))

    return RedirectResponse(f'/admin/pages/{page_id}/edit/', status_code=303)

def page_publish(page_id, auth):
    publish_page(page_id, auth.id)
    return RedirectResponse(f'/admin/pages/{page_id}/edit/', status_code=303)

def page_unpublish(page_id, auth):
    unpublish_page(page_id, auth.id)
    return RedirectResponse(f'/admin/pages/{page_id}/edit/', status_code=303)

def page_delete_confirm(page_id, auth):
    p = pages[page_id]
    return confirm_dialog(
        f'Delete "{p.title}"?',
        'This will permanently delete the page and all its child pages. This action cannot be undone.',
        f'/admin/pages/{page_id}/delete/',
        action_label='Delete Page'
    )

def page_delete_submit(page_id, auth):
    p = pages[page_id]
    parent_path = p.path[:-4]
    parent_pages = pages(where="path=?", where_args=[parent_path], limit=1)
    delete_page(page_id, auth.id)
    redirect_to = f'/admin/pages/{parent_pages[0].id}/' if parent_pages else '/admin/pages/'
    return RedirectResponse(redirect_to, status_code=303)

def page_lock(page_id, auth):
    lock_page(page_id, auth.id)
    return RedirectResponse(f'/admin/pages/{page_id}/edit/', status_code=303)

def page_unlock(page_id, auth):
    unlock_page(page_id, auth.id)
    return RedirectResponse(f'/admin/pages/{page_id}/edit/', status_code=303)

def page_copy_submit(page_id, auth, new_title: str = '', new_slug: str = ''):
    p = pages[page_id]
    parent_path = p.path[:-4]
    parent_pages = pages(where="path=?", where_args=[parent_path], limit=1)
    parent_id = parent_pages[0].id if parent_pages else 1
    new_page = copy_page(page_id, parent_id, new_title or None, new_slug or None, auth.id)
    return RedirectResponse(f'/admin/pages/{new_page.id}/edit/', status_code=303)

def page_move_submit(page_id, auth, new_parent_id: int = 1):
    move_page(page_id, new_parent_id, auth.id)
    return RedirectResponse(f'/admin/pages/{page_id}/edit/', status_code=303)

def page_revisions_list(page_id, auth):
    p = pages[page_id]
    revs = get_revisions(page_id)
    bc = [('Pages', '/admin/pages/'), (p.title, f'/admin/pages/{page_id}/edit/'), ('Revisions', None)]

    rows = []
    for rev in revs:
        editor = None
        if rev.created_by_id:
            try: editor = users[rev.created_by_id]
            except: pass
        rows.append(Tr(
            Td(rev.created_at[:19].replace('T', ' '), cls="py-2 px-4 text-sm"),
            Td(editor.name if editor else '—', cls="py-2 px-4 text-sm text-gray-500"),
            Td(rev.comment or '—', cls="py-2 px-4 text-sm text-gray-500"),
            Td(Span("Published", cls="text-green-600 text-xs") if rev.is_published else '', cls="py-2 px-4"),
            Td(Form(Button("Restore", type="submit", cls="text-xs text-accent hover:underline"),
                    method='post', action=f'/admin/pages/{page_id}/revisions/{rev.id}/restore/'),
               cls="py-2 px-4 text-right"),
        ))

    return admin_page(
        f'Revisions — {p.title}', auth=auth, active='pages', breadcrumbs=bc, body=[
        Div(
            H1(f'Revisions for “{p.title}”', cls="text-2xl font-semibold mb-6"),
            Div(
                Table(
                    Thead(Tr(
                        Th("Date", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                        Th("Editor", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                        Th("Comment", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                        Th("Status", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                        Th("", cls="py-2 px-4"),
                    )),
                    Tbody(*rows),
                    cls="w-full"
                ),
                cls="bg-white rounded-xl border border-gray-200"
            ),
        ),
    ])

def revision_restore(page_id, rev_id, auth):
    restore_revision(rev_id, auth.id)
    return RedirectResponse(f'/admin/pages/{page_id}/edit/', status_code=303)

def slugify_title(title: str = ''):
    slug = slugify(title)
    return field_panel('slug', 'Slug', value=slug, id='slug-field')

def page_chooser_view(auth, field: str = '', parent_id: int = 0):
    if parent_id:
        children = get_children(parent_id)
    else:
        root = pages(where="depth=1", limit=1)
        if root:
            children = get_children(root[0].id)
        else:
            children = []

    rows = []
    for child in children:
        ptype = PAGE_TYPES.get(child.content_type, {})
        rows.append(Div(
            Button(
                Span(ptype.get('icon', '📄'), cls="mr-2"),
                child.title,
                type="button",
                onclick=f"selectPage('{field}', {child.id}, '{child.title}'); document.getElementById('modal-container').innerHTML='';",
                cls="w-full text-left px-4 py-2 text-sm hover:bg-accent-dim rounded transition-colors"
            ),
            A("▶", href="#", hx_get=f"/admin/pages/chooser/?field={field}&parent_id={child.id}",
              hx_target="#modal-container", hx_swap="innerHTML",
              cls="px-2 text-gray-400 hover:text-accent") if child.numchild > 0 else '',
            cls="flex items-center justify-between"
        ))

    return Div(
        Div(
            Div(
                Div(
                    H3("Choose a page", cls="text-lg font-semibold"),
                    Button("✕", type="button", onclick="this.closest('#modal-container').innerHTML=''",
                           cls="text-gray-400 hover:text-gray-600 text-xl"),
                    cls="flex items-center justify-between mb-4"
                ),
                Div(*rows, cls="max-h-96 overflow-y-auto") if rows else P("No pages", cls="text-sm text-gray-500 py-4"),
                cls="bg-white rounded-2xl p-6 max-w-lg w-full shadow-xl max-h-[80vh] overflow-y-auto"
            ),
            cls="fixed inset-0 bg-black/50 flex items-center justify-center z-50",
            onclick="if(event.target===this)this.remove()"
        ),
    )
