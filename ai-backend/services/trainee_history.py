import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "trainee_history.db"


def create_database():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS training_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT UNIQUE,
            trainee_id TEXT,
            scenario_id TEXT,
            overall_score REAL,
            decision_quality REAL,
            safety_awareness REAL,
            rescue_effectiveness REAL,
            adaptability REAL,
            performance_class TEXT,
            weakest_competency TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()
    connection.close()


def save_session(
    session_id,
    trainee_id,
    scenario_id,
    overall_score,
    decision_quality,
    safety_awareness,
    rescue_effectiveness,
    adaptability,
    performance_class,
    weakest_competency
):

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO training_sessions (
            session_id,
            trainee_id,
            scenario_id,
            overall_score,
            decision_quality,
            safety_awareness,
            rescue_effectiveness,
            adaptability,
            performance_class,
            weakest_competency
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        trainee_id,
        scenario_id,
        overall_score,
        decision_quality,
        safety_awareness,
        rescue_effectiveness,
        adaptability,
        performance_class,
        weakest_competency
    ))

    connection.commit()
    connection.close()


def get_history(trainee_id):

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM training_sessions
        WHERE trainee_id = ?
        ORDER BY created_at
    """, (trainee_id,))

    rows = cursor.fetchall()

    connection.close()

    return rows


create_database()