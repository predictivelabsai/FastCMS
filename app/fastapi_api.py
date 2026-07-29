"""FastCMS public reads and token-gated structured-page writes."""

from fastapi import Depends
from pydantic import BaseModel, Field

from app import db as cms_db
from app.pages import create_page

from .api_core import (
    Resource,
    SQLiteBackend,
    create_sqlite_api,
    require_write_token,
)

RESOURCES = (
    Resource("pages", "page", "Pages", "Structured CMS pages and publishing metadata.", search_fields=("title", "slug", "content_type", "url_path")),
    Resource("images", "image", "Images", "Managed image assets and rendition metadata.", search_fields=("title", "alt_text", "tags")),
    Resource("documents", "document", "Documents", "Managed downloadable documents.", search_fields=("title", "file_ext", "tags")),
    Resource("submissions", "form_submission", "Form submissions", "Structured form submissions received by CMS pages.", search_fields=("submitted_at",)),
)

backend = SQLiteBackend(cms_db.DB_PATH, RESOURCES)
api = create_sqlite_api(
    product="FastCMS", version="1.0.0",
    description="Open integration access to FastCMS pages, media, documents, and form submissions.",
    base_url="https://cms.fastsme.com", backend=backend, resources=RESOURCES,
)


class PageCreate(BaseModel):
    parent_id: int = Field(description="Parent page identifier")
    title: str = Field(min_length=1, max_length=250)
    slug: str = Field(min_length=1, max_length=250, pattern=r"^[a-z0-9-]+$")
    content_type: str = "ContentPage"
    body_json: str = "[]"
    extra_json: str = "{}"


@api.post(
    "/v1/pages",
    status_code=201,
    dependencies=[Depends(require_write_token)],
    tags=["Pages"],
)
def create_structured_page(payload: PageCreate):
    """Create an unpublished page through FastCMS's page service."""

    page = create_page(
        payload.parent_id,
        payload.title,
        payload.slug,
        payload.content_type,
        payload.body_json,
        payload.extra_json,
    )
    item_id = page.id if hasattr(page, "id") else page
    return backend.get(RESOURCES[0], str(item_id))
