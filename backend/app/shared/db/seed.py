import os
import uuid
import random
from datetime import datetime, timedelta
from faker import Faker
import psycopg2
from psycopg2.extras import execute_values
import bcrypt

from app.shared.core.config import POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, POSTGRES_PORT

fake = Faker("vi_VN")
Faker.seed(42)
random.seed(42)


def generate_password_hash():
    """Generate a bcrypt hash for a dummy password."""
    return bcrypt.hashpw(b"password123", bcrypt.gensalt()).decode("utf-8")


def generate_users(amount):
    users_list = []
    for i in range(amount):
        users_list.append((
            str(uuid.uuid4()),  # UUID for id
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


def generate_showtimes(films, shows_per_film=3):
    """Generate showtimes for existing films."""
    rooms = ["Room 1", "Room 2", "Room 3", "Room 4", "Room 5"]
    showtimes_list = []

    for film in films:
        used_times = set()
        for _ in range(shows_per_film):
            days_from_now = random.randint(1, 14)
            hour = random.choice([9, 11, 13, 15, 17, 19, 21])

            # Ensure unique time slot per film per day
            key = (days_from_now, hour)
            while key in used_times:
                hour = random.choice([9, 11, 13, 15, 17, 19, 21])
                key = (days_from_now, hour)
            used_times.add(key)

            start = datetime.now() + timedelta(days=days_from_now)
            start = start.replace(hour=hour, minute=0, second=0, microsecond=0)

            showtimes_list.append((
                film[0],  # film_id
                random.choice(rooms),
                start,
                round(random.uniform(8.00, 15.00), 2),
            ))

    return showtimes_list


conn = psycopg2.connect(
    dbname=POSTGRES_DB,
    user=POSTGRES_USER,
    password=POSTGRES_PASSWORD,
    host=POSTGRES_HOST,
    port=POSTGRES_PORT,
)

with conn:
    with conn.cursor() as cur:
        # Check if users already exist
        cur.execute("SELECT COUNT(*) FROM users")
        existing_users = cur.fetchone()[0]

        if existing_users > 0:
            print(f"Users table already has {existing_users} rows. Skipping user generation.")
        else:
            execute_values(
                cur,
                """
                INSERT INTO users (id, first_name, last_name, email, password_hash, address, phone_number, birth_date, created_at, updated_at)
                VALUES %s
                """,
                users_list,
            )
            print(f"Inserted {len(users_list)} users")

        # Fetch existing films
        cur.execute("SELECT id, title FROM films")
        films = cur.fetchall()

        if films:
            # Check if showtimes already exist
            cur.execute("SELECT COUNT(*) FROM showtimes")
            existing_count = cur.fetchone()[0]

            if existing_count > 0:
                print(f"Showtimes table already has {existing_count} rows. Skipping showtime generation.")
            else:
                showtimes_list = generate_showtimes(films, shows_per_film=3)
                execute_values(
                    cur,
                    """
                    INSERT INTO showtimes (film_id, cinema_room, start_time, base_price)
                    VALUES %s
                    """,
                    showtimes_list,
                )
                print(f"Inserted {len(showtimes_list)} showtimes for {len(films)} films")

        # Generate seats for each showtime (independent of whether showtimes were just created)
        cur.execute("SELECT COUNT(*) FROM seats")
        existing_seats = cur.fetchone()[0]

        if existing_seats > 0:
            print(f"Seats table already has {existing_seats} rows. Skipping seat generation.")
        else:
            cur.execute("SELECT id, cinema_room FROM showtimes")
            showtimes = cur.fetchall()

            seats_list = []
            rows = ["A", "B", "C", "D", "E", "F", "G", "H"]
            seats_per_row = 10

            for showtime_id, room in showtimes:
                for row in rows:
                    for seat_num in range(1, seats_per_row + 1):
                        seat_label = f"{row}{seat_num}"
                        # Randomly mark some seats as booked (simulate sold tickets)
                        if random.random() < 0.15:  # 15% booked
                            status = "BOOKED"
                        else:
                            status = "AVAILABLE"
                        seats_list.append((showtime_id, seat_label, status))

            execute_values(
                cur,
                """
                INSERT INTO seats (showtime_id, seat_label, status)
                VALUES %s
                """,
                seats_list,
            )
            print(f"Inserted {len(seats_list)} seats for {len(showtimes)} showtimes")

conn.close()
