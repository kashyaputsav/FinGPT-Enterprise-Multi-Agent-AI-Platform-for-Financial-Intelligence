import uuid

import boto3
from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.exceptions import NotFoundError, ValidationFailedError
from app.db.session import get_db
from app.models.document import Document, DocumentChunk
from app.models.schemas import DocumentOut
from app.models.user import User
from app.rag.ingestion import ingest_document

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_TYPES = {"report", "contract", "kyc", "statement"}
_s3 = boto3.client("s3", region_name=settings.AWS_REGION)


@router.post("/upload", response_model=DocumentOut, status_code=201)
async def upload_document(
    file: UploadFile,
    doc_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if doc_type not in ALLOWED_TYPES:
        raise ValidationFailedError(f"doc_type must be one of {ALLOWED_TYPES}")

    raw_bytes = await file.read()
    document_id = uuid.uuid4()
    s3_key = f"documents/{current_user.id}/{document_id}/{file.filename}"

    # Upload the original file to S3 for archival / re-processing.
    _s3.put_object(Bucket=settings.S3_BUCKET_DOCUMENTS, Key=s3_key, Body=raw_bytes)

    document = Document(
        id=document_id,
        owner_id=current_user.id,
        filename=file.filename,
        doc_type=doc_type,
        s3_key=s3_key,
        status="processing",
    )
    db.add(document)
    await db.commit()

    # NOTE: for large files this should be pushed to a background worker (e.g. an
    # SQS-triggered Lambda or ECS task) rather than processed inline in the request.
    text = raw_bytes.decode("utf-8", errors="ignore")
    chunk_records = await ingest_document(document_id, file.filename, text)

    for record in chunk_records:
        db.add(DocumentChunk(document_id=document_id, **record))

    document.status = "indexed" if chunk_records else "failed"
    await db.commit()
    await db.refresh(document)
    return document


@router.get("", response_model=list[DocumentOut])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.scalars(select(Document).where(Document.owner_id == current_user.id))
    return result.all()


@router.get("/{document_id}", response_model=DocumentOut)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    document = await db.get(Document, document_id)
    if not document or document.owner_id != current_user.id:
        raise NotFoundError("Document not found")
    return document
