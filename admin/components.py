from fasthtml.common import *

ADMIN_TW = """
tailwind.config = {
  theme: {
    extend: {
      colors: {
        sidebar:  { DEFAULT: '#1E1B4B', hover: '#2E2860', active: '#3B3680' },
        accent:   { DEFAULT: '#7C3AED', deep: '#2E1065', dim: '#EDE9FE', light: '#A78BFA' },
        success:  '#16A34A',
        warning:  '#CA8A04',
        danger:   '#DC2626',
      },
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'], mono: ['JetBrains Mono', 'monospace'] },
    },
  },
};
"""

SIDEBAR_ITEMS = [
    ('dashboard', 'Dashboard', '/admin/', '📊'),
    ('pages', 'Pages', '/admin/pages/', '📄'),
    ('images', 'Images', '/admin/images/', '🖼️'),
    ('documents', 'Documents', '/admin/documents/', '📎'),
    ('snippets', 'Snippets', '/admin/snippets/', '✂️'),
    ('forms', 'Form Submissions', '/admin/form-submissions/', '📝'),
    ('reports', 'Reports', '/admin/reports/', '📈'),
    ('users', 'Users', '/admin/users/', '👥'),
    ('settings', 'Settings', '/admin/settings/', '⚙️'),
]

def admin_page(title, *content, auth=None, breadcrumbs=None, active='dashboard', body=None):
    if body is not None:
        content = body if isinstance(body, (list, tuple)) else [body]
    return Html(
        Head(
            Meta(charset='utf-8'),
            Meta(name='viewport', content='width=device-width, initial-scale=1'),
            Title(f'{title} — FastHTML-CMS Admin'),
            Link(rel='preconnect', href='https://fonts.googleapis.com'),
            Link(rel='preconnect', href='https://fonts.gstatic.com', crossorigin=''),
            Link(rel='stylesheet', href='https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400&display=swap'),
            Script(src='https://cdn.tailwindcss.com'),
            Script(NotStr(ADMIN_TW)),
            Script(src='https://unpkg.com/htmx.org@2.0.4'),
            Link(rel='stylesheet', type='text/css', href='https://unpkg.com/trix@2.1.12/dist/trix.css'),
            Script(src='https://unpkg.com/trix@2.1.12/dist/trix.umd.min.js'),
            Script(src='https://cdn.jsdelivr.net/npm/sortablejs@1.15.6/Sortable.min.js'),
            Link(rel='stylesheet', href='/static/css/admin.css'),
        ),
        Body(
            Div(
                admin_sidebar(active),
                Div(
                    admin_header(auth),
                    Main(
                        admin_breadcrumbs(breadcrumbs) if breadcrumbs else '',
                        *content,
                        cls='p-6 max-w-7xl'
                    ),
                    cls='flex-1 flex flex-col min-h-screen overflow-auto bg-gray-50'
                ),
                cls='flex min-h-screen'
            ),
            Div(id='toast-container', cls='fixed top-4 right-4 z-50 flex flex-col gap-2'),
            Div(id='modal-container'),
            Script(src='/static/js/admin.js'),
            Script(src='/static/js/blocks.js'),
            Script(src='/static/js/choosers.js'),
        ),
        lang='en',
    )

def admin_sidebar(active='dashboard'):
    items = []
    for key, label, url, icon in SIDEBAR_ITEMS:
        is_active = key == active
        cls = "flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm transition-colors "
        cls += "bg-sidebar-active text-white" if is_active else "text-gray-300 hover:bg-sidebar-hover hover:text-white"
        items.append(
            A(Span(icon, cls="text-base"), Span(label), href=url, cls=cls)
        )
    return Nav(
        Div(
            A(Span("◆", cls="text-accent-light mr-2"), Span("FastHTML-CMS", cls="font-semibold text-white"),
              href="/admin/", cls="flex items-center text-lg px-4 py-4"),
            cls="border-b border-sidebar-hover mb-2"
        ),
        Div(*items, cls="flex flex-col gap-0.5 px-2"),
        Div(
            A("← View Site", href="/", target="_blank",
              cls="flex items-center gap-2 px-4 py-2 text-xs text-gray-400 hover:text-white transition-colors"),
            cls="mt-auto border-t border-sidebar-hover pt-2 pb-4 px-2"
        ),
        cls="w-60 bg-sidebar flex flex-col min-h-screen shrink-0"
    )

def admin_header(auth=None):
    name = auth.name if auth else 'User'
    return Header(
        Div(
            Div(
                Input(type='search', name='q', placeholder='Search pages, images, documents...',
                      hx_get='/admin/search/', hx_trigger='keyup changed delay:300ms',
                      hx_target='#search-results', hx_swap='innerHTML',
                      cls="w-80 px-3 py-1.5 text-sm bg-white border border-gray-200 rounded-lg focus:ring-2 focus:ring-accent focus:border-accent outline-none"),
                Div(id='search-results', cls="absolute top-full left-0 w-80 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 hidden"),
                cls="relative"
            ),
            Div(
                Span(name, cls="text-sm text-gray-600"),
                A("Logout", href="/admin/logout",
                  cls="text-xs text-gray-400 hover:text-accent transition-colors ml-3"),
                cls="flex items-center gap-2"
            ),
            cls="flex items-center justify-between w-full"
        ),
        cls="px-6 py-3 bg-white border-b border-gray-200"
    )

