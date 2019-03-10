import os
import psycopg2
import psycopg2.errorcodes


def open_db():
    """Opens the database
    """
    return psycopg2.connect(
            database=os.environ['DB_NAME'] or 'microtiling',
            user=os.environ['DB_USER'] or 'microtiling',
            port=os.environ['DB_PORT'] or 26257,
            host=os.environ['DB_HOST'] or 'localhost'
    )


def onestmt(conn, sql):
    with conn.cursor() as cur:
        cur.execute(sql)


def run_transaction(conn, op):
    """Runs an operation *op* on *conn* until it either works
    or can't be recovered
    """
    with conn:
        onestmt(conn, "SAVEPOINT cockroach_restart")
        while True:
            try:
                # Attempt the work.
                op(conn)

                # If we reach this point, commit.
                onestmt(conn, "RELEASE SAVEPOINT cockroach_restart")
                break

            except psycopg2.OperationalError as e:
                if e.pgcode != psycopg2.errorcodes.SERIALIZATION_FAILURE:
                    # A non-retryable error; report this up the call stack.
                    raise e
                # Signal the database that we'll retry.
                onestmt(conn,
                        "ROLLBACK TO SAVEPOINT cockroach_restart")


def update_state(db, new_state, job_id):
    """Update the state in *db* for the job *job_id*
    if it is less than *new_state*
    """
    with db.cursor() as cur:
        current_state = cur.execute(
                'SELECT state FROM jobs WHERE jobs.id = ?',
                (job_id,)
        ).fetchone()

    if current_state is not None:
        if current_state < new_state:
            def update_db(cur):
                cur.execute(
                        'UPDATE jobs SET state = ?',
                        ' WHERE jobs.id = ?',
                        (new_state, job_id)
                )
            run_transaction(db, update_db)
