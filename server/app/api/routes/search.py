from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ...api.deps import get_current_user
from ...api.serializers import task_response
from ...database import get_db
from ...models.user import User
from ...schemas.checklist import ChecklistResponse
from ...schemas.note import NoteResponse
from ...schemas.project import ProjectResponse
from ...schemas.search import SearchResponse
from ...services.search import SearchService

router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


@router.get(
    "",
    response_model=SearchResponse,
)
def global_search(
    q: str = Query(min_length=1, max_length=200),
    limit: int = Query(default=20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SearchResponse:
    service = SearchService(db)

    data = service.search(current_user.id, q, limit)

    return SearchResponse(
        query=data["query"],
        tasks=[task_response(task) for task in data["tasks"]],
        projects=[
            ProjectResponse.model_validate(project)
            for project in data["projects"]
        ],
        notes=[
            NoteResponse.model_validate(note)
            for note in data["notes"]
        ],
        checklists=[
            ChecklistResponse.model_validate(checklist)
            for checklist in data["checklists"]
        ],
    )
