from fasthtml.common import *
from starlette.responses import RedirectResponse
from app.snippets import get_snippet_types, get_snippet_table, get_snippet_info
from admin.components import admin_page, field_panel, empty_state

def snippet_type_list(auth):
    types = get_snippet_types()
    cards = [
        A(
            Div(Span(info['icon'], cls="text-2xl"), cls="mb-2"),
            H3(name, cls="text-sm font-semibold"),
            P(f"{len(info['table']())} items", cls="text-xs text-gray-500"),
            href=f"/admin/snippets/{name}/",
            cls="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow block"
        )
        for name, info in types.items()
    ]
    return admin_page('Snippets', auth=auth, active='snippets', body=[
        Div(H1("Snippets", cls="text-2xl font-semibold"), cls="mb-6"),
        Div(*cards, cls="grid grid-cols-2 md:grid-cols-4 gap-4") if cards else
            empty_state('✂️', 'No snippets registered'),
    ])

def snippet_instance_list(type_name, auth):
    info = get_snippet_info(type_name)
    if not info: raise HTTPException(404)
    table = info['table']
    items = table()
    first_field = info['fields'][0]['name'] if info['fields'] else 'id'

    rows = [Tr(
        Td(A(getattr(item, first_field, f'#{item.id}'),
             href=f"/admin/snippets/{type_name}/{item.id}/edit/",
             cls="text-accent hover:underline"), cls="py-2 px-4 text-sm"),
        Td(str(item.id), cls="py-2 px-4 text-xs text-gray-400"),
    ) for item in items]

    return admin_page(f'{type_name}', auth=auth, active='snippets',
        breadcrumbs=[('Snippets', '/admin/snippets/'), (type_name, None)], body=[
        Div(
            H1(f"{info['icon']} {type_name}", cls="text-2xl font-semibold"),
            A(f"+ Add {type_name}", href=f"/admin/snippets/{type_name}/add/",
              cls="px-4 py-2 bg-accent text-white text-sm rounded-lg hover:bg-accent-deep"),
            cls="flex items-center justify-between mb-6"
        ),
        Div(
            Table(Thead(Tr(
                Th(first_field.replace('_', ' ').title(), cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                Th("ID", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
            )), Tbody(*rows), cls="w-full") if rows else
                empty_state(info['icon'], f'No {type_name} items', '', f'/admin/snippets/{type_name}/add/', f'Add {type_name}'),
            cls="bg-white rounded-xl border border-gray-200"
        ),
    ])

def snippet_add_form(type_name, auth):
    info = get_snippet_info(type_name)
    if not info: raise HTTPException(404)
    panels = [field_panel(f['name'], f['label'], field_type=f['type']) for f in info['fields']]
    return admin_page(f'Add {type_name}', auth=auth, active='snippets',
        breadcrumbs=[('Snippets', '/admin/snippets/'), (type_name, f'/admin/snippets/{type_name}/'), ('Add', None)], body=[
        Form(
            Div(*panels, cls="max-w-lg"),
            Button(f"Create {type_name}", type="submit",
                   cls="px-4 py-2 bg-accent text-white text-sm rounded-lg hover:bg-accent-deep mt-4"),
            method='post', action=f'/admin/snippets/{type_name}/add/',
        ),
    ])

def snippet_add_submit(type_name, auth, **kwargs):
    info = get_snippet_info(type_name)
    if not info: raise HTTPException(404)
    data = {f['name']: kwargs.get(f['name'], '') for f in info['fields']}
    for f in info['fields']:
        if f['type'] == 'number' and data[f['name']]:
            data[f['name']] = int(data[f['name']])
    info['table'].insert(**data)
    return RedirectResponse(f'/admin/snippets/{type_name}/', status_code=303)

def snippet_edit_form(type_name, item_id, auth):
    info = get_snippet_info(type_name)
    if not info: raise HTTPException(404)
    item = info['table'][item_id]
    panels = [field_panel(f['name'], f['label'], value=getattr(item, f['name'], ''), field_type=f['type'])
              for f in info['fields']]
    return admin_page(f'Edit {type_name}', auth=auth, active='snippets',
        breadcrumbs=[('Snippets', '/admin/snippets/'), (type_name, f'/admin/snippets/{type_name}/'), ('Edit', None)], body=[
        Form(
            Div(*panels, cls="max-w-lg"),
            Div(
                Button("Save", type="submit", cls="px-4 py-2 bg-accent text-white text-sm rounded-lg hover:bg-accent-deep"),
                Form(Button("Delete", type="submit", cls="text-sm text-red-600 hover:underline ml-4"),
                     method='post', action=f'/admin/snippets/{type_name}/{item_id}/delete/'),
                cls="flex items-center mt-4"
            ),
            method='post', action=f'/admin/snippets/{type_name}/{item_id}/edit/',
        ),
    ])

def snippet_edit_submit(type_name, item_id, auth, **kwargs):
    info = get_snippet_info(type_name)
    if not info: raise HTTPException(404)
    data = {f['name']: kwargs.get(f['name'], '') for f in info['fields']}
    for f in info['fields']:
        if f['type'] == 'number' and data[f['name']]:
            data[f['name']] = int(data[f['name']])
    data['id'] = item_id
    info['table'].update(**data)
    return RedirectResponse(f'/admin/snippets/{type_name}/', status_code=303)

def snippet_delete_submit(type_name, item_id, auth):
    info = get_snippet_info(type_name)
    if not info: raise HTTPException(404)
    info['table'].delete(item_id)
    return RedirectResponse(f'/admin/snippets/{type_name}/', status_code=303)
