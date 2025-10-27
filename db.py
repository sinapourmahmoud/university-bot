import os
from sqlalchemy import create_engine, Column, Integer, String,BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

# Use DATABASE_URL from environment (works locally or on Railway)
DATABASE_URL = os.getenv("DATABASE_URL")


# Create engine and session
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# Define your users table
class User(Base):
    __tablename__ = "users"
    
    tg_id = Column(String(20), primary_key=True)
    student_id_card = Column(String(20), nullable=True)
    full_name = Column(String)
    is_student = Column(Integer)
    linked_student_id = Column(String(20), nullable=True)
    payment_proof_file_id = Column(String)
    status = Column(String)
    ticket_code = Column(String)

# Create the table if it doesn't exist
Base.metadata.create_all(engine)
