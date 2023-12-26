from fastapi import FastAPI, HTTPException, status, Depends
from sqlmodel import Session, select
from models import Student, StudentCreate, StudentRead, StudentUpdate
from database import engine, create_db_and_tables
engine.echo = False
app = FastAPI()


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.post(path="/student", response_model=StudentRead)
# This will validate that all the data that we promised is there and will remove any data we didn't declare.
def create_student(student: StudentCreate):
    print("hi this is student:", student)
    # Apparently when you make a SQLModel Model with table=True, you don't get the data validation. So you eiher have to create a pydantic model for validation by removing table=True and at the same time, you should still have your table model with table=True.
    # Here, we create a new Student(db_student) (this is the actual table model that saves things to the database) using Student.model_validate().
    # The method .model_validate() reads data from another object with attributes (or a dict) and creates a new instance of this class, in this case Student. So like it is pretty much finding the attributes that the Student model has that are in the StudentCreate model or the model in the model_validate
    # In this case, we have a StudentCreate instance in the student variable. This is an object with attributes, so we use .model_validate() to read those attributes.
    # We are pretty much  converting from a StudentCreate instance to a Student instance
    db_student = Student.model_validate(student)
    with Session(engine) as session:
        session.add(db_student)
        session.commit()
        session.refresh(db_student)
        return db_student


@app.get(path="/students", response_model=list[StudentRead])
def read_students():
    # We should normally have one session per request in most of the cases.
    # In some isolated cases, we would want to have new sessions inside, so, more than one session per request.
    # But we would never want to share the same session among different requests.

    with Session(engine) as session:
        results = session.exec(select(Student)).all()
        return results
# The interactive docs UI is powered by Swagger UI, and what Swagger UI does is to read a big JSON content that defines the API with all the data schemas (data shapes) using the standard OpenAPI, and showing it in that nice UI.
# FastAPI automatically generates that OpenAPI for Swagger UI to read it.
# And it generates it based on the code you write, using the Pydantic models (in this case SQLModel models) and type annotations to know the schemas of the data that the API handles.


@app.get("/students/{matric_number}", response_model=StudentRead)
def read_student(matric_number: str):
    with Session(engine) as session:
        student = session.get(Student, matric_number)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Student not found")
        return student


@app.patch("/students/{matric_number}", response_model=StudentRead)
def update_student(matric_number: str, student: StudentUpdate):
    with Session(engine) as session:
        db_student = session.get(Student, matric_number)
        if not db_student:
            raise HTTPException(status_code=404, detail="Student not found")
        student_data = student.model_dump(exclude_unset=True)
        print("Student data is:", student_data)
        for key, value in student_data.items():
            setattr(db_student, key, value)
        session.add(db_student)
        session.commit()
        session.refresh(db_student)
        return db_student
# The StudentUpdate model has all the fields with default values, because they all have defaults, they are all optional, which is what we want.
# But that also means that if we just call student.model_dump() we will get a dictionary that could potentially have several or all of those values with their defaults, for example:
# {
#     "first_name": None,
#     "last_name": None,
#     "email": None,
#     "password": None
# }
# And then, if we update the student in the database with this data, we would be removing any existing values, and that's probably not what the client intended.
# But fortunately Pydantic models (and so SQLModel models) have a parameter we can pass to the .model_dump() method for that: exclude_unset=True.
# This tells Pydantic to not include the values that were not sent by the client. Saying it another way, it would only include the values that were sent by the client.
# So, if the client sent a JSON with no values:
# {}
# Then the dictionary we would get in Python using student.model_dump(exclude_unset=True) would be:
# {}
# But if the client sent a JSON with:
# {
#     "name": "Deadpuddle"
# }
# Then the dictionary we would get in Python using student.model_dump(exclude_unset=True) would be:
# {
#     "name": "Deadpuddle"
# }
# if the client sends {"name": null}, then student.model_dump(exclue_unset=True) would be {"name": None}
# because the client specified a value rather than not sending anything and this can cause errors. if the column is meant to be non null


@app.delete("/students/{matric_number}")
def delete_student(matric_number: str):
    with Session(engine) as session:
        student = session.get(Student, matric_number)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        session.delete(student)
        session.commit()
        return {"ok": True}


# A better way to create sessions. use dependencies. Why? Most of the time, the traditional method is good but in many use cases we would want to use FastAPI Dependencies, for example to verify that the client is logged in and get the current user before executing any other code in the path operation.
# These dependencies are also very useful during testing, because we can easily replace them, and then, for example, use a new database for our tests, or put some data before the tests, etc.

def get_session():
    with Session(engine) as session:
        # The value of a dependency will only be used for one request, FastAPI will call it right before calling your code and will give you the value from that dependency.
        # If it had yield, then it will continue the rest of the execution once you are done sending the response. In the case of the session, it will finish the cleanup code from the with block, closing the session, etc.
        # Then FastAPI will call it again for the next request.
        # Because it is called once per request, we will still get a single session per request as we should, so we are still fine with that. ✅
        # In fact, you could think that all that block of code inside of the create_hero() function is still inside a with block for the session, because this is more or less what's happening behind the scenes.
        # But now, the with block is not explicitly in the function, but in the dependency above:
        yield session


@app.delete("/students/{matric_number}")
def delete_student(*, session: Session = Depends(get_session), matric_number: str):
    student = session.get(Student, matric_number)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    session.delete(student)
    session.commit()
    return {"ok": True}
