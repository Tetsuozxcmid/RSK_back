from fastapi import APIRouter, HTTPException

from app.clients.teachers.teachers_client import TeachersClient
from app.schemas.teachers import TeacherList, Teacher

router = APIRouter(prefix="/admin/teachers")
teachers_client = TeachersClient()

@router.get("/", response_model=TeacherList)
async def get_all():
    """
    Get all teachers.
    """
    try:
        response = await teachers_client.get_all_teachers()
        return TeacherList(teachers=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{teacher_id}", response_model=Teacher)
async def get_teacher(teacher_id: int):
    """
    Get a specific teacher by ID.
    """
    try:
        response = await teachers_client.get_teacher_by_id(teacher_id)
        if not response:
            raise HTTPException(status_code=404, detail="Teacher not found")
        return Teacher(**response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/unapproved", response_model=TeacherList)
async def get_unapproved_teachers():
    """
    Get all unapproved teachers.
    """
    try:
        response = await teachers_client.get_unapproved_teachers()
        return TeacherList(teachers=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/approved", response_model=TeacherList)
async def get_approved_teachers():
    """
    Get all approved teachers.
    """
    try:
        response = await teachers_client.get_approved_teachers()
        return TeacherList(teachers=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{teacher_id}/approve", response_model=Teacher)
async def approve_teacher(teacher_id: int):
    """
    Approve a specific teacher.
    """
    try:
        response = await teachers_client.approve_teacher(teacher_id)
        return Teacher(**response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{teacher_id}/reject", response_model=Teacher)
async def reject_teacher(teacher_id: int):
    """
    Reject a specific teacher.
    """
    try:
        response = await teachers_client.reject_teacher(teacher_id)
        return Teacher(**response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
