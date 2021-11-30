import uuid
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from StateMachine import State, StateMachineDao


class SQLiteStateMachineDao(StateMachineDao):
    """
    ATTENTION! UTC is required
    """

    def __init__(self, connection_string):
        self.__connection_string = connection_string  # type: str
        self.__connection = None  # type: sqlite3.Connection
        self.__is_closed = False  # type: bool

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self):
        if self.__connection is None:
            self.__connection = sqlite3.connect(self.__connection_string)

    def close(self):
        if self.__connection is not None and (not self.__is_closed):
            self.__connection.close()
            self.__is_closed = True

    def __to_int_timestamp(self, value: Optional[datetime]) -> Optional[int]:
        if not value:
            return None
        return int(value.timestamp() * 1000000)

    def __from_int_timestamp(self, value: Optional[int]) -> Optional[datetime]:
        if not value:
            return None
        return datetime.fromtimestamp(value / 1000000.0, timezone.utc)

    def update(self, obj: State) -> State:
        assert obj
        assert self.__connection

        sql = '''
update
    "resource"
set
    "state" = :state
    , "resource" = :resource
    , attempt_count = :attempt_count
    , last_attempt = :last_attempt
    , "error" = :error
    , last_update = :last_update
    , "version" = :version
where
    "uid" = :uid
'''

        obj.last_update = datetime.now(timezone.utc)
        obj.version += 1

        args = {
            'state': obj.state
            , 'resource': obj.resource
            , 'attempt_count': obj.attempt_count
            , 'last_attempt': self.__to_int_timestamp(obj.last_attempt)
            , 'error': obj.error
            , 'last_update': self.__to_int_timestamp(obj.last_update)
            , 'version': obj.version
            , 'uid': obj.uid.urn
        }
        cur = self.__connection.execute(sql, args)

        # todo: check updated
        updated = cur.rowcount

        self.__connection.commit()
        return obj

    def create(self, obj: State) -> State:
        assert obj
        assert self.__connection

        sql = '''
insert into
    "resource"
("uid", "resource", "state", attempt_count, last_attempt, "error", last_update, "version")
values
(:uid, :resource, :state, :attempt_count, :last_attempt, :error, :last_update, :version)
'''

        obj.version = 1
        obj.last_update = datetime.now(timezone.utc)

        args = {
            'uid': obj.uid.urn
            , 'resource': obj.resource
            , 'state': obj.state
            , 'attempt_count': obj.attempt_count
            , 'last_attempt': self.__to_int_timestamp(obj.last_attempt)
            , 'error': obj.error
            , 'last_update': self.__to_int_timestamp(obj.last_update)
            , 'version': obj.version
        }
        cur = self.__connection.execute(sql, args)

        # todo: check updated
        updated = cur.rowcount

        self.__connection.commit()

        return obj

    def by_uid(self, uid) -> State:
        sql = '''
select
    "uid"
    , "resource"
    , "state"
    , attempt_count
    , last_attempt
    , "error"
    , last_update
    , "version"
from
    "resource"
where
    "uid" = :uid
'''
        args = {
            'uid': str(uid)
        }
        cursor = self.__connection.execute(sql, args)
        if cursor.rowcount == 0:
            return None
        row = cursor.fetchone()

        state = State(
            uuid.UUID(row[0])
            , row[1]
            , row[2]
            , row[3]
            , self.__from_int_timestamp(row[4])
            , row[5]
            , self.__from_int_timestamp(row[6])
            , row[7]
        )
        cursor.close()
        return state

    def delete(self, obj: State) -> bool:
        raise NotImplemented()

    def get_unsuccessful(self) -> Optional[State]:
        sql = '''
select
    "uid"
    , "resource"
    , "state"
    , attempt_count
    , last_attempt
    , "error"
    , last_update
    , "version"
from
    "resource"
where
    "state" = :created_state
    or
    (
        "state" = :failed_state
        and
        attempt_count < :max_attempt_count
    )
'''
        args = {
            'created_state': State.CREATED,
            'failed_state': State.FAILED,
            'max_attempt_count': 4
        }

        cursor = self.__connection.execute(sql, args)
        # if cursor.rowcount <= 0:
        #     return None
        row = cursor.fetchone()
        state = State(
            uuid.UUID(row[0])
            , row[1]
            , row[2]
            , row[3]
            , self.__from_int_timestamp(row[4])
            , row[5]
            , self.__from_int_timestamp(row[6])
            , row[7]
        )
        cursor.close()
        return state

