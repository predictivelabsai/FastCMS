from fasthtml.common import *
from dotenv import load_dotenv
import os

load_dotenv()

from app.db import setup_fts
from app.auth import auth_before, hash_password, login_page, login_submit, logout
from app.landing import landing_page
from app.developer import developer_page
from app import account_auth, google_auth
from app.fastapi_api import api
from app.db import now, users
from app.pages import resolve_page_by_url, check_scheduled_pages
from app.components import render_public_page
from app.blocks import block_add_html
from app.search import search as fts_search
from app import api as api_module
from app import snippets as _snippets  # noqa: triggers registration
from admin import ar as admin_router

# ── App setup ─────────────────────────────────────────────────────────

beforeware = Beforeware(
    auth_before,
    skip=[r'/favicon\.ico', r'/static/.*', r'/media/.*', r'/screenshots/.*',
          r'.*\.css', r'.*\.js', r'.*\.png', r'.*\.gif', r'.*\.jpg',
          r'/admin/login', r'/auth/google', r'/auth/google/callback', r'/auth/local/.*',
          r'/api/.*', r'^/$', r'^/developers$', r'^/swagger\.json$',
          r'^/help$', r'^/form-submit/.*']
)

app, rt = fast_app(
    live=False,
    pico=False,
    static_path='static',
    before=beforeware,
    secret_key=os.getenv('SECRET_KEY', 'change-me-in-production'),
    hdrs=(Meta(name='viewport', content='width=device-width, initial-scale=1'),),
)
app.mount('/api', api)


@rt('/swagger.json', methods=['GET'])
def swagger_schema():
    return JSONResponse(api.openapi())


@rt('/developers', methods=['GET'])
def developers():
    return developer_page()

setup_fts()
admin_router.to_app(app)


def establish_local_user(sess, account):
    matching = users(where='email=?', where_args=[account['email']])
    if matching:
        user = matching[0]
    else:
        user = users.insert(
            email=account['email'],
            name=account['name'],
            password_hash=hash_password(os.urandom(32).hex()),
            role='editor',
            is_active=True,
            created_at=now(),
        )
    if not user.is_active:
        raise HTTPException(403, 'Account is disabled')
    sess['user_id'] = user.id


account_auth.register_fasthtml_routes(
    rt, app_name="FastCMS", success_path="/admin/", on_login=establish_local_user
)

# ── Auth routes ───────────────────────────────────────────────────────

@rt('/admin/login')
def login_get(): return login_page()

@rt('/admin/login', methods=['POST'])
def login_post(email: str = '', password: str = '', sess=None):
    return login_submit(email, password, sess)

@rt('/admin/logout')
def logout_get(sess): return logout(sess)

@rt('/auth/google')
def google_start(sess, request):
    if not google_auth.enabled():
        return RedirectResponse('/admin/login?error=Google+sign-in+is+not+configured', status_code=303)
    state = google_auth.new_state()
    sess['google_oauth_state'] = state
    return RedirectResponse(google_auth.authorize_url(request, state), status_code=303)

@rt('/auth/google/callback')
def google_callback(sess, request, code: str = '', state: str = '', error: str = ''):
    if error or not code or state != sess.pop('google_oauth_state', None):
        return RedirectResponse('/admin/login?error=Google+sign-in+failed', status_code=303)
    identity = google_auth.exchange(request, code)
    matching = users(where='email=?', where_args=[identity['email']]) if identity else []
    allowlist_configured = bool(
        os.getenv('GOOGLE_ALLOWED_DOMAINS', '').strip()
        or os.getenv('GOOGLE_ALLOWED_EMAILS', '').strip()
    )
    if identity and not matching and allowlist_configured:
        user = users.insert(
            email=identity['email'],
            name=identity['name'],
            password_hash=hash_password(os.urandom(32).hex()),
            role='admin',
            is_active=True,
            created_at=now(),
        )
        matching = [user]
    if not matching or not matching[0].is_active:
        return RedirectResponse('/admin/login?error=Google+account+is+not+authorised', status_code=303)
    account_auth.accounts.link_google(identity['email'], identity['name'])
    sess['user_id'] = matching[0].id
    return RedirectResponse('/admin/', status_code=303)

# ── Static file serving ──────────────────────────────────────────────

