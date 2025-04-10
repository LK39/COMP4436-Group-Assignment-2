import sqlite3

DATABASE_NAME = 'predictions.db'

def get_db_connection():
    """Create a new database connection."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row 
    return conn

def init_db():
    """Initialize the SQLite database and create the predictions table."""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute('DROP TABLE IF EXISTS predictions') #Debug
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT NOT NULL,
            confidence REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def insert_prediction(class_name, confidence):
    """Insert a prediction into the database."""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('''
            INSERT INTO predictions (class_name, confidence) VALUES (?, ?)
        ''', (class_name, confidence))
        conn.commit()
    except Exception as e:
        print(f"Error inserting prediction: {e}")
    finally:
        conn.close()

def fetch_predictions():
    """Fetch all predictions from the database."""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('''
            SELECT class_name, confidence FROM predictions ORDER BY timestamp DESC
        ''')
        predictions = c.fetchall()
        return [{'class_name': row['class_name'], 'confidence': row['confidence']} for row in predictions]
    except Exception as e:
        print(f"Error fetching predictions: {e}")
        return []
    finally:
        conn.close()
