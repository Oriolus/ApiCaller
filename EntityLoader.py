import time

from typing import Optional
from StateMachine import State, StateMachine


class LoadContext:
    def __init__(self, uid, resource, params, headers, load_object: State, obj=None):
        self.Uid = uid
        self.Resource = resource
        self.params = params
        self.headers = headers
        self.LoadObject = load_object
        self.obj = obj


class LoadResult:
    def __init__(
            self,
            result,
            current_context: LoadContext,
            resp_text_data: Optional[str],
            resp_raw_data,
            resp_additional_info
    ):
        self.result = result
        self.current_context = current_context
        self.resp_raw_data = resp_raw_data
        self.resp_text_data = resp_text_data
        self.resp_additional_info = resp_additional_info

    def is_success(self) -> bool:
        raise NotImplemented()


class LoadContextManager:
    def next(self) -> Optional[LoadContext]:
        raise NotImplemented()


class LoadBehaviour:

    def load(self, obj: LoadContext) -> Optional[LoadResult]:
        raise NotImplemented()

    def pre_load(self, obj: LoadContext):
        """
        represents preprocessing logic
        this method is called before load() method call
        :param obj: context of current load operation
        :return:
        """
        raise NotImplemented()

    def handle_error(self, load_context: LoadContext, load_result: LoadResult, error_text: str):
        """
        represent handler of unexpected errors
        this method is called after load_context.LoadObject's state was changed by StateMachine
        :param load_context: context of current load operation
        :param load_result: result (if exists) of current load operation
        :param error_text: string-represented information about error
        :return:
        """
        raise NotImplemented()

    def post_load(self, load_result: LoadResult):
        """
        represents pos-processing logic
        this method is called after load() method call
        :param load_result:
        :return:
        """
        raise NotImplemented()


class WaitBehaviour:
    def wait(self, load_duration: int):
        """
        :param load_duration: duration of loading operation in milliseconds
        :return: void
        """
        raise NotImplemented()


class EntityLoader:
    """
    container-class, implementing loading objects from StateMachineDao.get_unsuccessful(),
    witch state maintains by StateMachine implementation
    """
    def __init__(
        self,
        load_context_manager: LoadContextManager,
        load_behaviour: LoadBehaviour,
        wait_behaviour: WaitBehaviour,
        state_machine: StateMachine
    ):
        """

        :param load_context_manager: implementation of LoadContextManager
        :param load_behaviour: implementation of LoadBehaviour
        :param wait_behaviour: implementation of WaitBehaviour
        :param state_machine: implementation of StateMachine
        """
        assert load_behaviour
        assert wait_behaviour
        assert state_machine
        assert load_context_manager

        self.__load_context_manager = load_context_manager
        self.__load_behaviour = load_behaviour
        self.__wait_behaviour = wait_behaviour
        self.__state_machine = state_machine

    def load(self) -> Optional[LoadResult]:
        """
        load next unloaded objects from StateMachineDao.get_unsuccessful
        :return: count of loaded objects
        """

        started_at = time.perf_counter()
        result = self.__load()
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        self.__wait_behaviour.wait(duration_ms)

        return result

    def __load(self) -> Optional[LoadResult]:

        load_context = self.__load_context_manager.next()
        load_result = None

        if load_context:
            try:

                load_context.LoadObject = self.__state_machine.to_processing(load_context.LoadObject)

                self.__load_behaviour.pre_load(load_context)

                load_result = self.__load_behaviour.load(load_context)

                if load_result:
                    if not load_result.is_success():
                        load_result.current_context.LoadObject.error = load_result.resp_text_data
                    self.__state_machine.change_state(load_result.current_context.LoadObject)

                self.__load_behaviour.post_load(load_result)

                return load_result

            except Exception as e:
                load_context.LoadObject.error = str(e)
                # warning: passing here after falling in __state_machine.to_processing ....
                self.__state_machine.change_state(load_context.LoadObject)
                self.__load_behaviour.handle_error(load_context, load_result, str(e))
        return load_result
