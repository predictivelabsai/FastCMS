from fasthtml.common import *
from starlette.responses import RedirectResponse
from app.db import images, documents, collections
from app.media import save_uploaded_image, save_uploaded_document, delete_image, delete_document, get_rendition_url, get_collection_tree, create_collection
from admin.components import admin_page, field_panel, pagination, empty_state, confirm_dialog

def image_list(auth, page: int = 1, collection: int = 0, q: str = ''):
    per_page = 24
    where_parts, args = [], []
    if collection:
        where_parts.append("collection_id=?"); args.append(collection)
    if q:
        where_parts.append("title LIKE ?"); args.append(f'%{q}%')
    where = ' AND '.join(where_parts) if where_parts else None
    all_imgs = images(where=where, where_args=args if args else None, order_by='created_at DESC')
    total = len(all_imgs)
    page_imgs = all_imgs[(page-1)*per_page:page*per_page]
    colls = get_collection_tree()

    grid = Div(
        *[A(
            Img(src=get_rendition_url(img.id, 'fill-150x150'), alt=img.alt_text,
                cls="w-full h-36 object-cover rounded-t-lg"),
            Div(P(img.title, cls="text-sm font-medium truncate"),
                P(f"{img.width}×{img.height}", cls="text-xs text-gray-400"),
                cls="p-2"),
            href=f"/admin/images/{img.id}/", cls="bg-white rounded-lg border border-gray-200 hover:shadow-md transition-shadow block"
        ) for img in page_imgs],
        cls="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-4"
    ) if page_imgs else empty_state('🖼️', 'No images yet', 'Upload your first image.', '/admin/images/', 'Upload Image')

    coll_links = [A("All", href="/admin/images/",
                     cls="text-sm " + ("font-semibold text-accent" if not collection else "text-gray-500 hover:text-accent"))]
    for c in colls:
        coll_links.append(A(c.name, href=f"/admin/images/?collection={c.id}",
                           cls="text-sm " + ("font-semibold text-accent" if collection == c.id else "text-gray-500 hover:text-accent")))

    return admin_page('Images', auth=auth, active='images', body=[
        Div(
            H1("Images", cls="text-2xl font-semibold"),
            cls="flex items-center justify-between mb-6"
        ),
        Div(
            Div(
                H3("Collections", cls="text-xs font-medium text-gray-500 uppercase mb-3"),
                Div(*coll_links, cls="flex flex-col gap-1"),
                cls="w-40 shrink-0"
            ),
            Div(
                Div(
                    Input(type='search', name='q', value=q, placeholder='Search images...',
                          hx_get='/admin/images/', hx_trigger='keyup changed delay:300ms',
                          hx_target='body', hx_push_url='true', hx_include='[name=collection]',
                          cls="w-64 px-3 py-1.5 text-sm border border-gray-200 rounded-lg outline-none"),
                    cls="mb-4"
                ),
                Form(
                    Div(
                        Input(type='file', name='file', accept='image/*', required=True,
                              cls="text-sm file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border file:border-gray-300 file:text-sm file:bg-white file:hover:bg-gray-50"),
                        Input(type='text', name='title', placeholder='Title', required=True,
                              cls="px-3 py-1.5 text-sm border border-gray-300 rounded-lg"),
                        Button("Upload", type="submit", cls="px-4 py-1.5 text-sm bg-accent text-white rounded-lg hover:bg-accent-deep"),
                        cls="flex items-center gap-3"
                    ),
                    method='post', action='/admin/images/add/', enctype='multipart/form-data',
                    cls="mb-4 p-3 bg-gray-50 rounded-lg border border-dashed border-gray-300"
                ),
                grid,
                pagination(total, page, per_page, '/admin/images/'),
                cls="flex-1"
            ),
            cls="flex gap-6"
        ),
    ])

