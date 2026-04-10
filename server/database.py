import sqlite3, os, time

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "auction.db")

def connect():
    return sqlite3.connect(DB_PATH)

# ---------------- INIT ----------------
def init_db():
    conn = connect()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS items(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        highest_bid INTEGER,
        winner TEXT,
        end_time REAL
    )
    """)

    # default admin
    c.execute("INSERT OR IGNORE INTO users VALUES ('admin','admin','admin')")

    conn.commit()
    conn.close()

# ---------------- USER ----------------
def register_user(u,p):
    conn=connect(); c=conn.cursor()
    try:
        role="admin" if u=="admin" else "user"
        c.execute("INSERT INTO users VALUES (?,?,?)",(u,p,role))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

def login_user(u,p):
    conn=connect(); c=conn.cursor()
    c.execute("SELECT role FROM users WHERE username=? AND password=?", (u,p))
    r=c.fetchone()
    conn.close()
    return r

# ---------------- ITEMS ----------------
def insert_default_items():
    conn=connect(); c=conn.cursor()
    c.execute("SELECT COUNT(*) FROM items")

    if c.fetchone()[0]==0:
        now=time.time()
        c.executemany(
            "INSERT INTO items(name,highest_bid,winner,end_time) VALUES (?,?,?,?)",
            [("Laptop",0,None,now+300),
             ("Phone",0,None,now+300)]
        )

    conn.commit(); conn.close()

def get_items():
    conn=connect(); c=conn.cursor()
    c.execute("SELECT * FROM items")
    rows=c.fetchall()
    conn.close()
    return rows

def update_bid(i,u,a):
    conn=connect(); c=conn.cursor()
    c.execute("UPDATE items SET highest_bid=?,winner=? WHERE id=?", (a,u,i))
    conn.commit(); conn.close()

def add_item(name):
    conn=connect(); c=conn.cursor()
    c.execute("INSERT INTO items(name,highest_bid,winner,end_time) VALUES (?,?,?,?)",
              (name,0,None,time.time()+300))
    conn.commit(); conn.close()

def remove_item(i):
    conn=connect(); c=conn.cursor()
    c.execute("DELETE FROM items WHERE id=?", (i,))
    conn.commit(); conn.close()

def get_expired_items():
    conn = connect()
    c = conn.cursor()

    current = time.time()

    c.execute("SELECT * FROM items WHERE end_time <= ?", (current,))
    rows = c.fetchall()

    conn.close()
    return rows
