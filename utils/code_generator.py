from random import randint
from db import session, User   

def generate_unique_code():
    while True:
        code = f"CINE-{randint(1,10000):05d}"

        # check if exists in Postgres
        exists = session.query(User).filter_by(ticket_code=code).first()

        if not exists:
            return code