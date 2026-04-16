from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.schemas.schemas import SMSTemplateResponse, SMSTemplateCreate, SMSTemplateUpdate
from app.services.sms_service import SMSService

router = APIRouter(prefix="/sms/templates", tags=["SMS Templates"])


def template_to_response(template) -> SMSTemplateResponse:
    """Map SmsTemplate model to SMSTemplateResponse schema."""
    return SMSTemplateResponse(
        id=template.id,
        name=template.template_name,
        content=template.template_content,
        variables=",".join(template.variables) if template.variables else None,
        is_active=template.status == "active",
        created_by=None,
        created_at=template.created_at
    )


@router.get("/", response_model=List[SMSTemplateResponse])
def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List SMS templates with optional active filter."""
    sms_service = SMSService(db)
    templates = sms_service.get_templates(skip=skip, limit=limit, is_active=is_active)
    return [template_to_response(t) for t in templates]


@router.get("/{template_id}", response_model=SMSTemplateResponse)
def get_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get SMS template by ID."""
    sms_service = SMSService(db)
    template = sms_service.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template_to_response(template)


@router.post("/", response_model=SMSTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    template: SMSTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new SMS template."""
    sms_service = SMSService(db)
    result, error = sms_service.create_template(
        name=template.name,
        content=template.content,
        variables=template.variables,
        created_by=current_user.id
    )
    if error:
        raise HTTPException(status_code=400, detail=error)
    return template_to_response(result)


@router.put("/{template_id}", response_model=SMSTemplateResponse)
def update_template(
    template_id: int,
    template: SMSTemplateUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an SMS template."""
    sms_service = SMSService(db)
    update_data = template.model_dump(exclude_unset=True)
    result, error = sms_service.update_template(template_id, **update_data)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return template_to_response(result)


@router.delete("/{template_id}")
def delete_template(
    template_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an SMS template."""
    sms_service = SMSService(db)
    success, error = sms_service.delete_template(template_id)
    if not success:
        raise HTTPException(status_code=400, detail=error)
    return {"message": "Template deleted successfully"}
