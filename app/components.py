import json
from fasthtml.common import *
from app.blocks import render_blocks
from app.settings import get_all_settings
from app.db import pages

def public_page(title, *content, description=''):
    settings = get_all_settings()
    return Html(
        Head(
            Meta(charset='utf-8'),
            Meta(name='viewport', content='width=device-width, initial-scale=1'),
            Meta(name='description', content=description or settings.get('default_meta_description', '')),
            Title(f"{title} — {settings.get('site_name', 'FastHTML-CMS')}"),
            Link(rel='preconnect', href='https://fonts.googleapis.com'),
            Link(rel='preconnect', href='https://fonts.gstatic.com', crossorigin=''),
            Link(rel='stylesheet', href='https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap'),
            Script(src='https://cdn.tailwindcss.com'),
            Style(NotStr(settings.get('custom_css', ''))) if settings.get('custom_css') else '',
            Script(NotStr(settings.get('analytics_tracking_code', ''))) if settings.get('analytics_tracking_code') else '',
        ),
        Body(
            public_header(settings),
            Main(*content, cls="max-w-4xl mx-auto px-6 py-12"),
            public_footer(settings),
            Script(NotStr(settings.get('custom_js', ''))) if settings.get('custom_js') else '',
            cls="min-h-screen bg-white text-gray-900 font-sans antialiased"
        ),
        lang='en',
    )

def public_header(settings):
    site_name = settings.get('site_name', 'FastHTML-CMS')
    menu_pages = pages(where="show_in_menus=1 AND live=1 AND depth=2", order_by='path')
    nav_items = [A(p.title, href=p.url_path, cls="text-sm text-gray-600 hover:text-gray-900") for p in menu_pages]
    return Header(
        Div(
            A(site_name, href="/", cls="text-lg font-semibold text-gray-900"),
            Nav(*nav_items, cls="flex items-center gap-6") if nav_items else '',
            cls="max-w-4xl mx-auto px-6 flex items-center justify-between h-16"
        ),
        cls="border-b border-gray-200"
    )

def public_footer(settings):
    site_name = settings.get('site_name', 'FastHTML-CMS')
    email = settings.get('contact_email', '')
    return Footer(
        Div(
            P(f"© 2025 {site_name}", cls="text-sm text-gray-400"),
            A(email, href=f"mailto:{email}", cls="text-sm text-gray-400 hover:text-gray-600") if email else '',
            cls="max-w-4xl mx-auto px-6 py-8 flex items-center justify-between"
        ),
        cls="border-t border-gray-200"
    )

def render_public_page(page):
    blocks = render_blocks(page.body_json)
    desc = page.search_description or ''
    title = page.seo_title or page.title

    if page.content_type == 'BlogIndexPage':
        child_pages = pages(where="path LIKE ? AND depth=? AND live=1",
                           where_args=[page.path + '%', page.depth + 1],
                           order_by='first_published_at DESC')
        blog_list = Div(
            *[Div(
                A(H3(cp.title, cls="text-xl font-semibold text-gray-900 hover:text-accent"),
                  href=cp.url_path),
                P(cp.search_description or '', cls="text-sm text-gray-500 mt-1"),
                P(cp.first_published_at[:10] if cp.first_published_at else '', cls="text-xs text-gray-400 mt-2"),
                cls="pb-6 mb-6 border-b border-gray-100"
            ) for cp in child_pages],
            cls="mt-8"
        )
        return public_page(title,
            H1(page.title, cls="text-4xl font-bold mb-4"),
            *blocks,
            blog_list,
            description=desc
        )

    if page.content_type == 'FormPage':
        from app.forms import render_form
        extra = json.loads(page.extra_json) if page.extra_json else {}
        return public_page(title,
            H1(page.title, cls="text-4xl font-bold mb-4"),
            *blocks,
            Div(NotStr(extra.get('intro', '')), cls="prose mb-6") if extra.get('intro') else '',
            render_form(page.id, f'/form-submit/{page.id}'),
            description=desc
        )

    return public_page(title,
        H1(page.title, cls="text-4xl font-bold mb-6"),
        *blocks,
        description=desc
    )
