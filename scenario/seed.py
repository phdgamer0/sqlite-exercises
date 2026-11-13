import os
import random
import re
import sqlite3
from datetime import datetime, timedelta
from itertools import islice

from faker import Faker

random.seed(42)
fake = Faker("en_US")
Faker.seed(42)

DB = "scenario.db"
SCHEMA = "scenario.sql"

N_COUNTRIES = 100
N_STATES = 1200
N_CITIES = 15000
N_UNIVERSITIES = 6000
N_TEACHERS = 40000
N_STUDENTS = 600000
N_CLUBS = 15000
N_EVENTS = 60000

UNI_TYPES = ["University", "Institute", "College", "Academy"]
CLUB_TYPES = ["Club", "Society", "Circle", "Crew"]
DOMAINS = ["example.com", "mail.com", "uni.edu", "student.org"]
BASE_NAMES = [
    "Computer Science", "Mathematics", "Physics", "Chemistry", "Biology", "Economics", "History",
    "Philosophy", "Literature", "Linguistics", "Law", "Medicine", "Architecture", "Psychology",
    "Sociology", "Statistics", "Engineering", "Astronomy", "Geology", "Music", "Art", "Theology"]

FIRST = [fake.first_name() for _ in range(1500)]
LAST = [fake.last_name() for _ in range(1500)]
WORDS = [fake.word().capitalize() for _ in range(3000)]

DT_FMT = "%Y-%m-%d %H:%M:%S"


def rand_dt(start: datetime, end: datetime) -> str:
    return (start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))).strftime(DT_FMT)


def date_pool(n, start: datetime, end: datetime):
    return [rand_dt(start, end) for _ in range(n)]