def admin_breadcrumbs(items):
    if not items: return ''
    parts = []
    for i, (label, url) in enumerate(items):
        if i > 0:
            parts.append(Span('/', cls="text-gray-300 mx-2"))
        if url and i < len(items) - 1:
            parts.append(A(label, href=url, cls="text-sm text-gray-500 hover:text-accent"))
        else:
            parts.append(Span(label, cls="text-sm text-gray-700 font-medium"))
    return Div(*parts, cls="flex items-center mb-4")

# ── Form field panels ─────────────────────────────────────────────────

def field_panel(name, label, value='', field_type='text', help_text='', required=False, options=None, **kw):
    label_el = Label(label, Span(' *', cls='text-red-500') if required else '',
                     cls="block text-sm font-medium text-gray-700 mb-1")
    if field_type == 'textarea':
        input_el = Textarea(value or '', name=name, rows=4, required=required,
                           cls="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-accent focus:border-accent outline-none", **kw)
    elif field_type == 'select' and options:
        opts = [Option(lbl, value=val, selected=(str(val) == str(value))) for val, lbl in options]
        input_el = Select(*opts, name=name, cls="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-accent focus:border-accent outline-none", **kw)
    elif field_type == 'checkbox':
        input_el = Div(
            Input(type='checkbox', name=name, checked=bool(value), value='1',
                  cls="w-4 h-4 text-accent border-gray-300 rounded focus:ring-accent", **kw),
            cls="flex items-center"
        )
    elif field_type == 'datetime':
        input_el = Input(type='datetime-local', name=name, value=value or '',
                        cls="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-accent focus:border-accent outline-none", **kw)
    elif field_type == 'date':
        input_el = Input(type='date', name=name, value=value or '',
                        cls="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-accent focus:border-accent outline-none", **kw)
    elif field_type == 'number':
        input_el = Input(type='number', name=name, value=value or '',
                        cls="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-accent focus:border-accent outline-none", **kw)
    elif field_type == 'hidden':
        return Input(type='hidden', name=name, value=value or '')
    else:
        input_el = Input(type=field_type, name=name, value=value or '', required=required,
                        cls="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-accent focus:border-accent outline-none", **kw)
    help_el = P(help_text, cls="text-xs text-gray-400 mt-1") if help_text else ''
    return Div(label_el, input_el, help_el, cls="mb-4")

def rich_text_panel(name, label, value='', help_text=''):
    return Div(
        Label(label, cls="block text-sm font-medium text-gray-700 mb-1"),
        Input(type='hidden', id=f'rt-{name}', name=name, value=value or ''),
        NotStr(f'<trix-editor input="rt-{name}" class="trix-content border border-gray-300 rounded-lg min-h-[200px] text-sm focus:ring-2 focus:ring-accent"></trix-editor>'),
        P(help_text, cls="text-xs text-gray-400 mt-1") if help_text else '',
        cls="mb-4"
    )

def image_chooser_panel(name, label, current_image=None):
    preview = ''
    if current_image:
        preview = Div(
            Img(src=f'/media/images/{current_image.file_path}', alt=current_image.alt_text,
                cls="w-32 h-32 object-cover rounded-lg border"),
            P(current_image.title, cls="text-xs text-gray-500 mt-1"),
            cls="mb-2", id=f'preview-{name}'
        )
    return Div(
        Label(label, cls="block text-sm font-medium text-gray-700 mb-1"),
        preview,
        Input(type='hidden', name=name, value=str(current_image.id) if current_image else '0', id=f'input-{name}'),
        Button("Choose Image", type="button",
               hx_get=f"/admin/images/chooser/?field={name}",
               hx_target="#modal-container", hx_swap="innerHTML",
               cls="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"),
        cls="mb-4"
    )

def page_chooser_panel(name, label, current_page=None):
    return Div(
        Label(label, cls="block text-sm font-medium text-gray-700 mb-1"),
        Div(
            Span(current_page.title if current_page else 'None selected', cls="text-sm", id=f'display-{name}'),
            cls="mb-2"
        ),
        Input(type='hidden', name=name, value=str(current_page.id) if current_page else '0', id=f'input-{name}'),
        Button("Choose Page", type="button",
               hx_get=f"/admin/pages/chooser/?field={name}",
               hx_target="#modal-container", hx_swap="innerHTML",
               cls="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"),
        cls="mb-4"
    )

# ── Layout components ─────────────────────────────────────────────────