@rt('/media/{path:path}')
async def serve_media(path: str):
    from starlette.responses import FileResponse
    file_path = f'media/{path}'
    if not os.path.exists(file_path): raise HTTPException(404)
    return FileResponse(file_path)

@rt('/screenshots/{path:path}')
async def serve_screenshots(path: str):
    from starlette.responses import FileResponse
    file_path = f'screenshots/{path}'
    if not os.path.exists(file_path): raise HTTPException(404)
    return FileResponse(file_path)

# ── Block add (HTMX endpoint) ────────────────────────────────────────

@rt('/admin/pages/block/add/')
def block_add(field: str = 'body', type: str = 'paragraph', idx: int = 0):
    return block_add_html(field, type, idx)

# ── Form submission ───────────────────────────────────────────────────

@rt('/form-submit/{page_id:int}', methods=['POST'])
async def form_submit(page_id: int, req):
    from app.forms import validate_submission, save_submission
    from app.db import pages
    import json
    form_data = dict(await req.form())
    errors = validate_submission(page_id, form_data)
    if errors:
        p = pages[page_id]
        return render_public_page(p)
    save_submission(page_id, form_data, req.client.host if req.client else '')
    p = pages[page_id]
    extra = json.loads(p.extra_json) if p.extra_json else {}
    thank_you = extra.get('thank_you_text', '<p>Thank you for your submission!</p>')
    from app.components import public_page
    return public_page(p.title,
        H1(p.title, cls="text-4xl font-bold mb-6"),
        Div(NotStr(thank_you), cls="prose"),
    )

# ── JSON API ──────────────────────────────────────────────────────────

@rt('/api/v1/pages/')
def api_pages(child_of: int = 0, type: str = '', search: str = '', fields: str = '',
              order: str = '-first_published_at', limit: int = 20, offset: int = 0):
    return api_module.api_pages_list(child_of, type, search, fields, order, limit, offset)

@rt('/api/v1/pages/{page_id:int}/')
def api_page(page_id: int): return api_module.api_page_detail(page_id)

@rt('/api/v1/images/')
def api_images(collection: int = 0, tags: str = '', search: str = '', limit: int = 20, offset: int = 0):
    return api_module.api_images_list(collection, tags, search, limit, offset)

@rt('/api/v1/images/{image_id:int}/')
def api_image(image_id: int): return api_module.api_image_detail(image_id)

@rt('/api/v1/documents/')
def api_documents(collection: int = 0, search: str = '', limit: int = 20, offset: int = 0):
    return api_module.api_documents_list(collection, search, limit, offset)

@rt('/api/v1/documents/{doc_id:int}/')
def api_document(doc_id: int): return api_module.api_document_detail(doc_id)

@rt('/api/v1/search/')
def api_search(query: str = '', type: str = '', limit: int = 20, offset: int = 0):
    return api_module.api_search(query, type, limit, offset)

# ── CSV export ────────────────────────────────────────────────────────

@rt('/admin/form-submissions/{page_id:int}/csv/')
def form_csv(page_id: int, auth):
    from app.forms import export_submissions_csv
    from starlette.responses import Response
    csv_data = export_submissions_csv(page_id)
    return Response(csv_data, media_type='text/csv',
                   headers={'Content-Disposition': f'attachment; filename=submissions-{page_id}.csv'})

# ── Help / User Guide ─────────────────────────────────────────────────

@rt('/help')
def help_page():
    return _help_page()

@rt('/admin/help')
def admin_help_page(auth):
    return _help_page()

