from fasthtml.common import *
from starlette.responses import RedirectResponse
from app.db import users, now
from app.auth import hash_password, require_admin
from admin.components import admin_page, field_panel, empty_state

ROLES = [('admin', 'Admin'), ('editor', 'Editor'), ('moderator', 'Moderator')]

def user_list(auth):
    require_admin(auth)
    all_users = users(order_by='created_at DESC')
    rows = [Tr(
        Td(A(u.name, href=f"/admin/users/{u.id}/edit/", cls="text-accent hover:underline"), cls="py-2 px-4 text-sm"),
        Td(u.email, cls="py-2 px-4 text-sm text-gray-500"),
        Td(Span(u.role, cls="px-2 py-0.5 text-xs font-medium rounded-full bg-gray-100"), cls="py-2 px-4"),
        Td(Span("Active", cls="text-green-600 text-xs") if u.is_active else Span("Inactive", cls="text-red-500 text-xs"), cls="py-2 px-4"),
        Td(u.last_login[:16].replace('T', ' ') if u.last_login else '—', cls="py-2 px-4 text-xs text-gray-400"),
    ) for u in all_users]

    return admin_page('Users', auth=auth, active='users', body=[
        Div(
            H1("Users", cls="text-2xl font-semibold"),
            A("+ Add User", href="/admin/users/add/", cls="px-4 py-2 bg-accent text-white text-sm rounded-lg hover:bg-accent-deep"),
            cls="flex items-center justify-between mb-6"
        ),
        Div(
            Table(Thead(Tr(
                Th("Name", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                Th("Email", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                Th("Role", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                Th("Status", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                Th("Last Login", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
            )), Tbody(*rows), cls="w-full"),
            cls="bg-white rounded-xl border border-gray-200"
        ),
    ])

def user_add_form(auth):
    require_admin(auth)
    return admin_page('Add User', auth=auth, active='users',
        breadcrumbs=[('Users', '/admin/users/'), ('Add User', None)], body=[
        Form(
            Div(
                field_panel('name', 'Name', required=True),
                field_panel('email', 'Email', field_type='email', required=True),
                field_panel('password', 'Password', field_type='password', required=True),
                field_panel('role', 'Role', field_type='select', options=ROLES, value='editor'),
                Div(Button("Create User", type="submit", cls="px-4 py-2 bg-accent text-white text-sm rounded-lg hover:bg-accent-deep"),
                    cls="mt-4"),
                cls="max-w-lg"
            ),
            method='post', action='/admin/users/add/',
        ),
    ])

def user_add_submit(auth, name: str = '', email: str = '', password: str = '', role: str = 'editor'):
    require_admin(auth)
    users.insert(name=name, email=email, password_hash=hash_password(password),
                 role=role, is_active=True, created_at=now())
    return RedirectResponse('/admin/users/', status_code=303)

def user_edit_form(user_id, auth):
    require_admin(auth)
    u = users[user_id]
    return admin_page(f'Edit — {u.name}', auth=auth, active='users',
        breadcrumbs=[('Users', '/admin/users/'), (u.name, None)], body=[
        Form(
            Div(
                field_panel('name', 'Name', value=u.name, required=True),
                field_panel('email', 'Email', value=u.email, field_type='email', required=True),
                field_panel('role', 'Role', field_type='select', options=ROLES, value=u.role),
                field_panel('is_active', 'Active', value=u.is_active, field_type='checkbox'),
                Div(
                    Button("Save", type="submit", cls="px-4 py-2 bg-accent text-white text-sm rounded-lg hover:bg-accent-deep"),
                    A("Change Password", href=f"/admin/users/{user_id}/password/",
                      cls="text-sm text-accent hover:underline ml-4"),
                    Form(Button("Delete", type="submit", cls="text-sm text-red-600 hover:underline ml-4"),
                         method='post', action=f'/admin/users/{user_id}/delete/') if user_id != auth.id else '',
                    cls="flex items-center mt-4"
                ),
                cls="max-w-lg"
            ),
            method='post', action=f'/admin/users/{user_id}/edit/',
        ),
    ])

def user_edit_submit(user_id, auth, name: str = '', email: str = '', role: str = 'editor', is_active: str = ''):
    require_admin(auth)
    users.update(id=user_id, name=name, email=email, role=role, is_active=bool(is_active))
    return RedirectResponse('/admin/users/', status_code=303)

def user_delete_submit(user_id, auth):
    require_admin(auth)
    if user_id == auth.id:
        return RedirectResponse('/admin/users/', status_code=303)
    users.delete(user_id)
    return RedirectResponse('/admin/users/', status_code=303)

def user_password_form(user_id, auth):
    require_admin(auth)
    u = users[user_id]
    return admin_page(f'Change Password — {u.name}', auth=auth, active='users',
        breadcrumbs=[('Users', '/admin/users/'), (u.name, f'/admin/users/{user_id}/edit/'), ('Password', None)], body=[
        Form(
            Div(
                field_panel('password', 'New Password', field_type='password', required=True),
                field_panel('password_confirm', 'Confirm Password', field_type='password', required=True),
                Button("Change Password", type="submit", cls="px-4 py-2 bg-accent text-white text-sm rounded-lg hover:bg-accent-deep mt-4"),
                cls="max-w-lg"
            ),
            method='post', action=f'/admin/users/{user_id}/password/',
        ),
    ])

def user_password_submit(user_id, auth, password: str = '', password_confirm: str = ''):
    require_admin(auth)
    if password != password_confirm:
        return user_password_form(user_id, auth)
    users.update(id=user_id, password_hash=hash_password(password))
    return RedirectResponse(f'/admin/users/{user_id}/edit/', status_code=303)
