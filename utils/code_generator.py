import secrets

from db import Registration, SessionLocal


def generate_unique_code(event_code: str) -> str:
    prefix = event_code.upper()

    while True:
        code = f"{prefix}-{secrets.randbelow(90000) + 10000}"

        with SessionLocal() as session:
            exists = (
                session.query(Registration)
                .filter(Registration.ticket_code == code)
                .first()
            )

            if not exists:
                return code