import os
import psycopg2
import configparser


def db_config(filename='/home/mick/flickr.ini'):
    """Read the database configuration info."""
    # create a parser
    config = configparser.ConfigParser()
    # read config file
    config.read(filename)

    # get postgres database settings
    db = {}
    if config.has_section('postgresql'):
        params = config.items('postgresql')
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(
            'Section postgresql not found in the {0} file'.format(filename))

    return db


def flickr_keys(filename='/home/mick/flickr.ini'):
    """Read the flickr key information."""
    # create a parser
    config = configparser.ConfigParser()
    # read config file
    config.read(filename)

    # get flickr api key and secret
    flickr_keys = {}
    if config.has_section('flickr'):
        params = config.items('flickr')
        for param in params:
            flickr_keys[param[0]] = param[1]
    else:
        raise Exception(
            'Section flickr not found in the {0} file'.format(filename))

    return flickr_keys


def connect():
    """Connect to the PostgreSQL database server."""
    conn = None
    try:
        # read connection parameters
        params = db_config()

        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params)
        conn.set_session(autocommit=True)

        # create a cursor
        cur = conn.cursor()
        print('PostgreSQL database version:')
        cur.execute('SELECT version()')

        # display the PostgreSQL database server version
        db_version = cur.fetchone()
        print(db_version)

        return conn, cur
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return None, None
    finally:
        if conn is None:
            print('Database connection closed.')


def disconnect(conn, cur):
    """Disconnect from PostgreSQL database."""
    cur.close()
    conn.close()