def image_detail(image_id, auth):
    img = images[image_id]
    return admin_page(f'Image — {img.title}', auth=auth, active='images',
        breadcrumbs=[('Images', '/admin/images/'), (img.title, None)], body=[
        Div(
            Div(
                Img(src=f'/media/images/{img.file_path}', alt=img.alt_text,
                    cls="max-w-full max-h-96 rounded-lg border"),
                cls="mb-6"
            ),
            Form(
                field_panel('title', 'Title', value=img.title, required=True),
                field_panel('alt_text', 'Alt Text', value=img.alt_text),
                field_panel('tags', 'Tags', value=img.tags, help_text='Comma-separated'),
                Div(
                    P(f"Dimensions: {img.width} × {img.height}px", cls="text-sm text-gray-500"),
                    P(f"File size: {img.file_size // 1024}KB", cls="text-sm text-gray-500"),
                    P(f"Uploaded: {img.created_at[:16].replace('T', ' ')}", cls="text-sm text-gray-500"),
                    cls="mb-4 space-y-1"
                ),
                Div(
                    Button("Save", type="submit", cls="px-4 py-2 bg-accent text-white text-sm rounded-lg hover:bg-accent-deep"),
                    A("Delete", href="#", hx_get=f"/admin/images/{image_id}/delete/confirm/",
                      hx_target="#modal-container", hx_swap="innerHTML",
                      cls="px-4 py-2 text-sm text-red-600 hover:underline ml-3"),
                    cls="flex items-center"
                ),
                method='post', action=f'/admin/images/{image_id}/',
            ),
            cls="max-w-2xl"
        ),
    ])

async def image_upload(auth, file, title: str = '', alt_text: str = '', tags: str = '', collection_id: int = 1):
    if not title:
        title = file.filename
    await save_uploaded_image(file, title, auth.id, collection_id, alt_text, tags)
    return RedirectResponse('/admin/images/', status_code=303)

def image_update(image_id, auth, title: str = '', alt_text: str = '', tags: str = ''):
    images.update(id=image_id, title=title, alt_text=alt_text, tags=tags)
    return RedirectResponse(f'/admin/images/{image_id}/', status_code=303)

def image_delete_confirm(image_id, auth):
    img = images[image_id]
    return confirm_dialog(f'Delete "{img.title}"?', 'This will permanently delete the image and all its renditions.',
                          f'/admin/images/{image_id}/delete/')

def image_delete_submit(image_id, auth):
    delete_image(image_id, auth.id)
    return RedirectResponse('/admin/images/', status_code=303)

def image_chooser(auth, field: str = '', q: str = ''):
    where = f"title LIKE '%{q}%'" if q else None
    imgs = images(where=where, order_by='created_at DESC', limit=40)
    grid = Div(
        *[Button(
            Img(src=get_rendition_url(img.id, 'fill-100x100'), alt=img.alt_text,
                cls="w-full h-20 object-cover rounded"),
            P(img.title, cls="text-xs truncate mt-1"),
            type="button",
            onclick=f"selectImage('{field}', {img.id}, '{img.title}', '/media/images/{img.file_path}'); document.getElementById('modal-container').innerHTML='';",
            cls="text-left p-1 hover:bg-accent-dim rounded transition-colors"
        ) for img in imgs],
        cls="grid grid-cols-4 gap-2 max-h-80 overflow-y-auto"
    )
    return Div(Div(Div(
        Div(H3("Choose an image", cls="text-lg font-semibold"),
            Button("✕", type="button", onclick="this.closest('#modal-container').innerHTML=''",
                   cls="text-gray-400 hover:text-gray-600 text-xl"),
            cls="flex items-center justify-between mb-4"),
        Input(type='search', placeholder='Search images...', value=q,
              hx_get=f'/admin/images/chooser/?field={field}', hx_trigger='keyup changed delay:300ms',
              hx_target='#modal-container', hx_swap='innerHTML', name='q',
              cls="w-full px-3 py-1.5 text-sm border border-gray-200 rounded-lg mb-4 outline-none"),
        grid if imgs else P("No images found", cls="text-sm text-gray-500 py-4"),
        cls="bg-white rounded-2xl p-6 max-w-2xl w-full shadow-xl max-h-[80vh] overflow-y-auto"
    ), cls="fixed inset-0 bg-black/50 flex items-center justify-center z-50",
       onclick="if(event.target===this)this.remove()"))

