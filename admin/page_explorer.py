from fasthtml.common import *
from app.db import pages, users
from app.pages import get_children, get_ancestors, get_root_page, PAGE_TYPES
from admin.components import admin_page, admin_breadcrumbs, status_badge, pagination, empty_state

def page_explorer_root(auth):
    root = get_root_page()
    if not root:
        return admin_page('Pages', auth=auth, active='pages', body=[
                          empty_state('📄', 'No pages yet', 'Run setup.py to create the root page.')])
    return page_explorer(root.id, auth)

def page_explorer(page_id, auth, page_num: int = 1):
    parent = pages[page_id]
    children = get_children(page_id)
    ancestors = get_ancestors(page_id)

    bc = [('Pages', '/admin/pages/')]
    for a in ancestors:
        if a.id != page_id:
            bc.append((a.title, f'/admin/pages/{a.id}/'))
    bc.append((parent.title, None))

    allowed = PAGE_TYPES.get(parent.content_type, {}).get('allowed_children', [])

    rows = []
    for child in children:
        ptype = PAGE_TYPES.get(child.content_type, {})
        icon = ptype.get('icon', '📄')
        has_children = child.numchild > 0

        title_el = Div(
            A(
                Span(icon, cls="mr-2"),
                Span(child.title, cls="font-medium"),
                Span(f" ({child.numchild})", cls="text-gray-400 text-xs ml-1") if has_children else '',
                href=f"/admin/pages/{child.id}/" if has_children else f"/admin/pages/{child.id}/edit/",
                cls="text-gray-900 hover:text-accent"
            ),
            cls="flex items-center"
        )

        actions_el = Div(
            A("Edit", href=f"/admin/pages/{child.id}/edit/",
              cls="text-xs text-accent hover:underline"),
            A("View", href=child.url_path, target="_blank",
              cls="text-xs text-gray-400 hover:underline ml-3") if child.live else '',
            A("Add child", href=f"/admin/pages/add/?parent_id={child.id}",
              cls="text-xs text-gray-400 hover:underline ml-3") if PAGE_TYPES.get(child.content_type, {}).get('allowed_children') else '',
            cls="flex items-center"
        )

        rows.append(Tr(
            Td(title_el, cls="py-3 px-4"),
            Td(Span(child.content_type, cls="text-xs text-gray-500"), cls="py-3 px-4"),
            Td(status_badge(child), cls="py-3 px-4"),
            Td(child.updated_at[:16].replace('T', ' ') if child.updated_at else '—', cls="py-3 px-4 text-sm text-gray-400"),
            Td(actions_el, cls="py-3 px-4 text-right"),
        ))

    add_buttons = []
    if allowed:
        for ct in allowed:
            ptype = PAGE_TYPES.get(ct, {})
            add_buttons.append(
                A(f"+ {ct}", href=f"/admin/pages/add/?parent_id={page_id}&content_type={ct}",
                  cls="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors")
            )

    return admin_page(
        f'Pages — {parent.title}', auth=auth, active='pages',
        breadcrumbs=bc, body=[

        Div(
            Div(
                H1(f"{parent.title}", cls="text-2xl font-semibold text-gray-900"),
                Div(*add_buttons, cls="flex gap-2") if add_buttons else '',
                cls="flex items-center justify-between"
            ),
            cls="mb-6"
        ),

        Div(
            Input(type='search', name='q', placeholder='Search pages...',
                  hx_get=f'/admin/pages/search/?parent_id={page_id}',
                  hx_trigger='keyup changed delay:300ms',
                  hx_target='#page-listing', hx_swap='innerHTML',
                  cls="w-64 px-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent outline-none"),
            cls="mb-4"
        ),

        Div(
            Table(
                Thead(Tr(
                    Th("Title", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                    Th("Type", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                    Th("Status", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                    Th("Updated", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                    Th("", cls="py-2 px-4"),
                )),
                Tbody(*rows),
                cls="w-full"
            ) if rows else empty_state(
                '📄', 'No child pages',
                f'Add a page under {parent.title}.',
                f'/admin/pages/add/?parent_id={page_id}' if allowed else '',
                f'+ Add page' if allowed else ''
            ),
            cls="bg-white rounded-xl border border-gray-200",
            id="page-listing"
        ),
    ])

def page_search(auth, q: str = '', parent_id: int = 0):
    if not q:
        return Div()
    results = pages(where="title LIKE ?", where_args=[f'%{q}%'], order_by='title', limit=20)
    if not results:
        return Div(P(f'No results for "{q}"', cls="text-sm text-gray-500 py-4 text-center"))
    rows = []
    for p in results:
        ptype = PAGE_TYPES.get(p.content_type, {})
        rows.append(Tr(
            Td(A(Span(ptype.get('icon', '📄'), cls="mr-2"), p.title,
                 href=f"/admin/pages/{p.id}/edit/", cls="text-sm text-gray-900 hover:text-accent"),
               cls="py-2 px-4"),
            Td(p.content_type, cls="py-2 px-4 text-xs text-gray-500"),
            Td(status_badge(p), cls="py-2 px-4"),
            Td(p.url_path, cls="py-2 px-4 text-xs text-gray-400"),
        ))
    return Table(
        Thead(Tr(
            Th("Title", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
            Th("Type", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
            Th("Status", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
            Th("URL", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
        )),
        Tbody(*rows),
        cls="w-full"
    )
