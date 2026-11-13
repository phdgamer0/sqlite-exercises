
CREATE TABLE country (
	id INTEGER PRIMARY KEY,
	name TEXT NOT NULL
);

CREATE TABLE state (
	id INTEGER PRIMARY KEY,
	name TEXT NOT NULL,
	country_id INTEGER REFERENCES country(id)
);

CREATE TABLE city (
	id INTEGER PRIMARY KEY,
	name TEXT NOT NULL,
	population INTEGER NOT NULL,
	area REAL NOT NULL,
	state_id INTEGER REFERENCES state(id)
);

CREATE TABLE university (
	id INTEGER PRIMARY KEY,
	name TEXT NOT NULL,
	founding_date DATETIME NOT NULL,
	city_id INTEGER REFERENCES city(id)
);

CREATE TABLE teacher (
	id INTEGER PRIMARY KEY,
	name TEXT NOT NULL,
	lastname TEXT NOT NULL,
	email TEXT NOT NULL UNIQUE,
	paycheck REAL NOT NULL,
	department_id INTEGER REFERENCES department(id),
	worked_since DATETIME NOT NULL
);

CREATE TABLE department (
	id INTEGER PRIMARY KEY,
	uni_id INTEGER REFERENCES university(id),
	manager_id INTEGER REFERENCES teacher(id),
	name TEXT NOT NULL UNIQUE
);

CREATE TABLE students (
	id INTEGER PRIMARY KEY,
	name TEXT NOT NULL,
	lastname TEXT NOT NULL,
	email TEXT NOT NULL UNIQUE,
	department_id INTEGER NOT NULL REFERENCES department(id),
	year INTEGER NOT NULL CHECK(year BETWEEN 1 AND 6)
);

CREATE TABLE club (
	id INTEGER PRIMARY KEY,
	name TEXT NOT NULL UNIQUE,
	founded_at DATETIME NOT NULL,
	president_id INTEGER,
	closed INTEGER NOT NULL DEFAULT 0,
	FOREIGN KEY (president_id) REFERENCES students(id)
);

CREATE TABLE members (
	student_id INTEGER NOT NULL,
	club_id INTEGER NOT NULL,
	member_since DATETIME,
	membership_status TEXT NOT NULL DEFAULT 'member' CHECK(membership_status IN ('member', 'president')),
	PRIMARY KEY (student_id, club_id),
	FOREIGN KEY (student_id) REFERENCES students(id),
	FOREIGN KEY (club_id) REFERENCES club(id)
);

CREATE TABLE event (
	id INTEGER NOT NULL PRIMARY KEY,
	name TEXT NOT NULL,
	capacity INTEGER NOT NULL CHECK(capacity > 0),
	time DATETIME NOT NULL,
	location TEXT CHECK(location IS NULL OR LENGTH(location) > 0),
	price REAL NOT NULL DEFAULT 0.0 CHECK(price >= 0.0)
);

CREATE TABLE register (
	event_id INTEGER NOT NULL,
	student_id INTEGER NOT NULL,
	PRIMARY KEY(student_id, event_id),
	FOREIGN KEY (student_id) REFERENCES students(id),
	FOREIGN KEY (event_id) REFERENCES event(id)
);
