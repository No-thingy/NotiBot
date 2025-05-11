import logging
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()
engine = create_engine('sqlite:///notibot.db', echo=True)
Session = sessionmaker(bind=engine)


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    notes = relationship("Note", back_populates="user")
    goals = relationship("Goal", back_populates="user")
    images = relationship("Image", back_populates="user")
    messages = relationship("Message", back_populates="user")


class Note(Base):
    __tablename__ = 'notes'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notes")


class Goal(Base):
    __tablename__ = 'goals'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String)
    description = Column(Text)
    status = Column(String, default='active')
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="goals")


class Image(Base):
    __tablename__ = 'images'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    file_id = Column(String)
    description = Column(Text)
    note_id = Column(Integer, ForeignKey('notes.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="images")
    note = relationship("Note", backref="images")

class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="messages")


def init_db():
    try:
        logger.info("Инициализация базы данных...")
        Base.metadata.create_all(engine)
        logger.info("База данных успешно инициализирована")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        raise


def create_user(telegram_id, username, first_name, last_name):
    try:
        session = Session()
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        session.add(user)
        session.commit()
        logger.info(f"Создан новый пользователь: {username}")
        return user
    except Exception as e:
        logger.error(f"Ошибка при создании пользователя: {e}")
        session.rollback()
        raise


def get_user(telegram_id):
    try:
        session = Session()
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        return user
    except Exception as e:
        logger.error(f"Ошибка при получении пользователя: {e}")
        raise
