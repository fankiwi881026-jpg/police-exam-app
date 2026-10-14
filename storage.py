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

# 書籤分類：升級既有資料表，舊自選股預設歸入「未分類」
def _categories_db(c):
    c.execute('CREATE TABLE IF NOT EXISTS categories(name TEXT PRIMARY KEY)')
    c.execute('INSERT OR IGNORE INTO categories(name) VALUES (?)',('未分類',))
    cols=[r[1] for r in c.execute('PRAGMA table_info(watchlist)')]
    if 'category' not in cols:c.execute("ALTER TABLE watchlist ADD COLUMN category TEXT DEFAULT '未分類'")

def categories():
    with connect() as c:
        _categories_db(c)
        return [r[0] for r in c.execute("SELECT name FROM categories ORDER BY CASE WHEN name='未分類' THEN 0 ELSE 1 END,name")]

def create_category(name):
    name=name.strip()[:30]
    if not name:raise ValueError('分類名稱不可空白')
    with connect() as c:
        _categories_db(c);c.execute('INSERT OR IGNORE INTO categories(name) VALUES (?)',(name,))

def add_watch_category(symbol,category):
    with connect() as c:
        _categories_db(c)
        c.execute('INSERT INTO watchlist(symbol,category) VALUES (?,?) ON CONFLICT(symbol) DO UPDATE SET category=excluded.category',(symbol,category))

def watches_by_category(category):
    with connect() as c:
        _categories_db(c)
        return [r[0] for r in c.execute('SELECT symbol FROM watchlist WHERE category=? ORDER BY symbol',(category,))]
