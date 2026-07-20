
import os
import random
import time
from typing import List

import tritonclient.http as httpclient
from locust import User, between, events


class TritonHTTPUser(User):
    """Subclass this. Set MODEL_NAME and OUTPUT_NAMES, implement build_inputs()."""
    abstract = True
    wait_time = between(0.0, 0.05)

    MODEL_NAME: str = ""
    OUTPUT_NAMES: List[str] = []

    def on_start(self) -> None:
        self._url = os.environ["TRITON_URL"]
        self._model = self.MODEL_NAME or os.environ["TRITON_MODEL"]
        self._client = httpclient.InferenceServerClient(url=self._url, verbose=False)

    def build_inputs(self) -> List[httpclient.InferInput]:
        raise NotImplementedError

    def infer(self, task_name: str) -> None:
        inputs = self.build_inputs()
        outputs = [httpclient.InferRequestedOutput(o) for o in self.OUTPUT_NAMES]
        req_id = f"loadtest-{random.getrandbits(32):08x}"

        start = time.perf_counter()
        try:
            self._client.infer(model_name=self._model, inputs=inputs,
                               outputs=outputs, request_id=req_id)
            exc = None
        except Exception as e:
            exc = e

        events.request.fire(
            request_type="TRITON",
            name=task_name,
            response_time=(time.perf_counter() - start) * 1000,
            response_length=0,
            exception=exc,
        )