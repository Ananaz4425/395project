
CREATE TABLE IF NOT EXISTS health_log (
      id            INTEGER PRIMARY KEY AUTOINCREMENT,
    date          TEXT    NOT NULL,
    mood          TEXT    NOT NULL,
    energy        TEXT    NOT NULL DEFAULT 'Medium',
    sleep_hours   REAL,
    water_intake  REAL,
    exercise      TEXT,
    notes         TEXT,
    created_at    TEXT    DEFAULT (datetime('now'))
);

-- Goals (student personal goals with deadlines)
CREATE TABLE IF NOT EXISTS goals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    category    TEXT    NOT NULL DEFAULT 'General',
    description TEXT,
    deadline    TEXT,
    status      TEXT    NOT NULL DEFAULT 'Active',
    priority    TEXT    NOT NULL DEFAULT 'Medium',
    created_at  TEXT    DEFAULT (datetime('now'))
);

-- Affirmations (daily positive affirmations)
CREATE TABLE IF NOT EXISTS affirmations (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    text        TEXT    NOT NULL,
    category    TEXT    NOT NULL DEFAULT 'General',
    is_favorite INTEGER DEFAULT 0,
    created_at  TEXT    DEFAULT (datetime('now'))
);

-- Deadlines (academic/personal deadlines)
CREATE TABLE IF NOT EXISTS deadlines (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    subject     TEXT,
    due_date    TEXT    NOT NULL,
    priority    TEXT    NOT NULL DEFAULT 'Medium',
    status      TEXT    NOT NULL DEFAULT 'Pending',
    notes       TEXT,
    created_at  TEXT    DEFAULT (datetime('now'))
);

-- ============================================================
-- SAMPLE DATA
-- ============================================================

INSERT INTO health_log (date, mood, energy, sleep_hours, water_intake, exercise, notes) VALUES
('2026-05-01', 'Great', 'High', 8.0, 2.5, '30 min run', 'Felt amazing today!'),
('2026-05-02', 'Good', 'Medium', 7.0, 2.0, 'Yoga', 'Productive study session'),
('2026-05-03', 'Okay', 'Low', 6.0, 1.5, 'Walk', 'Midterm stress kicking in'),
('2026-05-04', 'Good', 'High', 7.5, 2.2, 'Gym', 'Finished big assignment'),
('2026-05-05', 'Great', 'High', 8.5, 3.0, '45 min bike', 'Best day this week');

INSERT INTO goals (title, category, description, deadline, status, priority) VALUES
('Sleep 8 hours daily', 'Health', 'Maintain consistent sleep schedule for better focus', '2026-06-01', 'Active', 'High'),
('Drink 2.5L water daily', 'Health', 'Stay hydrated throughout the day', '2026-05-31', 'Active', 'Medium'),
('Exercise 4x per week', 'Fitness', 'Build a sustainable workout routine', '2026-06-30', 'Active', 'High'),
('Complete Final Project', 'Academic', 'Submit CS capstone project on time', '2026-05-20', 'Active', 'High'),
('Read 1 book per month', 'Personal', 'Expand knowledge outside of coursework', '2026-05-31', 'Active', 'Low');

INSERT INTO affirmations (text, category, is_favorite) VALUES
('I am capable of achieving everything I set my mind to.', 'Motivation', 1),
('My hard work today is building the future I deserve.', 'Academic', 1),
('I choose to take care of my body and mind every day.', 'Health', 1),
('Challenges make me stronger and smarter.', 'Resilience', 0),
('I am enough, exactly as I am right now.', 'Self-love', 1),
('Every step forward counts, no matter how small.', 'Motivation', 0),
('I deserve rest and it makes me more productive.', 'Balance', 1),
('My mental health is just as important as my grades.', 'Mental Health', 1);

INSERT INTO deadlines (title, subject, due_date, priority, status, notes) VALUES
('Calculus Final Exam', 'Mathematics', '2026-05-15', 'High', 'Pending', 'Chapters 8-12, focus on integrals'),
('CS Capstone Presentation', 'Computer Science', '2026-05-20', 'High', 'In Progress', 'Slides and demo required'),
('Psychology Essay', 'Psychology', '2026-05-12', 'Medium', 'Pending', '2000 words on cognitive bias'),
('Physics Lab Report', 'Physics', '2026-05-10', 'High', 'Done', 'Submitted early!'),
('Club Event Planning', 'Extracurricular', '2026-05-18', 'Low', 'Pending', 'Book the venue');