from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from models import schemas



metadata = MetaData()
engine = create_engine(
    'postgresql://linpostgres:HxywGpAs2-2CnbGh@lin-13704-4133-pgsql-primary.servers.linodedb.net:5432/aba_test')
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

schemas.Base.metadata.create_all(bind=engine)


# Dependency injection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()