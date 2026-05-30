from fasthtml.common import *
from app.db import pages, audit_logs, users
from admin.components import admin_page, empty_state

def reports_index(auth):
    reports = [
        ('📊', 'Page Types', 'Count of pages by content type', '/admin/reports/types/'),
        ('🔒', 'Locked Pages', 'Pages currently locked for editing', '/admin/reports/locked/'),
        ('⏰', 'Aging Pages', 'Pages not updated in 90+ days', '/admin/reports/aging/'),
        ('📜', 'Audit Log', 'History of all admin actions', '/admin/reports/audit/'),
    ]
    cards = [
        A(
            Div(Span(icon, cls="text-2xl"), cls="mb-2"),
            H3(title, cls="text-sm font-semibold"),
            P(desc, cls="text-xs text-gray-500"),
            href=url, cls="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow block"
        )
        for icon, title, desc, url in reports
    ]
    return admin_page('Reports', auth=auth, active='reports', body=[
        Div(H1("Reports", cls="text-2xl font-semibold"), cls="mb-6"),
        Div(*cards, cls="grid grid-cols-2 md:grid-cols-4 gap-4"),
    ])

def page_types_report(auth):
    all_pages = pages()
    counts = {}
    for p in all_pages:
        counts[p.content_type] = counts.get(p.content_type, 0) + 1
    rows = [Tr(
        Td(ct, cls="py-2 px-4 text-sm"),
        Td(str(count), cls="py-2 px-4 text-sm font-medium"),
    ) for ct, count in sorted(counts.items(), key=lambda x: -x[1])]

    return admin_page('Page Types Report', auth=auth, active='reports',
        breadcrumbs=[('Reports', '/admin/reports/'), ('Page Types', None)], body=[
        Div(H1("Page Types", cls="text-2xl font-semibold"), cls="mb-6"),
        Div(
            Table(Thead(Tr(
                Th("Content Type", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                Th("Count", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
            )), Tbody(*rows), cls="w-full"),
            cls="bg-white rounded-xl border border-gray-200"
        ),
    ])

def locked_pages_report(auth):
    locked = pages(where="locked=1")
    rows = []
    for p in locked:
        locker = None
        if p.locked_by_id:
            try: locker = users[p.locked_by_id]
            except: pass
        rows.append(Tr(
            Td(A(p.title, href=f"/admin/pages/{p.id}/edit/", cls="text-accent hover:underline"), cls="py-2 px-4 text-sm"),
            Td(locker.name if locker else '—', cls="py-2 px-4 text-sm text-gray-500"),
            Td(p.locked_at[:16].replace('T', ' ') if p.locked_at else '—', cls="py-2 px-4 text-xs text-gray-400"),
        ))

    return admin_page('Locked Pages', auth=auth, active='reports',
        breadcrumbs=[('Reports', '/admin/reports/'), ('Locked Pages', None)], body=[
        Div(H1("Locked Pages", cls="text-2xl font-semibold"), cls="mb-6"),
        Div(
            Table(Thead(Tr(
                Th("Page", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                Th("Locked By", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                Th("Locked At", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
            )), Tbody(*rows), cls="w-full") if rows else empty_state('🔓', 'No locked pages'),
            cls="bg-white rounded-xl border border-gray-200"
        ),
    ])

def aging_pages_report(auth):
    from datetime import datetime, timedelta, timezone
    cutoff = (datetime.now(timezone.utc) - timedelta(days=90)).isoformat()
    aging = pages(where="updated_at < ? AND updated_at != '' AND live=1", where_args=[cutoff],
                  order_by='updated_at')
    rows = [Tr(
        Td(A(p.title, href=f"/admin/pages/{p.id}/edit/", cls="text-accent hover:underline"), cls="py-2 px-4 text-sm"),
        Td(p.content_type, cls="py-2 px-4 text-xs text-gray-500"),
        Td(p.updated_at[:10] if p.updated_at else '—', cls="py-2 px-4 text-xs text-gray-400"),
    ) for p in aging]

    return admin_page('Aging Pages', auth=auth, active='reports',
        breadcrumbs=[('Reports', '/admin/reports/'), ('Aging Pages', None)], body=[
        Div(H1("Aging Pages (90+ days)", cls="text-2xl font-semibold"), cls="mb-6"),
        Div(
            Table(Thead(Tr(
                Th("Page", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                Th("Type", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                Th("Last Updated", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
            )), Tbody(*rows), cls="w-full") if rows else empty_state('✅', 'No aging pages', 'All live pages have been updated recently.'),
            cls="bg-white rounded-xl border border-gray-200"
        ),
    ])

def audit_log_report(auth, page: int = 1):
    per_page = 50
    all_logs = audit_logs(order_by='created_at DESC')
    total = len(all_logs)
    page_logs = all_logs[(page-1)*per_page:page*per_page]

    rows = []
    for log in page_logs:
        user = None
        if log.user_id:
            try: user = users[log.user_id]
            except: pass
        rows.append(Tr(
            Td(log.created_at[:19].replace('T', ' '), cls="py-2 px-4 text-xs text-gray-400"),
            Td(user.name if user else '—', cls="py-2 px-4 text-sm text-gray-500"),
            Td(Span(log.action, cls="px-2 py-0.5 text-xs rounded-full bg-gray-100 font-medium"), cls="py-2 px-4"),
            Td(f"{log.content_type} #{log.object_id}", cls="py-2 px-4 text-sm text-gray-500"),
            Td(log.object_repr, cls="py-2 px-4 text-sm"),
        ))

    from admin.components import pagination
    return admin_page('Audit Log', auth=auth, active='reports',
        breadcrumbs=[('Reports', '/admin/reports/'), ('Audit Log', None)], body=[
        Div(H1("Audit Log", cls="text-2xl font-semibold"), cls="mb-6"),
        Div(
            Table(Thead(Tr(
                Th("Date", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                Th("User", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                Th("Action", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                Th("Object", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                Th("Name", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
            )), Tbody(*rows), cls="w-full") if rows else empty_state('📜', 'No audit entries yet'),
            cls="bg-white rounded-xl border border-gray-200"
        ),
        pagination(total, page, per_page, '/admin/reports/audit/'),
    ])
