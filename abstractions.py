from typing import List, Dict, Optional, Callable


class LoadContext:
    def __init__(self, url: str, params, headers, obj=None):
        self.url = url
        self.params = params
        self.headers = headers
        self.obj = obj

    @staticmethod
    def get_simplified(url: str, obj):
        return LoadContext(
            url,
            None,
            None,
            obj
        )

    def next(self) -> Optional:
        pass

    def get_simplified_load_result(
            self,
            result,
            next_load_context
    ):
        return self.get_load_result(
            result, None, None, None, None, next_load_context
        )

    def get_load_result(
            self,
            result,
            resp_status: int,
            resp_headers: Optional[Dict] = None,
            resp_raw_data: Optional[Dict] = None,
            resp_text_data: Optional[str] = None,
            next_load_context=None
    ):
        return LoadResult(
            result,
            self,
            resp_status,
            resp_headers,
            resp_raw_data,
            resp_text_data,
            next_load_context
        )


class LoadResult:
    def __init__(
            self,
            result,
            current_context: LoadContext,
            resp_status: int,
            resp_headers: Optional[Dict],
            resp_raw_data: Optional[Dict],
            resp_text_data: Optional[str],
            next_load_context: Optional[LoadContext]
    ):
        self.result = result
        self.current_context = current_context
        self.resp_status = resp_status
        self.resp_headers = resp_headers
        self.resp_raw_data = resp_raw_data
        self.resp_text_data = resp_text_data
        self.next_load_context = next_load_context


class WaitBehaviour:
    def __init__(self):
        pass

    def wait(self, load_result: LoadResult):
        pass


class LoadBehaviour:
    def __init__(self):
        pass

    def get_load_context(self) -> LoadContext:
        pass

    def load(self, obj: LoadContext) -> Optional[LoadResult]:
        pass

    def pre_load(self, obj: LoadContext):
        pass

    def post_load(self, load_result: LoadResult):
        pass


class LoaderPersistence:
    def __int__(self):
        pass


class EntityLoader:
    def __init__(
        self,
        load_behaviour: LoadBehaviour,
        wait_behaviour: WaitBehaviour
    ):
        assert load_behaviour
        self._load_behaviour = load_behaviour
        self._wait_behaviour = wait_behaviour

    def load(self):
        self.__load()

    def __load(self):

        current_load_context = self._load_behaviour.get_load_context()

        while current_load_context:
            _loading = create_loading(
                current_load_context.url,
                current_load_context.headers,
                current_load_context.headers
            )
            load_result = None
            try:
                self._load_behaviour.pre_load(current_load_context)
                load_result = self._load_behaviour.load(current_load_context, _loading)
                if load_result:
                    _loading.set_finish_data(
                        load_result.resp_status,
                        load_result.resp_headers,
                        load_result.resp_raw_data,
                        load_result.resp_text_data
                    )
                self._load_behaviour.post_load(load_result)
            except Exception as e:
                _loading.error = str(e)
                load_result = self._load_behaviour.handle_error(current_load_context, e, _loading)
            finally:
                finish_loading(_loading)
                self._wait_behaviour.wait(load_result)
            current_load_context = load_result.next_load_context if load_result else None
