from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def run_migrations():
    """Lightweight auto-migration: add any new columns to an existing sqlite
    file that was created before they existed, so upgrading the app never
    breaks an already-running database."""
    inspector = inspect(engine)
    if "candidates" not in inspector.get_table_names():
        return  # fresh DB - Base.metadata.create_all already made the full table
    existing_cols = {c["name"] for c in inspector.get_columns("candidates")}
    new_columns = {
        "telugu": "TEXT DEFAULT 'No'",
    }
    with engine.begin() as conn:
        for col_name, col_def in new_columns.items():
            if col_name not in existing_cols:
                conn.execute(text(f"ALTER TABLE candidates ADD COLUMN {col_name} {col_def}"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
