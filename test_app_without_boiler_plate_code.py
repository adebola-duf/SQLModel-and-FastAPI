# So in the test_app, for every test, we would have to write code to handle the custom database, creating it in memory, the custom session, and the dependency override
# We are using pytest to run the tests. And pytest also has a very similar concept to the dependencies in FastAPI.
# Info
# In fact, pytest was one of the things that inspired the design of the dependencies in FastAPI.
# It's a way for us to declare some code that should be run before each test and provide a value for the test function (that's pretty much the same as FastAPI dependencies).
# In fact, it also has the same trick of allowing to use yield instead of return to provide the value, and then pytest makes sure that the code after yield is executed after the function with the test is done.
# In pytest, these things are called fixtures instead of dependencies.
# Let's use these fixtures to improve our code and reduce de duplicated boilerplate for the next tests.

import pytest
from fastapi.testclient import TestClient
from sqlmodel import create_engine, SQLModel, Session
from sqlmodel.pool import StaticPool
from app_with_crud_file import get_session, app
from models import Student

# Use the @pytest.fixture() decorator on top of the function to tell pytest that this is a fixture function (equivalent to a FastAPI dependency).
# We also give it a name of "session", this will be important in the testing function.

# I just remembered that in the response to my api, i don't include passowrds. So i am not going to be comparing password
fields_to_compare = [x for x in Student.model_fields if x != "password"]


@pytest.fixture(name="session")
def session_fixture():  # This is equivalent to a FastAPI dependency function.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
        # The thing that we return or yield is what will be available to the test function, in this case, the session object.
        # Here we use yield so that pytest comes back to execute "the rest of the code" in this function once the testing function is done.
        # We don't have any more visible "rest of the code" after the yield, but we have the end of the with block that will close the session.


def test_create_hero(session: Session):
    # Now, in the test function, to tell pytest that this test wants to get the fixture, instead of declaring something like in FastAPI with:
    # session: Session = Depends(session_fixture)
    # ...the way we tell pytest what is the fixture that we want is by using the exact same name of the fixture.
    # In this case, we named it session, so the parameter has to be exactly named session for it to work.
    # We also add the type annotation session: Session so that we can get autocompletion and inline error checks in our editor.
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    client = TestClient(app)
    response = client.post(
        "/student",
        json={"password": "someone", "matric_number": "21cg029882",
              "first_name": "Adebola", "last_name": "Odufuwa", "email": "adeboladuf@gmail.com"}
    )
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {"matric_number": "21cg029882",
                               "first_name": "Adebola", "last_name": "Odufuwa", "email": "adeboladuf@gmail.com"}

# pytest will make sure to run these fixture functions right before (and finish them right after) each test function that uses them or depens on them. So, each test function will actually have its own database, engine, and session.


# So one more thing is that if we were to continue with this code format for all the tests we are going to run, we would end up with a lot of boiler plate code.
# So, we woudl have to create the get_session_override, the app.dependency_overrides, the client and then clear the client later on.
# To prevent this, we would have another fixture and this fixture like fastapi dependency would have a sub fixture or would depend on another fixture


@pytest.fixture(name="client")
# now this fixture is depending on the session fixture
def client_fixture(session: Session):
    def get_session_override():
        return session
    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)

    yield client
    # This code would be executed since we used the yield
    # This is the cleanup code, after yield, and after the test function is done.
    app.dependency_overrides.clear()


def test_create_hero(client: TestClient):
    response = client.post(
        "/student",
        json={"password": "someone", "matric_number": "21cg029882",
              "first_name": "Adebola", "last_name": "Odufuwa", "email": "adeboladuf@gmail.com"}
    )
    assert response.status_code == 200
    assert response.json() == {"matric_number": "21cg029882",
                               "first_name": "Adebola", "last_name": "Odufuwa", "email": "adeboladuf@gmail.com"}


def test_create_hero_incomplete(client: TestClient):
    response = client.post(
        "/student",
        # This json is incomplete
        json={"matric_number": "21cg029882", "first_name": "Adebola"}
    )

    assert response.status_code == 422


def test_create_hero_invalid(client: TestClient):
    response = client.post(
        "/student",
        # matric number is a list and we were meant to pass str
        json={"matric_number": ["21cg029882"], "first_name": "Adebola",
              "last_name": "Odufuwa", "password": "password"}
    )

    assert response.status_code == 422
# It's always good idea to not only test the normal case, but also that invalid data, errors, and corner cases are handled correctly.
# That's why we add these two extra tests here.

# sometimes, in our test functions, we might require more than one fixtures. So, we might not only require fixtures in othere fixtures but also in test functions


def test_get_students(client: TestClient, session: Session):
    # Since the database might be empty, we might get an empty list and we wouldn't know if the students data is being sent correctly. So we are going to first add data. That is why we need the session fixture
    student_1 = Student(matric_number="21cg029882", first_name="Adebola",
                        last_name="Odufuwa", email="adeboladuf@gmail.com", password="password")
    student_2 = Student(matric_number="21cg029883", first_name="Oluwaferanmi",
                        last_name="Odufuwa", email="adeboladuf@gmail.com", password="password")
    session.add(student_1)
    session.add(student_2)
    session.commit()

    response = client.get(url="/students")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2
    # I don't know if this logic is even correct. but i think it is. Like i think i am mistakening it for that equality and identitiy stuff. But this one has to do with equality not identity
    received_student1 = Student(**data[0])
    received_student2 = Student(**data[1])

    are_equal1 = all([getattr(received_student1, attr) ==
                     getattr(student_1, attr) for attr in fields_to_compare])
    are_equal2 = all([getattr(received_student2, attr) ==
                     getattr(student_2, attr) for attr in fields_to_compare])

    assert are_equal1
    assert are_equal2


def test_get_student(session: Session, client: TestClient):
    student = Student(matric_number="21cg029882", first_name="Adebola",
                      last_name="Odufuwa", password="password")
    session.add(student)
    session.commit()

    response = client.get(f"/students/{student.matric_number}")
    data = response.json()

    assert response.status_code == 200
    received_student = Student(**data)

    are_equal = all([getattr(received_student, attr) ==
                     getattr(student, attr) for attr in fields_to_compare])
    assert are_equal


def test_patch_student(session: Session, client: TestClient):
    student = Student(matric_number="21cg029882", first_name="Adebola",
                      last_name="Odufuwa", password="password")
    session.add(student)
    session.commit()

    response = client.patch(
        f"/students/{student.matric_number}", json={"email": "adeboladuf@gmail.com"})
    data = response.json()

    student.email = "adeboladuf@gmail.com"

    assert response.status_code == 200
    received_student = Student(**data)

    are_equal = all([getattr(received_student, attr) ==
                     getattr(student, attr) for attr in fields_to_compare])
    assert are_equal


def test_delete_student(session: Session, client: TestClient):
    student = Student(matric_number="21cg029882", first_name="Adebola",
                      last_name="Odufuwa", password="password", email="adebolauf@gmail.com")
    session.add(student)
    session.commit()

    response = client.delete(url=f"/students/{student.matric_number}")
    assert response.status_code == 200
    student_in_db = session.get(Student, student.matric_number)
    assert student_in_db is None
