import json
import time
import requests
from typing import Optional

from EntityLoader import LoadBehaviour, WaitBehaviour, LoadResult, LoadContext


class HttpLoadResult(LoadResult):
    def __init__(
            self,
            result,
            current_context: LoadContext,
            resp_text_data: Optional[str],
            resp_raw_data,
            resp_additional_info
    ):
        super().__init__(result, current_context, resp_text_data,resp_raw_data, resp_additional_info)

    def is_success(self) -> bool:
        return self.result.status_code < 400


class HttpLoadBehaviour(LoadBehaviour):
    def __init__(self):
        pass

    def load(self, obj: LoadContext) -> Optional[LoadResult]:

        j_headers = json.loads(obj.headers) if obj.headers else None
        j_params = json.loads(obj.params) if obj.params else None
        resp = requests.get(obj.Resource, headers=j_headers, params=j_params)

        load_result = HttpLoadResult(
            result=resp,
            current_context=obj,
            resp_text_data=resp.text,
            resp_raw_data=resp.content,
            resp_additional_info=None
        )

        return load_result

    def pre_load(self, obj: LoadContext):
        pass

    def handle_error(self, load_context: LoadContext, load_result: LoadResult, error_text: str):
        pass

    def post_load(self, load_result: LoadResult):
        pass


class SimpleWaitBehaviour(WaitBehaviour):
    def __init__(self, milliseconds):
        self.__wait_milliseconds = milliseconds

    def wait(self, load_duration: int):
        if load_duration >= self.__wait_milliseconds:
            return

        time.sleep((self.__wait_milliseconds - load_duration) / 1000.0)
