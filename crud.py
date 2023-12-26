from sqlmodel import Session, select, or_, col
from models import StudentCreate, Student, StudentRead, StudentUpdate


def create_students(session: Session, student: StudentCreate) -> StudentRead:
    db_student = Student.model_validate(student)
    session.add(db_student)
    session.commit()
    session.refresh(db_student)
    return db_student


def get_students(session: Session) -> list[StudentRead]:
    return session.exec(select(Student)).all()


def get_student_by_matric_number(session: Session, matric_number: str) -> StudentRead | None:
    return session.get(Student, matric_number)


def update_student(session: Session, matric_number: str, student_info_to_update: StudentUpdate):
    db_student = session.get(Student, matric_number)
    if not db_student:
        return None
    info_to_update = student_info_to_update.model_dump(exclude_unset=True)
    for key, value in info_to_update.items():
        setattr(db_student, key, value)
    session.add(db_student)
    session.commit()
    session.refresh(db_student)
    return db_student


def delete_student(session: Session, matric_number: str):
    student = session.get(Student, matric_number)
    if not student:
        return None
    session.delete(student)
    session.commit()
    return "ok"
