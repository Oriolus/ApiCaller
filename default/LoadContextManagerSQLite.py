import sqlite3
import uuid
from typing import Optional

from EntityLoader import LoadContextManager, LoadContext
from StateMachine import StateMachineDao


class HttpParams(object):
    def __init__(self,
                 uid: uuid.UUID,
                 resource: str,
                 params: str,
                 headers: str):
        self.Uid = uid
        self.Resource = resource
        self.Params = params
        self.Headers = headers


class HttpParamsDao(object):
    def __init__(self, connection_string: str):
        assert connection_string

        self.__connection_string = connection_string  # type: str
        self.__connection = None  # type: sqlite3.Connection
        self.__is_closed = False

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self):
        if not self.__connection:
            self.__connection = sqlite3.connect(self.__connection_string)

    def close(self):
        if self.__connection and (not self.__is_closed):
            self.__connection.close()
            self.__connection = None
            self.__is_closed = True

    def insert(self, obj: HttpParams) -> HttpParams:
        sql = '''
insert into
    "http_params"
("uid", "resource", "headers", "params")
values
(:uid, :resource, :headers, :params)
'''
        args = {
            'uid': obj.Uid.urn,
            'resource': obj.Resource,
            'headers': obj.Headers,
            'params': obj.Params
        }

        cursor = self.__connection.execute(sql, args)
        updated = cursor.rowcount
        self.__connection.commit()

        return obj

    def update(self, obj: HttpParams) -> HttpParams:
        sql = '''
update
    "http_header"
set
    "resource" = :resource,
    "params" = :params,
    "headers" = :headers
where
    "uid" = :uid
'''
        args = {
            'uid': obj.Uid.urn,
            'resource': obj.Resource,
            'headers': obj.Headers,
            'params': obj.Params
        }

        cursor = self.__connection.execute(sql, args)
        updated = cursor.rowcount
        self.__connection.commit()

        return obj

    def by_uid(self, uid: str) -> Optional[HttpParams]:
        sql = '''
select
    uid,
    "resource",
    "headers",
    "params"
from
    "http_params"
where
    uid = :uid
'''
        args = {
            'uid': uid
        }
        cursor = self.__connection.execute(sql, args)
        if cursor.rowcount <= 0:
            return None
        row = cursor.fetchone()
        params = HttpParams(
            uid=uuid.UUID(row[0]),
            resource=row[1],
            params=row[2],
            headers=row[3]
        )
        cursor.close()
        return params


class LoadContextManagerSQLite(LoadContextManager):
    def __init__(self,
                 state_machine_dao: StateMachineDao,
                 http_params_dao: HttpParamsDao):
        assert state_machine_dao
        assert http_params_dao

        self.__state_machine_dao = state_machine_dao
        self.__http_params_dao = http_params_dao

    def next(self) -> Optional[LoadContext]:
        next_resource = self.__state_machine_dao.get_unsuccessful()

        if next_resource:
            http_params = self.__http_params_dao.by_uid(next_resource.uid.urn)

            if http_params:
                return LoadContext(
                    http_params.Uid,
                    http_params.Resource,
                    http_params.Params,
                    http_params.Headers,
                    next_resource,
                    None
                )
            else:
                return LoadContext(
                    next_resource.uid,
                    next_resource.resource,
                    None,
                    None,
                    next_resource,
                    None
                )

        return None

