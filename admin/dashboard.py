from fasthtml.common import *
from app.db import pages, images, documents, users, revisions
from admin.components import admin_page, stat_card, empty_state

def admin_dashboard(auth):
    page_count = len(pages())
    image_count = len(images())
    doc_count = len(documents())
    user_count = len(users())

    recent_revs = revisions(order_by='created_at DESC', limit=10)
    recent_rows = []
    for rev in recent_revs:
        try:
            p = pages[rev.page_id]
            editor = users[rev.created_by_id] if rev.created_by_id else None
            recent_rows.append(Tr(
                Td(A(p.title, href=f"/admin/pages/{p.id}/edit/", cls="text-accent hover:underline"), cls="py-2 px-3 text-sm"),
                Td(editor.name if editor else '—', cls="py-2 px-3 text-sm text-gray-500"),
                Td(rev.created_at[:16].replace('T', ' '), cls="py-2 px-3 text-sm text-gray-400"),
                Td(Span("Published", cls="text-green-600 text-xs") if rev.is_published else Span("Draft", cls="text-gray-400 text-xs"),
                   cls="py-2 px-3"),
            ))
        except:
            pass

    drafts = pages(where="live=0 AND has_unpublished_changes=1", limit=10)
    draft_rows = [
        Tr(
            Td(A(p.title, href=f"/admin/pages/{p.id}/edit/", cls="text-accent hover:underline"), cls="py-2 px-3 text-sm"),
            Td(p.content_type, cls="py-2 px-3 text-sm text-gray-500"),
            Td(p.updated_at[:16].replace('T', ' ') if p.updated_at else '—', cls="py-2 px-3 text-sm text-gray-400"),
        ) for p in drafts
    ]

    welcome = Div(
        H1(f"Welcome, {auth.name}", cls="text-2xl font-semibold text-gray-900"),
        P("Here's what's happening with your site.", cls="text-sm text-gray-500 mt-1"),
        cls="mb-6"
    )
    stats = Div(
        stat_card("Pages", page_count, "📄"),
        stat_card("Images", image_count, "🖼️"),
        stat_card("Documents", doc_count, "📎"),
        stat_card("Users", user_count, "👥"),
        cls="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
    )
    tables = Div(
        Div(
            Div(H2("Recent Edits", cls="text-lg font-semibold"),
                A("View all pages →", href="/admin/pages/", cls="text-sm text-accent hover:underline"),
                cls="flex items-center justify-between mb-3"),
            Table(Thead(Tr(
                Th("Page", cls="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase"),
                Th("Editor", cls="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase"),
                Th("Date", cls="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase"),
                Th("Status", cls="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase"),
            )), Tbody(*recent_rows) if recent_rows else Tbody(Tr(Td("No recent edits", colspan="4", cls="py-4 text-center text-gray-400 text-sm"))),
            cls="w-full") if recent_rows else empty_state('📝', 'No edits yet', 'Create your first page.', '/admin/pages/', 'Create a page'),
            cls="bg-white rounded-xl border border-gray-200 p-4"
        ),
        Div(
            Div(H2("Draft Pages", cls="text-lg font-semibold"), cls="mb-3"),
            Table(Thead(Tr(
                Th("Page", cls="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase"),
                Th("Type", cls="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase"),
                Th("Updated", cls="py-2 px-3 text-left text-xs font-medium text-gray-500 uppercase"),
            )), Tbody(*draft_rows) if draft_rows else Tbody(Tr(Td("No drafts", colspan="3", cls="py-4 text-center text-gray-400 text-sm"))),
            cls="w-full"),
            cls="bg-white rounded-xl border border-gray-200 p-4"
        ),
        cls="grid lg:grid-cols-2 gap-6 mb-8"
    )
    actions = Div(
        H2("Quick Actions", cls="text-lg font-semibold mb-3"),
        Div(
            A("+ New Page", href="/admin/pages/add/?parent_id=1", cls="px-4 py-2 bg-accent text-white text-sm rounded-lg hover:bg-accent-deep"),
            A("+ Upload Image", href="/admin/images/", cls="px-4 py-2 border border-gray-300 text-sm rounded-lg hover:bg-gray-50"),
            A("+ Upload Document", href="/admin/documents/", cls="px-4 py-2 border border-gray-300 text-sm rounded-lg hover:bg-gray-50"),
            cls="flex gap-3"
        ),
        cls="mb-8"
    )
    return admin_page('Dashboard', welcome, stats, tables, actions, auth=auth, active='dashboard')
