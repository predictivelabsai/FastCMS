from fasthtml.common import *
from starlette.responses import RedirectResponse
import bcrypt
from app.db import users, now

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed.encode())

def get_current_user(sess):
    uid = sess.get('user_id')
    if not uid: return None
    try: return users[uid]
    except: return None

def auth_before(req, sess):
    auth = req.scope['auth'] = get_current_user(sess)
    path = req.url.path
    if path.startswith('/admin') and path != '/admin/login' and not auth:
        return RedirectResponse('/admin/login', status_code=303)

def require_admin(auth):
    if not auth or auth.role != 'admin':
        raise HTTPException(403, 'Admin access required')

def require_editor(auth):
    if not auth or auth.role not in ('admin', 'editor'):
        raise HTTPException(403, 'Editor access required')

def can_publish(auth):
    return auth and auth.role in ('admin', 'editor')

def can_delete(auth):
    return auth and auth.role == 'admin'

def can_manage_users(auth):
    return auth and auth.role == 'admin'

def can_manage_settings(auth):
    return auth and auth.role == 'admin'

# ── Login page ────────────────────────────────────────────────────────

TAILWIND_CONFIG = """
tailwind.config = {
  theme: {
    extend: {
      colors: {
        accent: { DEFAULT: '#7C3AED', deep: '#2E1065', dim: '#EDE9FE' },
      },
      fontFamily: { sans: ['Inter', 'system-ui', 'sans-serif'] },
    },
  },
};
"""

def login_page(error=''):
    return Html(
        Head(
            Meta(charset='utf-8'),
            Meta(name='viewport', content='width=device-width, initial-scale=1'),
            Title('Login — FastHTML-CMS'),
            Link(rel='stylesheet', href='https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap'),
            Script(src='https://cdn.tailwindcss.com'),
            Script(NotStr(TAILWIND_CONFIG)),
        ),
        Body(
            Div(
                Div(
                    Span("◆", cls="text-accent text-2xl mr-2"),
                    Span("FastHTML-CMS", cls="text-xl font-semibold"),
                    cls="flex items-center justify-center mb-8"
                ),
                H1("Sign in to admin", cls="text-lg font-medium text-center mb-6"),
                Div(P(error, cls="text-red-600 text-sm mb-4"), cls="") if error else '',
                Form(
                    Div(
                        Label("Email", cls="block text-sm font-medium text-gray-700 mb-1"),
                        Input(name="email", type="email", required=True, autofocus=True,
                              cls="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-accent focus:border-accent outline-none"),
                        cls="mb-4"
                    ),
                    Div(
                        Label("Password", cls="block text-sm font-medium text-gray-700 mb-1"),
                        Input(name="password", type="password", required=True,
                              cls="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-accent focus:border-accent outline-none"),
                        cls="mb-6"
                    ),
                    Button("Sign in", type="submit",
                           cls="w-full py-2 px-4 bg-accent text-white rounded-lg font-medium hover:bg-accent-deep transition-colors"),
                    method="post", action="/admin/login",
                ),
                cls="max-w-sm mx-auto p-8 bg-white rounded-2xl shadow-lg border border-gray-100"
            ),
            cls="min-h-screen flex items-center justify-center bg-gray-50 font-sans"
        ),
    )

def login_submit(email, password, sess):
    matching = users(where="email=?", where_args=[email])
    if not matching:
        return login_page(error='Invalid email or password')
    user = matching[0]
    if not user.is_active:
        return login_page(error='Account is disabled')
    if not check_password(password, user.password_hash):
        return login_page(error='Invalid email or password')
    sess['user_id'] = user.id
    users.update(id=user.id, last_login=now())
    return RedirectResponse('/admin/', status_code=303)

def logout(sess):
    sess.clear()
    return RedirectResponse('/admin/login', status_code=303)
