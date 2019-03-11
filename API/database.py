import os
import psycopg2
import psycopg2.errorcodes


def open_db():
    """Opens the database
    """
    conn = psycopg2.connect(
            database=os.environ['DB_NAME'] or 'microtiling',
            user=os.environ['DB_USER'] or 'microtiling',
            port=os.environ['DB_PORT'] or 26257,
            host=os.environ['DB_HOST'] or 'localhost'
    )

    return conn


def onestmt(conn, sql):
    with conn.cursor() as cur:
        cur.execute(sql)


def run_transaction(op):
    """Runs an operation *op* on *conn* until it either works
    or can't be recovered
    """
    
    conn = open_db()
    
    with conn:
        onestmt(conn, "SAVEPOINT cockroach_restart")
        while True:
            try:
                op(conn)
                onestmt(conn, "RELEASE SAVEPOINT cockroach_restart")
                break
            except psycopg2.OperationalError as e:
                if e.pgcode != psycopg2.errorcodes.SERIALIZATION_FAILURE:
                    raise e
                onestmt(conn, "ROLLBACK TO SAVEPOINT cockroach_restart")


def update_state(new_state, job_id):
    """Update the state in *db* for the job *job_id*
    if it is less than *new_state*
    """

    print(0)

    carrent_state = None
    with open_db().cursor() as cur:
        print('ok', os.environ['DB_HOST'])
        cur.execute(
                'SELECT state FROM jobs WHERE jobs.id = %s',
                (job_id,)
        )
        current_state = cur.fetchone()[0]

    print(1)

    if current_state is not None:
        if current_state < new_state:
            def update_db(conn):
                with conn.cursor() as cur:
                    cur.execute(
                        'UPDATE jobs SET state = %s WHERE jobs.id = %s',
                        (new_state, job_id)
                    )
                    print('héhé')
            
            print('huhuhuhhu')
            run_transaction(update_db)
            print('olala')
