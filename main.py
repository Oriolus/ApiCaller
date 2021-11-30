from default.StateMachineDao import SQLiteStateMachineDao
from default.LoadContextManagerSQLite import LoadContextManagerSQLite, HttpParamsDao
from default.HttpLoadBehaviour import HttpLoadBehaviour, SimpleWaitBehaviour

from EntityLoader import EntityLoader
from StateMachine import State, StateMachine

# state = State(
#     uid=uuid.uuid4()
#     , resource='some resource'
#     , state=State.CREATED
#     , attempt_count=0
# )

conn_string = 'C:\\Users\\User\\PycharmProjects\\ApiCaller\\loader.db'

exists_state_uid = 'urn:uuid:06f18e09-24f8-4aa3-a710-eb27203e0e9b'

with SQLiteStateMachineDao(conn_string) as dao:  # type: SQLiteStateMachineDao
    with HttpParamsDao(conn_string) as http_dao:

        context_manager = LoadContextManagerSQLite(dao, http_dao)
        state_machine = StateMachine(max_attempt_count=4, dao=dao)
        load_behaviour = HttpLoadBehaviour()
        wait_behaviour = SimpleWaitBehaviour(1500)

        loader = EntityLoader(context_manager, load_behaviour, wait_behaviour, state_machine)

        loaded = loader.load()

        print(loaded.result.text)


