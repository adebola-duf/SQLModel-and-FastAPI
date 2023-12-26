from fastapi import FastAPI, HTTPException, status, Depends
from sqlmodel import Session
from models import StudentCreate, StudentRead, StudentUpdate
from database import engine, create_db_and_tables
import crud
engine.echo = False


app = FastAPI()


# @app.on_event("startup")
# def on_startup():
#     create_db_and_tables()


def get_session():
    with Session(engine) as session:
        yield session


@app.post(path="/student", response_model=StudentRead)
def create_student(student: StudentCreate, session: Session = Depends(get_session)):
    return crud.create_students(session, student)


@app.get(path="/students", response_model=list[StudentRead])
def read_students(session: Session = Depends(get_session)):
    return crud.get_students(session)


@app.get("/students/{matric_number}", response_model=StudentRead)
def read_student(matric_number: str, session: Session = Depends(get_session)):
    student = crud.get_student_by_matric_number(session, matric_number)
    if not student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Student not found")
    return student


@app.patch("/students/{matric_number}", response_model=StudentRead)
def update_student(matric_number: str, student: StudentUpdate, session: Session = Depends(get_session)):
    db_student = crud.update_student(session, matric_number, student)
    if not db_student:
        raise HTTPException(status_code=404, detail="Student not found")
    return db_student


@app.delete("/students/{matric_number}")
def delete_student(*, session: Session = Depends(get_session), matric_number: str):
    student = crud.delete_student(session, matric_number)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"ok": True}
