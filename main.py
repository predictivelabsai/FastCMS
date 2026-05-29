from fasthtml.common import *

SITE_NAME = "FastHTML-CMS"
SITE_TAGLINE = "Modern content management, radically simplified."
DEMO_URL = "https://fastcms.predictivelabs.ai"
ABOUT_URL = "https://predictivelabs.ai"
GITHUB_URL = "https://github.com/predictivelabs/FastHTML-CMS"

TAILWIND_CONFIG = """
tailwind.config = {
  theme: {
    extend: {
      colors: {
        bg:     { DEFAULT: '#FAFAFA', elevated: '#FFFFFF', raised: '#F3F1F9' },
        ink:    { DEFAULT: '#1E1B4B', muted: '#64748B', dim: '#94A3B8' },
        line:   { DEFAULT: '#E2E8F0', bright: '#CBD5E1' },
        accent: { DEFAULT: '#7C3AED', dim: '#EDE9FE', deep: '#2E1065', cyan: '#06B6D4' },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'monospace'],
      },
      letterSpacing: { tightest: '-0.04em', tighter: '-0.025em' },
    },
  },
};
"""

app, rt = fast_app(
    live=False,
    pico=False,
    static_path="static",
    hdrs=(
        Meta(name='viewport', content='width=device-width, initial-scale=1'),
        Meta(name='description', content=f'{SITE_NAME} — {SITE_TAGLINE}'),
    ),
)


# -- Shared components --

def Eyebrow(text, *, cls=""):
    return Span(text, cls=f"font-mono text-[11px] tracking-[0.18em] uppercase text-accent {cls}".strip())

def Heading(level, text, *, cls=""):
    tag = {1: H1, 2: H2, 3: H3, 4: H4}[level]
    base = {
        1: "text-4xl sm:text-5xl md:text-7xl font-medium tracking-tightest text-ink leading-[1.05] md:leading-[1.02]",
        2: "text-2xl sm:text-3xl md:text-5xl font-medium tracking-tighter text-ink leading-[1.12] md:leading-[1.08]",
        3: "text-lg sm:text-xl md:text-2xl font-medium tracking-tight text-ink",
        4: "text-base md:text-lg font-medium text-ink",
    }[level]
    return tag(text, cls=f"{base} {cls}".strip())

def Btn(text, *, href="#", primary=True, cls=""):
    base = "inline-flex items-center gap-2 px-5 py-3 rounded-full text-sm font-medium transition-all duration-200"
    if primary:
        style = "bg-accent text-white hover:bg-accent-deep shadow-[0_0_0_1px_#7C3AED] hover:shadow-[0_0_0_1px_#2E1065]"
    else:
        style = "bg-transparent text-ink border border-line-bright hover:border-accent hover:text-accent"
    return A(text, Span("→", cls="text-base"), href=href, cls=f"{base} {style} {cls}".strip())

def Section_(*content, cls="", **kw):
    return Section(Div(*content, cls="max-w-7xl mx-auto px-5 md:px-6"), cls=f"py-14 md:py-20 lg:py-24 {cls}".strip(), **kw)

