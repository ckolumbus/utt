import sqlite3
from typing import List

from utt.api import _v1

from ...data_structures.activity import Activity

CREATE_ACTIVITIES_TABLE = """CREATE TABLE activities (
    actid integer PRIMARY KEY,
    project text,
    task text,
    start text,
    end text,
    duration integer,
    type integer,
    comment text
);"""
CREATE_TAG_TABLE = """CREATE TABLE tags (
    tagid integer PRIMARY KEY,
    tagact integer,
    tag text,
    value text,
    FOREIGN KEY(tagact) REFERENCES activities(actid)
);"""
INSERT_ACT = """INSERT INTO 
    activities(actid,project,task,start,end,duration,type,comment) 
    VALUES(NULL,?,?,?,?,?,?,?)
;"""
INSERT_TAG = """INSERT INTO 
    tags(tagid,tagact,tag,value)
    VALUES(NULL,?,?,?)
;"""


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except sqlite3.Error as e:
        print(e)


# -------------------------------------------------------------------------------------------


class SqlModel:
    def __init__(self, activities: List[Activity]):
        self._sql = sqlite3.connect(":memory:")
        self._activities = activities

        create_table(self._sql, CREATE_ACTIVITIES_TABLE)
        create_table(self._sql, CREATE_TAG_TABLE)

        self.sql_load_activities()

    def get_connection(self):
        return self._sql

    def get_cursor(self):
        return self._sql.cursor()

    def sql_load_activities(self):
        c = self._sql.cursor()
        for a in self._activities:
            ai = (a.name.project, a.name.task, a.start, a.end, (a.end - a.start).total_seconds(), a.type, a.comment)
            c.execute(INSERT_ACT, ai)

            actid = c.lastrowid
            if a.tags:
                for t in a.tags:
                    ti = (actid, t[0], t[1])
                    c.execute(INSERT_TAG, ti)
            else:
                # add empty tag to normalize for report
                ti = (actid, "", "")
                c.execute(INSERT_TAG, ti)

        self._sql.commit()


_v1.register_component(SqlModel, SqlModel)
