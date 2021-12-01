import uuid
import copy
from typing import Optional
from datetime import datetime, timezone


class State(object):
    """
    Representation of resource state
    """

    CREATED = 'created'
    PROCESSING = 'processing'
    SUCCESSFUL = 'successful'
    FAILED = 'failed'

    def __init__(self,
                 uid: uuid = None,
                 resource: str = None,
                 state: str = None,
                 attempt_count: int = None,
                 last_attempt: datetime = None,
                 error: str = None,
                 last_update: datetime = None,
                 version: int = None):
        self.__uid = uid  # type: uuid
        self.__resource = resource  # type: str
        self.__state = state  # type: str
        self.__attempt_count = attempt_count  # type: int
        self.__last_attempt = last_attempt  # type: datetime
        self.__error = error  # type: str
        self.__last_update = last_update  # type: datetime
        self.__version = version  # type: int

    @property
    def uid(self) -> uuid.UUID:
        return self.__uid

    @uid.setter
    def uid(self, value):
        self.__uid = value

    @property
    def resource(self):
        return self.__resource

    @resource.setter
    def resource(self, value):
        self.__resource = value

    @property
    def state(self) -> str:
        return self.__state

    @state.setter
    def state(self, value):
        self.__state = value

    @property
    def attempt_count(self):
        return self.__attempt_count

    @attempt_count.setter
    def attempt_count(self, value):
        self.__last_attempt = value

    @property
    def last_attempt(self):
        return self.__last_attempt

    @last_attempt.setter
    def last_attempt(self, value):
        self.__last_attempt = value

    @property
    def error(self):
        return self.__error

    @error.setter
    def error(self, value):
        self.__error = value

    @property
    def last_update(self):
        return self.__last_update

    @last_update.setter
    def last_update(self, value):
        self.__last_update = value

    @property
    def version(self):
        return self.__version

    @version.setter
    def version(self, value):
        self.__version = value


class StateMachineDao(object):
    def update(self, obj: State) -> State:
        raise NotImplemented()

    def create(self, obj: State) -> State:
        raise NotImplemented()

    def delete(self, obj: State) -> bool:
        raise NotImplemented()

    def by_uid(self, uid) -> State:
        raise NotImplemented()

    def get_unsuccessful(self) -> Optional[State]:
        raise NotImplemented()


class StateMachine:
    """
    ATTENTION! Using UTC
    """

    def __init__(self,
                 max_attempt_count: int,
                 dao: StateMachineDao):
        assert dao is not None
        assert max_attempt_count > 0

        self.__max_attempt_count = max_attempt_count  # type: int
        self.__dao = dao  # type: StateMachineDao

    def create(self, obj: State):
        assert obj
        assert obj.state is None

        saved = copy.deepcopy(obj)

        obj.state = State.CREATED
        obj.version = 1
        obj.last_attempt = datetime.now(timezone.utc)
        obj.last_update = datetime.now(timezone.utc)
        obj.error = None

        try:
            obj = self.__dao.update(obj)
        except Exception as e:
            obj = saved
            raise e

        return obj

    def to_processing(self, obj: State) -> State:
        assert obj
        assert obj.state == State.CREATED

        last_obj = copy.deepcopy(obj)

        obj.state = State.PROCESSING
        obj.attempt_count += 1
        obj.last_attempt = datetime.now(timezone.utc)

        try:
            self.__dao.update(obj)
        except Exception as e:
            obj = last_obj
            raise e

        return obj

    def change_state(self, obj: State) -> State:
        assert obj is not None
        assert obj.state == State.PROCESSING

        last_obj = copy.deepcopy(obj)

        if obj.error is not None:
            obj.state = State.FAILED
        elif obj.error is None:
            obj.error = None
            obj.state = State.SUCCESSFUL
        else:
            obj.error = str.format('unexpected state: {0}, error: {1}', (obj.state, str(obj.error)))

        try:
            obj = self.__dao.update(obj)
        except Exception as e:
            obj = last_obj
            raise e

        return obj