def _page(title, *content):
    return Html(
        Head(
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            Meta(name="description", content=f"{SITE_NAME} — {SITE_TAGLINE}"),
            Title(f"{title} · {SITE_NAME}"),
            Link(rel="preconnect", href="https://fonts.googleapis.com"),
            Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
            Link(rel="stylesheet",
                 href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap"),
            Script(src="https://cdn.tailwindcss.com"),
            Script(NotStr(TAILWIND_CONFIG)),
        ),
        Body(
            _navbar(),
            Main(*content, cls="min-h-screen"),
            _footer(),
            cls="bg-bg text-ink font-sans antialiased",
        ),
        lang="en",
    )


def _navbar():
    return Nav(
        Div(
            A(
                Span("◆", cls="text-accent mr-2"),
                Span(SITE_NAME, cls="font-medium tracking-tight"),
                href="/",
                cls="flex items-center text-ink text-base hover:text-accent transition-colors",
            ),
            Div(
                A("Features", href="#features", cls="text-sm text-ink-muted hover:text-ink transition-colors hidden lg:inline"),
                A("About Us", href=ABOUT_URL, target="_blank", cls="text-sm text-ink-muted hover:text-ink transition-colors hidden lg:inline"),
                cls="flex items-center gap-7",
            ),
            Div(
                A("Demo", href=DEMO_URL, target="_blank",
                  cls="hidden lg:inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium text-ink border border-line-bright hover:border-accent hover:text-accent transition-colors"),
                A("Get Started", href="#get-started",
                  cls="inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs font-medium bg-accent text-white hover:bg-accent-deep transition-colors"),
                cls="flex items-center gap-3",
            ),
            cls="max-w-7xl mx-auto px-5 md:px-6 flex items-center justify-between h-16 gap-4",
        ),
        cls="sticky top-0 z-50 backdrop-blur-md bg-bg/80 border-b border-line",
    )


def _footer():
    return Footer(
        Div(
            Div(
                Div(
                    A(Span("◆", cls="text-accent mr-2"), Span(SITE_NAME, cls="font-medium text-ink"),
                      href="/", cls="flex items-center text-lg mb-4"),
                    P(SITE_TAGLINE, cls="text-ink-muted text-sm max-w-xs mb-5"),
                    P("Open source CMS built with FastHTML and SQLite. No complexity, just content.",
                      cls="text-ink-dim text-xs leading-relaxed max-w-xs"),
                ),
                Div(
                    H4("Project", cls="text-xs font-mono tracking-[0.18em] uppercase text-ink-muted mb-5"),
                    Ul(
                        Li(A("Features", href="#features", cls="text-sm text-ink hover:text-accent"), cls="mb-2"),
                        Li(A("Documentation", href="#get-started", cls="text-sm text-ink hover:text-accent"), cls="mb-2"),
                        Li(A("GitHub", href=GITHUB_URL, target="_blank", cls="text-sm text-ink hover:text-accent"), cls="mb-2"),
                    ),
                ),
                Div(
                    H4("Company", cls="text-xs font-mono tracking-[0.18em] uppercase text-ink-muted mb-5"),
                    Ul(
                        Li(A("About Us", href=ABOUT_URL, target="_blank", cls="text-sm text-ink hover:text-accent"), cls="mb-2"),
                        Li(A("Demo", href=DEMO_URL, target="_blank", cls="text-sm text-ink hover:text-accent"), cls="mb-2"),
                        Li(A("Contact", href="mailto:info@predictivelabs.ai", cls="text-sm text-ink hover:text-accent"), cls="mb-2"),
                    ),
                ),
                Div(
                    H4("Community", cls="text-xs font-mono tracking-[0.18em] uppercase text-ink-muted mb-5"),
                    Ul(
                        Li(A("GitHub", href=GITHUB_URL, target="_blank", cls="text-sm text-ink hover:text-accent"), cls="mb-2"),
                        Li(A("FastHTML", href="https://fastht.ml", target="_blank", cls="text-sm text-ink hover:text-accent"), cls="mb-2"),
                    ),
                ),
                cls="grid grid-cols-2 md:grid-cols-4 gap-10",
            ),
            Div(
                Div("© 2025 FastHTML-CMS · ", A("Predictive Labs Ltd", href=ABOUT_URL, target="_blank", cls="text-accent hover:text-ink"), ".",
                    cls="text-ink-dim text-xs"),
                A("MIT License", href=GITHUB_URL, cls="text-ink-dim text-xs hover:text-accent"),
                cls="mt-10 md:mt-14 pt-6 border-t border-line flex items-start md:items-center justify-between flex-wrap gap-4",
            ),
            cls="max-w-7xl mx-auto px-5 md:px-6",
        ),
        cls="py-12 md:py-16 border-t border-line bg-bg-elevated",
    )


def _stat(value, caption):
    return Div(
        Span(value, cls="text-2xl md:text-3xl font-medium tracking-tighter text-ink"),
        P(caption, cls="text-ink-muted text-xs md:text-sm mt-1"),
    )


def _feature_card(icon, title, desc):
    return Article(
        Div(
            Span(icon, cls="text-accent text-xl"),
            cls="mb-4",
        ),
        H4(title, cls="text-ink font-medium mb-1.5"),
        P(desc, cls="text-ink-muted text-sm leading-relaxed"),
        cls="p-6 rounded-2xl bg-bg-elevated border border-line hover:border-accent/50 transition-colors h-full",
    )


# -- Homepage --

@rt("/")
def index():
    hero = Section(
        Div(
            Div(cls="absolute inset-0 bg-gradient-to-b from-accent-dim/40 via-transparent to-bg pointer-events-none"),
            Div(
                Eyebrow("Open Source CMS"),
                H1(
                    Span("Create content that "),
                    Span("flies", cls="text-accent"),
                    Span("."),
                    cls="mt-5 md:mt-6 text-[40px] sm:text-5xl md:text-7xl lg:text-[84px] font-medium tracking-tightest text-ink leading-[1.05] md:leading-[1.02] max-w-5xl",
                ),
                P("The modern Python CMS built on FastHTML and SQLite. Lightweight, fast, and enterprise-ready — with zero external dependencies.",
                  cls="mt-6 md:mt-8 text-base md:text-xl text-ink-muted max-w-2xl leading-relaxed"),
                Div(
                    Btn("Try the Demo", href=DEMO_URL, primary=True),
                    Btn("Get Started", href="#get-started", primary=False),
                    cls="mt-8 md:mt-10 flex items-center gap-3 flex-wrap",
                ),
                Div(
                    Span("$", cls="text-ink-dim mr-2"),
                    Span("pip install fasthtml-cms", cls="text-accent-cyan"),
                    cls="mt-8 inline-flex items-center px-5 py-3 rounded-xl bg-ink text-sm font-mono",
                ),
                cls="relative z-30 max-w-7xl mx-auto px-5 md:px-6 py-24 md:py-0",
            ),
            cls="relative min-h-[80vh] md:min-h-[86vh] flex items-center overflow-hidden bg-bg",
        ),
        Div(
            Div(
                _stat("0", "external services"),
                _stat("1", "Python file to start"),
                _stat("60s", "to first page"),
                _stat("SQLite", "embedded database"),
                cls="max-w-7xl mx-auto px-5 md:px-6 py-5 md:py-6 grid grid-cols-2 md:grid-cols-4 gap-6",
            ),
            cls="border-y border-line bg-bg-elevated/60",
        ),
    )

    tech_strip = Section_(
        Div(
            Eyebrow("Built on"),
            Div(
                *[Span(name, cls="font-mono text-[11px] tracking-widest uppercase text-ink-dim") for name in
                  ["FastHTML", "SQLite", "HTMX", "Starlette", "Uvicorn", "Python", "Pillow"]],
                cls="mt-4 flex flex-wrap gap-x-8 gap-y-2",
            ),
        ),
        cls="border-b border-line",
    )

    features = Section_(
        Div(
            Eyebrow("Features"),
            Heading(2, "Everything you need to manage content", cls="mt-3 max-w-3xl mb-2"),
            P("Inspired by Wagtail, rebuilt for simplicity. All the power, none of the complexity.",
              cls="mt-2 text-ink-muted text-base max-w-2xl leading-relaxed mb-10"),
        ),
        Div(
            _feature_card("📄", "Page Tree", "Hierarchical page management with intuitive tree navigation, drag-and-drop reordering, and nested page types."),
            _feature_card("✏️", "Rich Text Editor", "WYSIWYG editing with image embedding, links, and formatting — all server-rendered with HTMX."),
            _feature_card("🧱", "Content Blocks", "StreamField-inspired composable blocks: text, image, embed, table, code, and custom blocks."),
            _feature_card("🖼️", "Media Library", "Upload, organize, and reuse images and documents with collections, tagging, and focal points."),
            _feature_card("🔍", "Full-Text Search", "SQLite FTS5 powered search across all content — pages, images, documents, and snippets."),
            _feature_card("📋", "Draft & Publish", "Draft, review, schedule, and publish workflow with full revision history and diff comparison."),
            _feature_card("👥", "User Roles", "Role-based access control: Admin, Editor, Moderator — with per-collection permissions."),
            _feature_card("🔌", "JSON API", "Headless CMS capability with RESTful API endpoints for pages, images, and documents."),
            _feature_card("💾", "Zero Config DB", "SQLite embedded storage. No PostgreSQL, no Redis, no Docker. Just Python and a file."),
            cls="grid sm:grid-cols-2 lg:grid-cols-3 gap-4",
        ),
        cls="border-t border-line", id="features",
    )

    comparison = Section_(
        Div(
            Eyebrow("Why FastHTML-CMS"),
            Heading(2, "Traditional CMS platforms carry decades of complexity", cls="mt-3 max-w-3xl mb-10"),
        ),
        Div(
            Article(
                P("Instead of", cls="text-[11px] font-mono tracking-widest uppercase text-ink-dim mb-3"),
                P("Django + PostgreSQL", cls="text-xl font-medium tracking-tight text-ink mb-3"),
                P("FastHTML + SQLite. Same power, 10x simpler to deploy. One file database, one process, zero config.",
                  cls="text-ink-muted text-sm leading-relaxed"),
                cls="p-7 rounded-2xl bg-bg-elevated border border-line",
            ),
            Article(
                P("Instead of", cls="text-[11px] font-mono tracking-widest uppercase text-ink-dim mb-3"),
                P("React admin panels", cls="text-xl font-medium tracking-tight text-ink mb-3"),
                P("HTMX + Server rendering. No webpack, no node_modules, no build step. Fast, accessible, and progressively enhanced.",
                  cls="text-ink-muted text-sm leading-relaxed"),
                cls="p-7 rounded-2xl bg-bg-elevated border border-line",
            ),
            Article(
                P("Instead of", cls="text-[11px] font-mono tracking-widest uppercase text-ink-dim mb-3"),
                P("Complex ORM migrations", cls="text-xl font-medium tracking-tight text-ink mb-3"),
                P("Fastlite with auto-transform. Add a field, restart, done. No migration files to manage.",
                  cls="text-ink-muted text-sm leading-relaxed"),
                cls="p-7 rounded-2xl bg-bg-elevated border border-line",
            ),
            cls="grid md:grid-cols-3 gap-4",
        ),
        cls="border-t border-line bg-bg-raised/40",
    )

    get_started = Section_(
        Div(
            Eyebrow("Quick Start"),
            Heading(2, "Up and running in 60 seconds", cls="mt-3 max-w-3xl mb-2"),
            P("No Docker, no PostgreSQL, no Redis. Just Python.",
              cls="mt-2 text-ink-muted text-base max-w-2xl leading-relaxed mb-10"),
        ),
        Div(
            Pre(
                Code(
                    "$ pip install fasthtml-cms\n"
                    "$ fasthtml-cms init mysite\n"
                    "$ cd mysite\n"
                    "$ python setup.py\n"
                    "$ python main.py\n"
                    "\n"
                    "  FastHTML-CMS running at http://localhost:5001\n"
                    "  Admin panel at http://localhost:5001/admin/",
                    cls="text-accent-cyan/90",
                ),
                cls="bg-ink rounded-2xl p-6 md:p-8 text-sm leading-relaxed overflow-x-auto font-mono",
            ),
            cls="max-w-2xl mb-10",
        ),
        Div(
            Btn("Try the Demo", href=DEMO_URL, primary=True),
            Btn("View on GitHub", href=GITHUB_URL, primary=False),
            cls="flex items-center gap-3 flex-wrap",
        ),
        cls="border-t border-line", id="get-started",
    )

    cta = Section(
        Div(
            Div(
                Eyebrow("Get Started", cls="text-accent-dim"),
                Heading(2, "Ready to simplify your CMS?", cls="mt-3 max-w-3xl text-white"),
                P("FastHTML-CMS is open source, free, and built for developers who value simplicity.",
                  cls="mt-5 text-white/70 text-lg max-w-2xl leading-relaxed"),
                Div(
                    A("Get Started", Span("→", cls="text-base ml-1"), href="#get-started",
                      cls="inline-flex items-center gap-1 px-5 py-3 rounded-full text-sm font-medium bg-white text-accent-deep hover:bg-accent-dim transition-all"),
                    A("About Predictive Labs", Span("→", cls="text-base ml-1"), href=ABOUT_URL, target="_blank",
                      cls="inline-flex items-center gap-1 px-5 py-3 rounded-full text-sm font-medium text-white/80 border border-white/30 hover:border-white hover:text-white transition-all"),
                    cls="mt-8 flex items-center gap-3 flex-wrap",
                ),
                cls="max-w-7xl mx-auto px-5 md:px-6 py-20 md:py-28 relative z-10",
            ),
            Div(cls="absolute inset-0 bg-gradient-to-br from-accent/10 via-transparent to-transparent pointer-events-none"),
            cls="relative overflow-hidden bg-accent-deep",
        ),
    )

    return _page(
        "Modern Content Management",
        hero,
        tech_strip,
        features,
        comparison,
        get_started,
        cta,
    )


serve()
