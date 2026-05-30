import json, csv, io
from fasthtml.common import *
from app.db import form_fields, form_submissions, pages, now

def get_form_fields(page_id):
    return form_fields(where="page_id=?", where_args=[page_id], order_by='sort_order')

def render_form(page_id, action_url):
    fields = get_form_fields(page_id)
    if not fields:
        return P("No form fields configured.", cls="text-gray-500")

    inputs = []
    for f in fields:
        label_el = Label(f.label, Span(' *', cls='text-red-500') if f.required else '',
                         cls="block text-sm font-medium text-gray-700 mb-1")
        if f.field_type == 'textarea':
            inp = Textarea(f.default_value or '', name=f.label, required=f.required,
                          cls="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm", rows=4)
        elif f.field_type in ('radio', 'dropdown') and f.choices:
            choices = [c.strip() for c in f.choices.split('|')]
            if f.field_type == 'dropdown':
                opts = [Option(c, value=c, selected=c == f.default_value) for c in choices]
                inp = Select(*opts, name=f.label, required=f.required,
                            cls="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm")
            else:
                radios = [Div(
                    Input(type='radio', name=f.label, value=c, checked=c == f.default_value,
                          cls="mr-2"), Span(c, cls="text-sm"),
                    cls="flex items-center mb-1"
                ) for c in choices]
                inp = Div(*radios)
        elif f.field_type == 'checkbox':
            inp = Input(type='checkbox', name=f.label, value='Yes', cls="w-4 h-4 mr-2")
        else:
            inp = Input(type=f.field_type, name=f.label, value=f.default_value or '',
                       required=f.required,
                       cls="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm")
        help_el = P(f.help_text, cls="text-xs text-gray-400 mt-1") if f.help_text else ''
        inputs.append(Div(label_el, inp, help_el, cls="mb-4"))

    return Form(
        *inputs,
        Button("Submit", type="submit", cls="px-6 py-2 bg-accent text-white rounded-lg font-medium hover:bg-accent-deep"),
        method="post", action=action_url,
    )

def validate_submission(page_id, form_data):
    errors = []
    fields = get_form_fields(page_id)
    for f in fields:
        val = form_data.get(f.label, '').strip()
        if f.required and not val:
            errors.append(f'{f.label} is required')
        if f.field_type == 'email' and val and '@' not in val:
            errors.append(f'{f.label} must be a valid email')
        if f.field_type == 'number' and val:
            try: float(val)
            except: errors.append(f'{f.label} must be a number')
    return errors

def save_submission(page_id, form_data, ip=''):
    fields = get_form_fields(page_id)
    data = {f.label: form_data.get(f.label, '') for f in fields}
    return form_submissions.insert(
        page_id=page_id, data_json=json.dumps(data),
        submitted_at=now(), submitted_by_ip=ip
    )

def get_submissions(page_id, limit=50, offset=0):
    return form_submissions(where="page_id=?", where_args=[page_id],
                            order_by='submitted_at DESC', limit=limit, offset=offset)

def export_submissions_csv(page_id):
    subs = form_submissions(where="page_id=?", where_args=[page_id], order_by='submitted_at')
    if not subs:
        return ''
    output = io.StringIO()
    first_data = json.loads(subs[0].data_json)
    fieldnames = ['submitted_at', 'ip'] + list(first_data.keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for sub in subs:
        data = json.loads(sub.data_json)
        data['submitted_at'] = sub.submitted_at
        data['ip'] = sub.submitted_by_ip
        writer.writerow(data)
    return output.getvalue()