def document_list(auth, page: int = 1, q: str = ''):
    per_page = 20
    where = f"title LIKE '%{q}%'" if q else None
    all_docs = documents(where=where, order_by='created_at DESC')
    total = len(all_docs)
    page_docs = all_docs[(page-1)*per_page:page*per_page]

    rows = [Tr(
        Td(A(doc.title, href=f"/admin/documents/{doc.id}/", cls="text-accent hover:underline"), cls="py-2 px-4 text-sm"),
        Td(doc.file_ext, cls="py-2 px-4 text-xs text-gray-500"),
        Td(f"{doc.file_size // 1024}KB", cls="py-2 px-4 text-xs text-gray-500"),
        Td(doc.created_at[:16].replace('T', ' ') if doc.created_at else '', cls="py-2 px-4 text-xs text-gray-400"),
    ) for doc in page_docs]

    return admin_page('Documents', auth=auth, active='documents', body=[
        Div(H1("Documents", cls="text-2xl font-semibold"), cls="mb-6"),
        Form(
            Div(
                Input(type='file', name='file', required=True, cls="text-sm file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border file:border-gray-300 file:text-sm"),
                Input(type='text', name='title', placeholder='Title', required=True, cls="px-3 py-1.5 text-sm border border-gray-300 rounded-lg"),
                Button("Upload", type="submit", cls="px-4 py-1.5 text-sm bg-accent text-white rounded-lg hover:bg-accent-deep"),
                cls="flex items-center gap-3"
            ),
            method='post', action='/admin/documents/add/', enctype='multipart/form-data',
            cls="mb-4 p-3 bg-gray-50 rounded-lg border border-dashed border-gray-300"
        ),
        Div(
            Table(Thead(Tr(
                Th("Title", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                Th("Type", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                Th("Size", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
                Th("Uploaded", cls="py-2 px-4 text-left text-xs font-medium text-gray-500 uppercase"),
            )), Tbody(*rows), cls="w-full") if rows else empty_state('📎', 'No documents', 'Upload your first document.'),
            cls="bg-white rounded-xl border border-gray-200"
        ),
        pagination(total, page, per_page, '/admin/documents/'),
    ])

def document_detail(doc_id, auth):
    doc = documents[doc_id]
    return admin_page(f'Document — {doc.title}', auth=auth, active='documents',
        breadcrumbs=[('Documents', '/admin/documents/'), (doc.title, None)], body=[
        Form(
            field_panel('title', 'Title', value=doc.title, required=True),
            field_panel('tags', 'Tags', value=doc.tags, help_text='Comma-separated'),
            Div(P(f"File: {doc.file_path}", cls="text-sm text-gray-500"),
                P(f"Size: {doc.file_size // 1024}KB", cls="text-sm text-gray-500"),
                A("Download", href=f"/media/documents/{doc.file_path}", target="_blank", cls="text-sm text-accent"), cls="mb-4 space-y-1"),
            Div(Button("Save", type="submit", cls="px-4 py-2 bg-accent text-white text-sm rounded-lg"),
                Form(Button("Delete", type="submit", cls="text-sm text-red-600 hover:underline ml-3"),
                     method='post', action=f'/admin/documents/{doc_id}/delete/'),
                cls="flex items-center"),
            method='post', action=f'/admin/documents/{doc_id}/',
        ),
    ])

async def document_upload(auth, file, title: str = '', tags: str = ''):
    if not title: title = file.filename
    await save_uploaded_document(file, title, auth.id, tags=tags)
    return RedirectResponse('/admin/documents/', status_code=303)

def document_update(doc_id, auth, title: str = '', tags: str = ''):
    documents.update(id=doc_id, title=title, tags=tags)
    return RedirectResponse(f'/admin/documents/{doc_id}/', status_code=303)

def document_delete_submit(doc_id, auth):
    delete_document(doc_id, auth.id)
    return RedirectResponse('/admin/documents/', status_code=303)

def document_chooser(auth, field: str = '', q: str = ''):
    where = f"title LIKE '%{q}%'" if q else None
    docs = documents(where=where, order_by='created_at DESC', limit=40)
    rows = [Button(
        Span(f"📎 {doc.title} ({doc.file_ext})", cls="text-sm"),
        type="button",
        onclick=f"selectDocument('{field}', {doc.id}, '{doc.title}'); document.getElementById('modal-container').innerHTML='';",
        cls="block w-full text-left px-3 py-2 hover:bg-accent-dim rounded transition-colors"
    ) for doc in docs]
    return Div(Div(Div(
        Div(H3("Choose a document", cls="text-lg font-semibold"),
            Button("✕", type="button", onclick="this.closest('#modal-container').innerHTML=''",
                   cls="text-gray-400 hover:text-gray-600 text-xl"),
            cls="flex items-center justify-between mb-4"),
        Div(*rows, cls="max-h-80 overflow-y-auto") if rows else P("No documents", cls="text-sm text-gray-500 py-4"),
        cls="bg-white rounded-2xl p-6 max-w-lg w-full shadow-xl"
    ), cls="fixed inset-0 bg-black/50 flex items-center justify-center z-50",
       onclick="if(event.target===this)this.remove()"))
