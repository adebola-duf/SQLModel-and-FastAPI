from sqlmodel import SQLModel, Field

# this model reps our table in the database


# class Student(SQLModel, table=True):
#     matric_number: str = Field(primary_key=True)
#     first_name: str
#     last_name: str
#     email: str | None = None
#     password: str


# this model is a pydantic model and it reps the class we would be using for the creation of students like to validate the incoming data
# without the table=True, it is pretty much like a pydantic model
# class StudentCreate(SQLModel):
#     matric_number: str
#     first_name: str
#     last_name: str
#     email: str | None = None
#     password: str

# we are specifying a model for the response of like students because we don't want to include password in the response


# class StudentRead(SQLModel):
#     matric_number: str
#     first_name: str
#     last_name: str
#     email: str | None = None


# So to avoid all these duplications, we can just use something known as inheritance
class StudentBase(SQLModel):
    matric_number: str
    first_name: str
    last_name: str
    email: str | None = None


class Student(StudentBase, table=True):
    matric_number: str = Field(primary_key=True)
    password: str


class StudentCreate(StudentBase):
    password: str


class StudentRead(StudentBase):
    # Since we want it to have the same fields as the base one
    pass


class StudentUpdate(SQLModel):
    # This is almost the same as StudentBase, but all the fields are optional, so we can't simply inherit from StudentBase.
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    password: str | None = None