def tab_panel(tabs, active_idx=0):
    buttons = []
    panels = []
    for i, (label, content) in enumerate(tabs):
        is_active = i == active_idx
        btn_cls = "px-4 py-2 text-sm font-medium border-b-2 transition-colors cursor-pointer "
        btn_cls += "border-accent text-accent" if is_active else "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
        buttons.append(
            Button(label, type="button", onclick=f"switchTab({i})",
                   cls=btn_cls, data_tab=str(i))
        )
        panel_cls = "py-6 " + ("" if is_active else "hidden")
        panels.append(Div(content, cls=panel_cls, id=f"tab-panel-{i}", data_panel=str(i)))
    return Div(
        Div(*buttons, cls="flex border-b border-gray-200 mb-0"),
        *panels
    )

def action_menu(primary_label, primary_action, *secondary_actions, method='post'):
    secondary = []
    for label, action, extra_cls in secondary_actions:
        secondary.append(
            Button(label, formaction=action, type='submit',
                   cls=f"block w-full text-left px-4 py-2 text-sm hover:bg-gray-50 {extra_cls}")
        )
    dropdown = ''
    if secondary:
        dropdown = Div(
            Button("▾", type="button", onclick="this.nextElementSibling.classList.toggle('hidden')",
                   cls="px-2 py-2 bg-accent text-white rounded-r-lg hover:bg-accent-deep border-l border-accent-deep"),
            Div(*secondary, cls="hidden absolute bottom-full right-0 mb-1 w-48 bg-white border border-gray-200 rounded-lg shadow-lg py-1"),
            cls="relative"
        )
    return Div(
        Div(
            Button(primary_label, formaction=primary_action, type='submit',
                   cls="px-6 py-2 bg-accent text-white text-sm font-medium rounded-lg hover:bg-accent-deep transition-colors" + (" rounded-r-none" if secondary else "")),
            dropdown,
            cls="flex"
        ),
        cls="fixed bottom-0 left-60 right-0 bg-white border-t border-gray-200 px-6 py-3 flex justify-end z-40"
    )

def status_badge(page):
    if page.live and page.has_unpublished_changes:
        return Span("Live + Draft", cls="px-2 py-0.5 text-xs font-medium rounded-full bg-amber-100 text-amber-700")
    elif page.live:
        return Span("Live", cls="px-2 py-0.5 text-xs font-medium rounded-full bg-green-100 text-green-700")
    elif page.go_live_at:
        return Span("Scheduled", cls="px-2 py-0.5 text-xs font-medium rounded-full bg-blue-100 text-blue-700")
    else:
        return Span("Draft", cls="px-2 py-0.5 text-xs font-medium rounded-full bg-gray-100 text-gray-600")

def pagination(total, page_num, per_page, base_url):
    total_pages = max(1, (total + per_page - 1) // per_page)
    if total_pages <= 1: return ''
    items = []
    if page_num > 1:
        items.append(A('←', href=f"{base_url}?page={page_num-1}",
                       cls="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"))
    items.append(Span(f"Page {page_num} of {total_pages}", cls="text-sm text-gray-500 px-3"))
    if page_num < total_pages:
        items.append(A('→', href=f"{base_url}?page={page_num+1}",
                       cls="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"))
    return Div(*items, cls="flex items-center justify-center gap-2 mt-6")

def stat_card(label, value, icon=''):
    return Div(
        Div(Span(icon, cls="text-2xl") if icon else '', cls="mb-2"),
        P(str(value), cls="text-3xl font-semibold text-gray-900"),
        P(label, cls="text-sm text-gray-500 mt-1"),
        cls="bg-white rounded-xl border border-gray-200 p-5"
    )

def empty_state(icon, title, message='', action_url='', action_label=''):
    return Div(
        Span(icon, cls="text-4xl mb-3 block"),
        H3(title, cls="text-lg font-medium text-gray-700 mb-1"),
        P(message, cls="text-sm text-gray-500 mb-4") if message else '',
        A(action_label, href=action_url,
          cls="px-4 py-2 bg-accent text-white text-sm rounded-lg hover:bg-accent-deep") if action_url else '',
        cls="text-center py-16"
    )

def confirm_dialog(title, message, action_url, action_label='Delete', method='post'):
    return Div(
        Div(
            Div(
                H3(title, cls="text-lg font-semibold mb-2"),
                P(message, cls="text-sm text-gray-600 mb-6"),
                Div(
                    Button("Cancel", type="button", onclick="this.closest('#modal-container').innerHTML=''",
                           cls="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"),
                    Form(
                        Button(action_label, type="submit",
                               cls="px-4 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700"),
                        method=method, action=action_url,
                    ),
                    cls="flex justify-end gap-3"
                ),
                cls="bg-white rounded-2xl p-6 max-w-md w-full shadow-xl"
            ),
            cls="fixed inset-0 bg-black/50 flex items-center justify-center z-50",
            onclick="if(event.target===this)this.remove()"
        ),
    )

def toast(message, type='success'):
    bg = {'success': 'bg-green-600', 'error': 'bg-red-600', 'warning': 'bg-amber-600', 'info': 'bg-blue-600'}.get(type, 'bg-gray-600')
    return Div(
        Span(message, cls="text-white text-sm"),
        cls=f"{bg} px-4 py-2 rounded-lg shadow-lg animate-fade-in",
        hx_swap_oob="beforeend:#toast-container"
    )
