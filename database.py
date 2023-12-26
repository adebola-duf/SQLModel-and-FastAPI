from models import Student
from sqlmodel import create_engine, SQLModel
import os
from dotenv import load_dotenv
load_dotenv()

sqlite_file_name = "students.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
postgres_url = os.getenv("POSTGRES_DB_URL")
engine = create_engine(url=sqlite_url, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
