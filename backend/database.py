from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Creates a local SQLite database file named campuscore.db inside backend/
SQLALCHEMY_DATABASE_URL = "sqlite:///./campuscore.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()