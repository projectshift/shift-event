import sqlalchemy as sa
from sqlalchemy.dialects import mysql


def define_tables(meta, dialect=None):
    """
    Creates table definitions and adds them to schema catalogue.
    Use your application schema when integrating into your app for migrations
    support and other good things.

    :param meta: metadata catalogue to add to
    :param dialect: str, only required for mysql to switch payload to longtext
    :return: dict
    """
    tables = dict()

    # mysql needs longtext to store enough data in text column
    text_type = sa.Text if dialect != 'mysql' else mysql.LONGTEXT

    # events
    tables['events'] = sa.Table('event_store', meta,
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('created', sa.DateTime, nullable=False, index=True),
        sa.Column('type', sa.String(256), nullable=False, index=True),
        sa.Column('author', sa.String(256), nullable=False, index=True),
        sa.Column('object_id', sa.String(256), nullable=True, index=True),
        sa.Column('payload', text_type, nullable=True),
        sa.Column('payload_rollback', text_type, nullable=True),
    )

    return tables

