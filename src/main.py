import sqlite3

conn = sqlite3.connect('fintrack.db')
cursor = conn.cursor()

conn.commit()
conn.close()