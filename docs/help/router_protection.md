Защита API

Теперь правило для остальных endpoint'ов очень простое.

Было:

@router.get("/projects")
def get_projects(
    db: Session = Depends(get_db),
):
    ...

Станет:

@router.get("/projects")
def get_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ...

И обязательно использовать current_user.id.

Например:

projects = service.get_user_projects(current_user.id)

а не:

projects = service.get_all_projects()
23. Критически важное правило для будущих Projects/Tasks

Защита API — это не только:

есть JWT?

Нужно ещё:

есть JWT?
   ↓
кто пользователь?
   ↓
имеет ли он доступ к объекту?

Например:

GET /projects/15
Authorization: Bearer USER_A_TOKEN

Если project 15 принадлежит USER_B:

USER_A
   │
   ▼
GET project 15
   │
   ▼
project.user_id != USER_A.id
   │
   ▼
403 / 404

Поэтому когда начнём Stage 7/8, каждый repository/service должен учитывать current_user.id.

Это напрямую соответствует дальнейшему пункту roadmap про защиту чужих проектов и задач.