def _help_page():
    sections = [
        ("Getting Started", "getting-started", [
            ("Log in at <code>/admin/login</code> with your email and password.", None),
            ("Edit the <strong>Home</strong> page from the Pages section.", None),
            ("Upload images to the <strong>Media Library</strong>.", None),
            ("Configure your site in <strong>Settings</strong>.", None),
        ]),
        ("Dashboard", "dashboard", [
            ("The dashboard shows stats (pages, images, documents, users), recent edits, drafts awaiting review, and quick action buttons.", "screenshots/02-dashboard.png"),
        ]),
        ("Managing Pages", "pages", [
            ("The <strong>Page Explorer</strong> shows your page tree. Click a page title to see its children, or click Edit to modify it.", "screenshots/03-page-explorer.png"),
            ("Click <strong>+ PageType</strong> buttons to create new pages under the current parent.", None),
            ("Pages can be <strong>Live</strong> (published), <strong>Draft</strong> (saved but not public), <strong>Scheduled</strong> (will go live at a set time), or <strong>Live + Draft</strong> (published with unpublished changes).", None),
        ]),
        ("Page Editor", "editor", [
            ("The editor has three tabs: <strong>Content</strong> (title, slug, blocks), <strong>Promote</strong> (SEO), and <strong>Settings</strong> (scheduling, menu visibility).", "screenshots/05-page-editor.png"),
            ("The <strong>slug</strong> auto-generates from the title. You can override it manually.", None),
            ("Use the action menu (bottom-right) to Save Draft, Publish, Unpublish, Lock, View Revisions, or Delete.", None),
        ]),
        ("Content Blocks (StreamField)", "blocks", [
            ("The page body uses composable content blocks. Click <strong>+ Add Block</strong> to insert a new block.", None),
            ("<strong>Heading</strong> &mdash; H2/H3/H4 with text", None),
            ("<strong>Paragraph</strong> &mdash; Rich text with formatting toolbar (bold, italic, links, lists)", None),
            ("<strong>Image</strong> &mdash; Choose from media library with caption and alt text", None),
            ("<strong>Embed</strong> &mdash; Paste a URL or embed HTML (YouTube, Vimeo, etc.)", None),
            ("<strong>Quote</strong> &mdash; Blockquote with attribution", None),
            ("<strong>Code</strong> &mdash; Code snippet with language selector", None),
            ("<strong>List, Table, Document, Raw HTML</strong> &mdash; Additional block types", None),
            ("Drag the <strong>&#x22EE;&#x22EE;</strong> handle to reorder blocks. Click <strong>&times;</strong> to remove.", None),
        ]),
        ("Images & Documents", "media", [
            ("Upload images and documents from their respective sections in the sidebar.", "screenshots/09-images.png"),
            ("Images are automatically resized into thumbnails. Set alt text and tags for organization.", None),
            ("Use the <strong>Image Chooser</strong> modal (inside the page editor) to select or upload images inline.", None),
        ]),
        ("Snippets", "snippets", [
            ("Snippets are reusable content fragments: NavigationMenu, FooterContent, SocialLink, Testimonial, FAQ.", "screenshots/11-snippets.png"),
            ("Click a snippet type to create, edit, or delete instances.", None),
        ]),
        ("Users & Roles", "users", [
            ("<strong>Admin</strong> &mdash; Full access: edit, publish, delete, manage users and settings.", None),
            ("<strong>Editor</strong> &mdash; Edit and publish pages, upload media.", None),
            ("<strong>Moderator</strong> &mdash; Edit pages and upload media, but cannot publish or delete.", None),
        ]),
        ("Site Settings", "settings", [
            ("Configure site name, tagline, contact info, social media links, analytics, and custom CSS/JS.", "screenshots/13-settings.png"),
        ]),
        ("JSON API", "api", [
            ("<code>GET /api/v1/pages/</code> &mdash; List published pages (filter: child_of, type, search, order, limit, offset)", None),
            ("<code>GET /api/v1/pages/{id}/</code> &mdash; Single page with body blocks", None),
            ("<code>GET /api/v1/images/</code> &mdash; List images with rendition URLs", None),
            ("<code>GET /api/v1/documents/</code> &mdash; List documents", None),
            ("<code>GET /api/v1/search/?query=term</code> &mdash; Full-text search", None),
        ]),
        ("Keyboard Shortcuts", "shortcuts", [
            ("<code>Ctrl+S</code> / <code>Cmd+S</code> &mdash; Save draft in page editor", None),
            ("<code>Escape</code> &mdash; Close modal dialogs", None),
        ]),
    ]

    toc = Ul(*[Li(A(title, href=f"#section-{anchor}", cls="text-purple-600 hover:underline"), cls="mb-1")
               for title, anchor, _ in sections], cls="mb-10 list-disc ml-6")

    content_sections = []
    for title, anchor, items in sections:
        els = [Li(NotStr(text), cls="mb-2 text-gray-700 leading-relaxed") for text, img in items]
        section_content = [
            H2(title, id=f"section-{anchor}", cls="text-2xl font-semibold mt-10 mb-4 text-gray-900"),
            Ul(*els, cls="list-disc ml-6 mb-4"),
        ]
        if items and items[0][1]:
            section_content.append(
                Img(src=f"/{items[0][1]}", alt=title, cls="rounded-xl border border-gray-200 shadow-sm max-w-full mb-6")
            )
        content_sections.extend(section_content)

    return Html(
        Head(
            Meta(charset='utf-8'),
            Meta(name='viewport', content='width=device-width, initial-scale=1'),
            Title('User Guide — FastHTML-CMS'),
            Link(rel='stylesheet', href='https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'),
            Script(src='https://cdn.tailwindcss.com'),
        ),
        Body(
            Header(
                Div(
                    A(Span("◆", cls="text-purple-600 mr-2"), "FastHTML-CMS", href="/", cls="text-lg font-semibold text-gray-900"),
                    Div(
                        A("Home", href="/", cls="text-sm text-gray-500 hover:text-gray-900"),
                        A("Admin", href="/admin/", cls="text-sm text-gray-500 hover:text-gray-900 ml-4"),
                        cls="flex items-center"
                    ),
                    cls="max-w-3xl mx-auto px-6 flex items-center justify-between h-16"
                ),
                cls="border-b border-gray-200"
            ),
            Main(
                Div(
                    Img(src="/screenshots/admin-tour.gif", alt="FastHTML-CMS Admin Tour",
                        cls="rounded-xl border border-gray-200 shadow-md mb-8 w-full"),
                    cls="mb-2"
                ),
                H1("User Guide", cls="text-4xl font-bold mb-2 text-gray-900"),
                P("Everything you need to know to manage your FastHTML-CMS website.", cls="text-lg text-gray-500 mb-8"),
                Div(H3("Contents", cls="text-lg font-semibold mb-3"), toc, cls="bg-gray-50 rounded-xl p-6 mb-8 border border-gray-100"),
                *content_sections,
                Div(
                    H2("Need Help?", cls="text-2xl font-semibold mb-4"),
                    P(A("GitHub", href="https://github.com/predictivelabs/FastHTML-CMS", cls="text-purple-600 hover:underline"),
                      " · ",
                      A("Predictive Labs", href="https://predictivelabs.ai", cls="text-purple-600 hover:underline"),
                      cls="text-gray-600"),
                    cls="mt-12 mb-8 pt-8 border-t border-gray-200"
                ),
                cls="max-w-3xl mx-auto px-6 py-12"
            ),
            cls="min-h-screen bg-white text-gray-900 font-[Inter] antialiased"
        ),
    )

