import sqlite3

def check_database():
    try:
        conn = sqlite3.connect('jobs.db')
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM processed_jobs')
        count = cursor.fetchone()[0]
        print(f'Total jobs recorded in DB: {count}\n')

        cursor.execute('SELECT id, org_name, role_name, discovered_date, job_url FROM processed_jobs ORDER BY id DESC')
        rows = cursor.fetchall()

        if not rows:
            print('Database is currently empty.')
            return

        for row in rows:
            print(f'ID: {row[0]}')
            print(f'  Organization : {row[1]}')
            print(f'  Role         : {row[2]}')
            print(f'  Date Added   : {row[3]}')
            print(f'  URL          : {row[4]}')
            print('-' * 50)

        conn.close()
    except sqlite3.OperationalError as e:
        print(f'Database error: {e}')

if __name__ == '__main__':
    check_database()
