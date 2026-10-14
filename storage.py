import sqlite3
from pathlib import Path
DB=Path(__file__).with_name('stockvision.sqlite3')
def connect():
    con=sqlite3.connect(DB)
    con.execute('CREATE TABLE IF NOT EXISTS watchlist(symbol TEXT PRIMARY KEY)')
    con.execute('CREATE TABLE IF NOT EXISTS alerts(id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT, direction TEXT, target REAL, fired INTEGER DEFAULT 0)')
    con.commit()
    return con

def watches():
    with connect() as c:return [r[0] for r in c.execute('SELECT symbol FROM watchlist ORDER BY symbol')]
def add_watch(s):
    with connect() as c:c.execute('INSERT OR IGNORE INTO watchlist VALUES (?)',(s,))
def remove_watch(s):
    with connect() as c:c.execute('DELETE FROM watchlist WHERE symbol=?',(s,))
def add_alert(s,d,t):
    with connect() as c:c.execute('INSERT INTO alerts(symbol,direction,target) VALUES (?,?,?)',(s,d,t))
def alerts():
    with connect() as c:return c.execute('SELECT id,symbol,direction,target,fired FROM alerts ORDER BY id DESC').fetchall()
def delete_alert(i):
    with connect() as c:c.execute('DELETE FROM alerts WHERE id=?',(i,))
def mark_fired(i):
    with connect() as c:c.execute('UPDATE alerts SET fired=1 WHERE id=?',(i,))
