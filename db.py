import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    create_engine,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker


load_dotenv()


class Base(DeclarativeBase):
    pass


def get_database_url() -> str:
    url = os.getenv("DATABASE_URL")

    if not url:
        base_dir = Path(__file__).resolve().parent
        db_path = base_dir / "university_bot.db"
        return f"sqlite:///{db_path}"

    # Some Railway/Postgres providers return postgres://.
    # SQLAlchemy expects postgresql://.
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    return url


DATABASE_URL = get_database_url()

CINEMA_NAME = "🎬 سینما: مینیون‌ها"
CINEMA_CAPACITY = 50
CINEMA_STUDENT_PRICE = 130000
CINEMA_GUEST_PRICE = 150000

engine_kwargs = {"pool_pre_ping": True, "pool_recycle": 1800}
if DATABASE_URL.startswith("sqlite"):
    # `timeout` makes SQLite wait (instead of immediately raising
    # "database is locked") when two requests try to write at the same
    # moment, e.g. a user cancelling while another request touches the
    # same row. Telegram bots are low-concurrency, but polling runs
    # handlers on multiple worker threads, so this can still happen.
    engine_kwargs["connect_args"] = {
        "check_same_thread": False,
        "timeout": 30,
    }

engine = create_engine(
    DATABASE_URL,
    **engine_kwargs,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    tg_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        index=True,
        nullable=False,
    )

    full_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    student_id_card: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    is_student: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    registrations: Mapped[list["Registration"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    capacity: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    student_price: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    guest_price: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    registrations: Mapped[list["Registration"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )


class Registration(Base):
    __tablename__ = "registrations"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "event_id",
            name="uq_registration_user_event",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    event_id: Mapped[int] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    registration_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    linked_student_id: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    payment_proof_file_id: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="draft",
        nullable=False,
        index=True,
    )

    ticket_code: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship(
        back_populates="registrations",
    )

    event: Mapped[Event] = relationship(
        back_populates="registrations",
    )


def init_db():
    Base.metadata.create_all(engine)
    seed_events()


def seed_events():
    with SessionLocal() as session:
        cinema = session.query(Event).filter_by(code="cinema").first()

        if cinema is not None and cinema.name != CINEMA_NAME:
            # A different movie is being screened: archive the previous
            # showing under its own code (keeping its registrations and
            # tickets intact) so the new movie starts with a clean
            # capacity count and nobody is told they are "already
            # registered" from the last one.
            cinema.code = f"cinema_archived_{cinema.id}"
            cinema.is_active = False
            session.flush()
            cinema = None

        if not cinema:
            cinema = Event(
                code="cinema",
                name=CINEMA_NAME,
                capacity=CINEMA_CAPACITY,
                student_price=CINEMA_STUDENT_PRICE,
                guest_price=CINEMA_GUEST_PRICE,
                is_active=True,
            )
            session.add(cinema)
        else:
            # Keep an already-existing row's price/capacity in sync with
            # the constants above on every startup (the "yalda.is_active"
            # sync below follows the same pattern) so changing a value
            # here takes effect on the next restart without a manual
            # DB edit.
            cinema.student_price = CINEMA_STUDENT_PRICE
            cinema.guest_price = CINEMA_GUEST_PRICE
            cinema.capacity = CINEMA_CAPACITY
            cinema.is_active = True

        yalda = session.query(Event).filter_by(code="yalda").first()

        if not yalda:
            yalda = Event(
                code="yalda",
                name="🍉 یلدای علوم کامپیوتر",
                capacity=120,
                student_price=250000,
                guest_price=280000,
                is_active=False,
            )
            session.add(yalda)
        else:
            yalda.is_active = False

        session.commit()