import sqlite3
import os


def init_db(db_file, schema_file, log):
    """Create database if this not exists
    """
    if not os.path.exists(db_file):
        con = sqlite3.connect(db_file)
        f = open(schema_file,'r')
        schema= f.read()
        log.info("schema: %s",schema)
        con.executescript(schema)
        con.commit()
        con.close()


def query_db(query, args=(), one=False, db_file="lab_captive_portal.db"):
    """SQLite3 query for INSERT and SELECT
    """
    con = sqlite3.connect(db_file)
    cur = con.cursor()
    cur.execute(query, args)
    con.commit()
    rows = cur.fetchall()
    con.close()
    return (rows[0] if rows else None) if one else rows


def query_update_db(query, args=(), db_file="lab_captive_portal.db"):
    """SQLite3 update query
    Return: rows affected
    """
    con = sqlite3.connect(db_file)
    cur = con.cursor()
    cur.execute(query, args)
    con.commit()
    nr_rows_affected = cur.rowcount
    con.close()
    return nr_rows_affected
