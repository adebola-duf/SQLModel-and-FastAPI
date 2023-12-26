from better_app import app
from fastapi.testclient import TestClient
from sqlmodel import create_engine, SQLModel, Session
from sqlmodel.pool import StaticPool
from better_app import get_session


def test_create_student():
    # So when we are testing, we don't want to be interacting with the production database so we don't go and delete or update data in that database. That could be costly.
    # So, we'd have to use a test database

    engine = create_engine("sqlite:///testing.db", echo=True,
                           connect_args={"check_same_thread": False})
    # Remember that order matters. So when we execute this line, since we imported from better_app, all the codes in this better_app is executed including the one where we put like the Student class
    SQLModel.metadata.create_all(engine)

    # Remember in our app code, all the path operations have a dependency on the get_session funcion. But we don't want to use that session because it is for our production database.
    # so we are going to use a new sesssion for the test database.
    with Session(engine) as session:
        def get_session_override():
            return session

        # Then, the FastAPI app object has an attribute app.dependency_overrides.
        # This attribute is a dictionary, and we can put dependency overrides in it by passing, as the key, the original dependency function, and as the value, the new overriding dependency function.
        # So, here we are telling the FastAPI app to use get_session_override instead of get_session in all the places in the code that depend on get_session, that is, all the parameters with something like:
        # session: Session = Depends(get_session)

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


def test_use_in_memory_database():
    # Now we are going to use an in memory database that would be created once the application starts and would be deleted once it ends
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # This is pretty much the code we'd use to make the database an in memory database
