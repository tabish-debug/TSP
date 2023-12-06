from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from app.main import app
from app import models
from app.database import get_db
from app.config import settings
from app.routers.drone import complete_processing

DATABASE_URL_TEST = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOSTNAME}:{settings.POSTGRES_PORT}"

engine = create_engine(DATABASE_URL_TEST)
models.Base.metadata.drop_all(bind=engine)


def db_test():
    models.Base.metadata.create_all(bind=engine)
    db = Session(autocommit=False, autoflush=False, bind=engine)
    yield db
    db.close()


def complete_processing_test():
    pass


app.dependency_overrides[get_db] = db_test
app.dependency_overrides[complete_processing] = complete_processing_test


client = TestClient(app)
