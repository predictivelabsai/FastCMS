from fasthtml.common import APIRouter
from admin import dashboard, page_explorer, page_editor, media_library
from admin import user_manager, snippet_editor, settings_admin, reports

ar = APIRouter()

# Dashboard
@ar("/admin/")
def get(auth): return dashboard.admin_dashboard(auth)

# Pages
@ar("/admin/pages/")
def get(auth): return page_explorer.page_explorer_root(auth)

@ar("/admin/pages/{page_id:int}/")
def get(page_id: int, auth, page: int = 1): return page_explorer.page_explorer(page_id, auth, page)

@ar("/admin/pages/search/")
def get(auth, q: str = '', parent_id: int = 0): return page_explorer.page_search(auth, q, parent_id)

@ar("/admin/pages/add/")
def get(auth, parent_id: int = 1, content_type: str = 'ContentPage'):
    return page_editor.page_add_form(auth, parent_id, content_type)

@ar("/admin/pages/add/", methods=["POST"])
def post(auth, **kwargs): return page_editor.page_add_submit(auth, **kwargs)

@ar("/admin/pages/{page_id:int}/edit/")
def get(page_id: int, auth): return page_editor.page_edit_form(page_id, auth)

@ar("/admin/pages/{page_id:int}/edit/", methods=["POST"])
def post(page_id: int, auth, **kwargs): return page_editor.page_edit_submit(page_id, auth, **kwargs)

@ar("/admin/pages/{page_id:int}/publish/", methods=["POST"])
def post(page_id: int, auth): return page_editor.page_publish(page_id, auth)

@ar("/admin/pages/{page_id:int}/unpublish/", methods=["POST"])
def post(page_id: int, auth): return page_editor.page_unpublish(page_id, auth)

@ar("/admin/pages/{page_id:int}/delete/")
def get(page_id: int, auth): return page_editor.page_delete_confirm(page_id, auth)

@ar("/admin/pages/{page_id:int}/delete/", methods=["POST"])
def post(page_id: int, auth): return page_editor.page_delete_submit(page_id, auth)

@ar("/admin/pages/{page_id:int}/lock/", methods=["POST"])
def post(page_id: int, auth): return page_editor.page_lock(page_id, auth)

@ar("/admin/pages/{page_id:int}/unlock/", methods=["POST"])
def post(page_id: int, auth): return page_editor.page_unlock(page_id, auth)

@ar("/admin/pages/{page_id:int}/copy/", methods=["POST"])
def post(page_id: int, auth, **kwargs): return page_editor.page_copy_submit(page_id, auth, **kwargs)

@ar("/admin/pages/{page_id:int}/move/", methods=["POST"])
def post(page_id: int, auth, **kwargs): return page_editor.page_move_submit(page_id, auth, **kwargs)

@ar("/admin/pages/{page_id:int}/revisions/")
def get(page_id: int, auth): return page_editor.page_revisions_list(page_id, auth)

@ar("/admin/pages/{page_id:int}/revisions/{rev_id:int}/restore/", methods=["POST"])
def post(page_id: int, rev_id: int, auth): return page_editor.revision_restore(page_id, rev_id, auth)

@ar("/admin/pages/slugify/")
def get(title: str = ''): return page_editor.slugify_title(title)

@ar("/admin/pages/chooser/")
def get(auth, field: str = '', parent_id: int = 0): return page_editor.page_chooser_view(auth, field, parent_id)

# Images
@ar("/admin/images/")
def get(auth, page: int = 1, collection: int = 0, q: str = ''):
    return media_library.image_list(auth, page, collection, q)

@ar("/admin/images/{image_id:int}/")
def get(image_id: int, auth): return media_library.image_detail(image_id, auth)

@ar("/admin/images/{image_id:int}/", methods=["POST"])
def post(image_id: int, auth, **kwargs): return media_library.image_update(image_id, auth, **kwargs)

@ar("/admin/images/add/", methods=["POST"])
async def post(auth, file, **kwargs): return await media_library.image_upload(auth, file, **kwargs)

@ar("/admin/images/{image_id:int}/delete/confirm/")
def get(image_id: int, auth): return media_library.image_delete_confirm(image_id, auth)

@ar("/admin/images/{image_id:int}/delete/", methods=["POST"])
def post(image_id: int, auth): return media_library.image_delete_submit(image_id, auth)

@ar("/admin/images/chooser/")
def get(auth, field: str = '', q: str = ''): return media_library.image_chooser(auth, field, q)

# Documents
@ar("/admin/documents/")
def get(auth, page: int = 1, q: str = ''): return media_library.document_list(auth, page, q)

@ar("/admin/documents/{doc_id:int}/")
def get(doc_id: int, auth): return media_library.document_detail(doc_id, auth)

