from sqlmodel import Field, Session, SQLModel, create_engine

DATABASE_URL = "sqlite:///netmon.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


class Device(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    ip: str = Field(unique=True, index=True)


class DeviceCreate(SQLModel):
    name: str
    ip: str


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session