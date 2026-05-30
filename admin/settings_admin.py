from fasthtml.common import *
from starlette.responses import RedirectResponse
from app.settings import get_all_settings, set_setting, DEFAULT_SETTINGS
from app.auth import require_admin
from admin.components import admin_page, field_panel, rich_text_panel

def settings_edit(auth):
    require_admin(auth)
    settings = get_all_settings()

    groups = [
        ("General", [
            ('site_name', 'Site Name', 'text'),
            ('site_tagline', 'Site Tagline', 'text'),
            ('default_meta_description', 'Default Meta Description', 'textarea'),
        ]),
        ("Contact", [
            ('contact_email', 'Contact Email', 'email'),
            ('contact_phone', 'Contact Phone', 'text'),
            ('contact_address', 'Contact Address', 'textarea'),
        ]),
        ("Social Media", [
            ('social_twitter', 'Twitter URL', 'url'),
            ('social_facebook', 'Facebook URL', 'url'),
            ('social_linkedin', 'LinkedIn URL', 'url'),
            ('social_github', 'GitHub URL', 'url'),
        ]),
        ("Advanced", [
            ('analytics_tracking_code', 'Analytics Tracking Code', 'textarea'),
            ('custom_css', 'Custom CSS', 'textarea'),
            ('custom_js', 'Custom JavaScript', 'textarea'),
        ]),
    ]

    sections = []
    for group_name, fields in groups:
        panels = [field_panel(key, label, value=settings.get(key, ''), field_type=ft) for key, label, ft in fields]
        sections.append(Div(
            H2(group_name, cls="text-lg font-semibold mb-4"),
            *panels,
            cls="bg-white rounded-xl border border-gray-200 p-6 mb-6"
        ))

    return admin_page('Settings', auth=auth, active='settings', body=[
        Div(H1("Site Settings", cls="text-2xl font-semibold"), cls="mb-6"),
        Form(
            *sections,
            Div(
                Button("Save Settings", type="submit",
                       cls="px-6 py-2 bg-accent text-white text-sm rounded-lg hover:bg-accent-deep"),
                cls="mb-8"
            ),
            method='post', action='/admin/settings/',
        ),
    ])

def settings_save(auth, **kwargs):
    require_admin(auth)
    for key in DEFAULT_SETTINGS:
        if key in kwargs:
            set_setting(key, kwargs[key])
    return RedirectResponse('/admin/settings/', status_code=303)
