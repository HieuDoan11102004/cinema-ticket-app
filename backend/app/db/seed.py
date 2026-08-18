import os
from faker import Faker
import psycopg2
from psycopg2.extras import execute_values
import bcrypt

from app.core.config import POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT

fake = Faker("vi_VN")
Faker.seed(42)


def generate_password_hash():
    """Generate a bcrypt hash for a dummy password."""
    return bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")


def generate_users(amount):
    users_list = []
    for i in range(amount):
        users_list.append((
            fake.first_name(),
            fake.last_name(),
            fake.unique.email(),
            generate_password_hash(),
            fake.address(),
            fake.phone_number(),
            fake.date_of_birth(minimum_age=12, maximum_age=50),  # birthday
            fake.date_time_between_dates(datetime_start="-30y", datetime_end="now"),  # created_at
            fake.date_time_between_dates(datetime_start="-30y", datetime_end="now"),  # updated_at
        ))
    return users_list


users_list = generate_users(20)

conn = psycopg2.connect(
    dbname=POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
)

with conn:
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO users (first_name, last_name, email, password_hash, address, phone_number, birth_date, created_at, updated_at)
            VALUES %s
            """,
            users_list,
        )

conn.close()
print(f"Inserted {len(users_list)} rows")