def clean(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def main():
    if os.path.exists(DB):
        os.remove(DB)

    con = sqlite3.connect(DB)
    con.isolation_level = None
    with open(SCHEMA) as f:
        con.executescript(f.read())
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = OFF")
    con.execute("PRAGMA synchronous = OFF")
    con.execute("BEGIN")

    cur = con.cursor()

    def bulk(sql, rows, step=20000):
        for i in range(0, len(rows), step):
            cur.executemany(sql, rows[i:i + step])

    def stream(sql, gen, step=50000):
        while True:
            rows = list(islice(gen, step))
            if not rows:
                break
            cur.executemany(sql, rows)

    bulk("INSERT INTO country(name) VALUES (?)",
         [(fake.unique.country(),) for _ in range(N_COUNTRIES)])

    bulk("INSERT INTO state(name, country_id) VALUES (?, ?)",
         [(fake.city(), random.randint(1, N_COUNTRIES)) for _ in range(N_STATES)])

    bulk("INSERT INTO city(name, population, area, state_id) VALUES (?, ?, ?, ?)",
         [(fake.city(), random.randint(1000, 20000000), round(random.uniform(10, 5000), 1), random.randint(1, N_STATES))
          for _ in range(N_CITIES)])

    founding_pool = date_pool(1000, datetime(1200, 1, 1), datetime(2015, 1, 1))
    bulk("INSERT INTO university(name, founding_date, city_id) VALUES (?, ?, ?)",
         [(f"{random.choice(LAST)} {random.choice(UNI_TYPES)}", random.choice(founding_pool), random.randint(1, N_CITIES))
          for _ in range(N_UNIVERSITIES)])

    worked_pool = date_pool(2000, datetime(1980, 1, 1), datetime(2024, 1, 1))
    teachers = []
    for tid in range(1, N_TEACHERS + 1):
        fn, ln = random.choice(FIRST), random.choice(LAST)
        teachers.append((fn, ln, f"{clean(fn)}.{clean(ln)}.{tid}@{random.choice(DOMAINS)}",
                         round(random.uniform(2500, 12000), 2), random.choice(worked_pool)))
    bulk("INSERT INTO teacher(name, lastname, email, paycheck, worked_since) VALUES (?, ?, ?, ?, ?)", teachers)

    dept_slots = []
    for uid in range(1, N_UNIVERSITIES + 1):
        for _ in range(3):
            dept_slots.append(uid)
    n_departments = len(dept_slots)
    teachers_by_dept = {d: [] for d in range(1, n_departments + 1)}
    for tid in range(1, N_TEACHERS + 1):
        teachers_by_dept[random.randint(1, n_departments)].append(tid)

    departments = []
    for did, uni in enumerate(dept_slots, start=1):
        pool = teachers_by_dept[did]
        manager = random.choice(pool) if pool else random.randint(1, N_TEACHERS)
        departments.append((uni, manager, f"{BASE_NAMES[did % len(BASE_NAMES)]} {did}"))
    bulk("INSERT INTO department(uni_id, manager_id, name) VALUES (?, ?, ?)", departments)

    bulk("UPDATE teacher SET department_id = ? WHERE id = ?",
         [(did, tid) for did, pool in teachers_by_dept.items() for tid in pool], step=50000)

    students = []
    for sid in range(1, N_STUDENTS + 1):
        fn, ln = random.choice(FIRST), random.choice(LAST)
        students.append((fn, ln, f"{clean(fn)}.{clean(ln)}.{sid}@{random.choice(DOMAINS)}",
                         random.randint(1, n_departments), random.randint(1, 6)))
    bulk("INSERT INTO students(name, lastname, email, department_id, year) VALUES (?, ?, ?, ?, ?)", students, step=50000)

    founded_pool = date_pool(1000, datetime(1995, 1, 1), datetime(2026, 6, 1))
    clubs = []
    presidents = {}
    for cid in range(1, N_CLUBS + 1):
        pres = random.randint(1, N_STUDENTS)
        presidents[cid] = pres
        clubs.append((f"{random.choice(WORDS)} {random.choice(CLUB_TYPES)} {cid}",
                      random.choice(founded_pool), pres, 1 if random.random() < 0.08 else 0))
    bulk("INSERT INTO club(name, founded_at, president_id, closed) VALUES (?, ?, ?, ?)", clubs)

    since_pool = date_pool(1000, datetime(2016, 1, 1), datetime(2026, 9, 1))
    stream("INSERT INTO members(student_id, club_id, member_since, membership_status) VALUES (?, ?, ?, ?)",
           (row
            for cid in range(1, N_CLUBS + 1)
            for row in (
                [(presidents[cid], cid, random.choice(since_pool), "president")] +
                [(sid, cid, random.choice(since_pool), "member")
                 for sid in random.sample(range(1, N_STUDENTS + 1), random.randint(4, 40))
                 if sid != presidents[cid]])))

    event_pool = date_pool(2000, datetime(2026, 11, 12), datetime(2027, 12, 31))
    events = [(f"{fake.catch_phrase()}", random.randint(10, 5000), random.choice(event_pool),
               None if random.random() < 0.25 else fake.city(),
               0.0 if random.random() < 0.4 else round(random.uniform(1, 250), 2))
              for _ in range(N_EVENTS)]
    bulk("INSERT INTO event(name, capacity, time, location, price) VALUES (?, ?, ?, ?, ?)", events)

    event_ids = list(range(1, N_EVENTS + 1))

    def gen_register():
        for sid in range(1, N_STUDENTS + 1):
            for eid in random.sample(event_ids, random.randint(0, 4)):
                yield (sid, eid)

    stream("INSERT INTO register(student_id, event_id) VALUES (?, ?)", gen_register())

    con.execute("COMMIT")

    fk = cur.execute("PRAGMA foreign_key_check").fetchall()
    ok = cur.execute("PRAGMA integrity_check").fetchone()[0]
    print("foreign_key_check:", "OK" if not fk else fk[:5])
    print("integrity_check:", ok)
    total = 0
    for table in ["country", "state", "city", "university", "teacher", "department", "students", "club", "members", "event", "register"]:
        n = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        total += n
        print(f"{table:>12}: {n:>9}")
    print(f"{'TOTAL':>12}: {total:>9}")
    con.close()


if __name__ == "__main__":
    main()