# ── Homepage ──────────────────────────────────────────────────────────

@rt('/')
def homepage():
    page = resolve_page_by_url('/')
    if page:
        return render_public_page(page)
    return landing_page()

# ── Public page catch-all (MUST be last) ──────────────────────────────

@rt('/{path:path}')
def serve_page(path: str):
    url_path = f'/{path}/'
    page = resolve_page_by_url(url_path)
    if not page:
        raise HTTPException(404)
    return render_public_page(page)

# ── Fallback landing page ─────────────────────────────────────────────

def _landing_page():
    return Html(
        Head(
            Meta(charset='utf-8'),
            Meta(name='viewport', content='width=device-width, initial-scale=1'),
            Title('FastHTML-CMS'),
            Script(src='https://cdn.tailwindcss.com'),
            Link(rel='stylesheet', href='https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'),
        ),
        Body(
            Div(
                Div(
                    Span("◆", cls="text-purple-600 text-3xl mr-3"),
                    Span("FastHTML-CMS", cls="text-3xl font-bold"),
                    cls="flex items-center justify-center mb-6"
                ),
                P("Your CMS is running. Set up your site:", cls="text-gray-500 text-center mb-8"),
                Div(
                    A("Open Admin Panel →", href="/admin/",
                      cls="px-6 py-3 bg-purple-600 text-white rounded-xl font-medium hover:bg-purple-700 transition-colors"),
                    cls="text-center"
                ),
                Pre(Code("python setup.py  # if not done yet", cls="text-purple-400"),
                    cls="mt-8 bg-gray-900 text-sm rounded-xl p-4 max-w-sm mx-auto"),
                cls="max-w-md mx-auto p-12"
            ),
            cls="min-h-screen flex items-center justify-center bg-gray-50 font-[Inter]"
        ),
    )

serve()