@ar("/admin/documents/{doc_id:int}/", methods=["POST"])
def post(doc_id: int, auth, **kwargs): return media_library.document_update(doc_id, auth, **kwargs)

@ar("/admin/documents/add/", methods=["POST"])
async def post(auth, file, **kwargs): return await media_library.document_upload(auth, file, **kwargs)

@ar("/admin/documents/{doc_id:int}/delete/", methods=["POST"])
def post(doc_id: int, auth): return media_library.document_delete_submit(doc_id, auth)

@ar("/admin/documents/chooser/")
def get(auth, field: str = '', q: str = ''): return media_library.document_chooser(auth, field, q)

# Users
@ar("/admin/users/")
def get(auth): return user_manager.user_list(auth)

@ar("/admin/users/add/")
def get(auth): return user_manager.user_add_form(auth)

@ar("/admin/users/add/", methods=["POST"])
def post(auth, **kwargs): return user_manager.user_add_submit(auth, **kwargs)

@ar("/admin/users/{user_id:int}/edit/")
def get(user_id: int, auth): return user_manager.user_edit_form(user_id, auth)

@ar("/admin/users/{user_id:int}/edit/", methods=["POST"])
def post(user_id: int, auth, **kwargs): return user_manager.user_edit_submit(user_id, auth, **kwargs)

@ar("/admin/users/{user_id:int}/delete/", methods=["POST"])
def post(user_id: int, auth): return user_manager.user_delete_submit(user_id, auth)

@ar("/admin/users/{user_id:int}/password/")
def get(user_id: int, auth): return user_manager.user_password_form(user_id, auth)

@ar("/admin/users/{user_id:int}/password/", methods=["POST"])
def post(user_id: int, auth, **kwargs): return user_manager.user_password_submit(user_id, auth, **kwargs)

# Snippets
@ar("/admin/snippets/")
def get(auth): return snippet_editor.snippet_type_list(auth)

@ar("/admin/snippets/{type_name}/")
def get(type_name: str, auth): return snippet_editor.snippet_instance_list(type_name, auth)

@ar("/admin/snippets/{type_name}/add/")
def get(type_name: str, auth): return snippet_editor.snippet_add_form(type_name, auth)

@ar("/admin/snippets/{type_name}/add/", methods=["POST"])
def post(type_name: str, auth, **kwargs): return snippet_editor.snippet_add_submit(type_name, auth, **kwargs)

@ar("/admin/snippets/{type_name}/{item_id:int}/edit/")
def get(type_name: str, item_id: int, auth): return snippet_editor.snippet_edit_form(type_name, item_id, auth)

@ar("/admin/snippets/{type_name}/{item_id:int}/edit/", methods=["POST"])
def post(type_name: str, item_id: int, auth, **kwargs): return snippet_editor.snippet_edit_submit(type_name, item_id, auth, **kwargs)

@ar("/admin/snippets/{type_name}/{item_id:int}/delete/", methods=["POST"])
def post(type_name: str, item_id: int, auth): return snippet_editor.snippet_delete_submit(type_name, item_id, auth)

# Settings
@ar("/admin/settings/")
def get(auth): return settings_admin.settings_edit(auth)

@ar("/admin/settings/", methods=["POST"])
def post(auth, **kwargs): return settings_admin.settings_save(auth, **kwargs)

# Reports
@ar("/admin/reports/")
def get(auth): return reports.reports_index(auth)

@ar("/admin/reports/types/")
def get(auth): return reports.page_types_report(auth)

@ar("/admin/reports/locked/")
def get(auth): return reports.locked_pages_report(auth)

@ar("/admin/reports/aging/")
def get(auth): return reports.aging_pages_report(auth)

@ar("/admin/reports/audit/")
def get(auth, page: int = 1): return reports.audit_log_report(auth, page)

# Search
@ar("/admin/search/")
def get(auth, q: str = ''):
    from app.search import search
    if not q: return Div()
    results = search(q, limit=10)
    if not results:
        return Div(P(f'No results for "{q}"', cls="text-sm text-gray-500 p-3"))
    from fasthtml.common import Div, A, Span, P
    items = [
        A(
            Span(r['content_type'], cls="text-xs text-gray-400 mr-2"),
            Span(r['title'], cls="text-sm"),
            href=f"/admin/pages/{r['object_id']}/edit/" if r['content_type'] == 'page'
                 else f"/admin/images/{r['object_id']}/" if r['content_type'] == 'image'
                 else f"/admin/documents/{r['object_id']}/",
            cls="block px-3 py-2 hover:bg-accent-dim rounded text-gray-700"
        ) for r in results
    ]
    return Div(*items, cls="bg-white border border-gray-200 rounded-lg shadow-lg p-1")
