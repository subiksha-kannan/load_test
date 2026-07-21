import os

import numpy as np
from locust import LoadTestShape, constant_throughput, task

from triton_http import TritonHTTPUser
from payloads import random_jpeg_bytes


# ── Mode selection (set in kustomization.yaml env) ────────────────────────
LOAD_MODE = os.getenv("LOAD_MODE", "ramp")   # "ramp" (Tests 1+2) or "constant" (Test 3)
USER_RPS  = float(os.getenv("USER_RPS", "2.0"))  # only used when LOAD_MODE=constant

# ── Model-specific params ─────────────────────────────────────────────────
ATTRIBUTE_IDS = [a.strip() for a in os.getenv("ATTRIBUTE_IDS", "").split(",") if a.strip()]
IMAGE_SIZE    = int(os.getenv("IMAGE_SIZE", "512"))
TOP_N         = int(os.getenv("TOP_N", "5"))


class MetadataPipelineUser(TritonHTTPUser):
    MODEL_NAME   = "metadata_prediction_pipeline"
    OUTPUT_NAMES = ["PREDICTIONS_JSON"]

    # In constant mode, each user fires exactly USER_RPS req/sec.
    # In ramp mode, we inherit `between(0, 0.05)` from the base class (fire ASAP).
    if LOAD_MODE == "constant":
        wait_time = constant_throughput(USER_RPS)

    def build_inputs(self):
        # Match team load-test-http.py shapes:
        #   INPUT_IMAGE:   [1, 1]
        #   ATTRIBUTE_IDS: [1, N]  ← NOT [N, 1]
        #   TOP_N:         [1, 1]
        import tritonclient.http as httpclient

        image_np = np.array([[random_jpeg_bytes(IMAGE_SIZE)]], dtype=object)
        attrs_np = np.array([ATTRIBUTE_IDS], dtype=object)  # shape [1, N]
        topn_np = np.array([[TOP_N]], dtype=np.int32)

        inp_image = httpclient.InferInput("INPUT_IMAGE", image_np.shape, "BYTES")
        inp_image.set_data_from_numpy(image_np)
        inp_attrs = httpclient.InferInput("ATTRIBUTE_IDS", attrs_np.shape, "BYTES")
        inp_attrs.set_data_from_numpy(attrs_np)
        inp_topn = httpclient.InferInput("TOP_N", topn_np.shape, "INT32")
        inp_topn.set_data_from_numpy(topn_np)
        return [inp_image, inp_attrs, inp_topn]

    @task
    def predict(self):
        self.infer("predict::metadata_prediction_pipeline")


# ── Ramp shape (only active in ramp mode) ─────────────────────────────────
if LOAD_MODE == "ramp":

    class StepLoad(LoadTestShape):
        """+20 users every 30s up to 500 users, then hold for 5 min. ~17.5 min total."""
        step_users   = 20
        step_seconds = 30
        max_users    = 500
        hold_seconds = 300

        def tick(self):
            t = self.get_run_time()
            ramp = (self.max_users // self.step_users) * self.step_seconds
            if t < ramp:
                step = int(t / self.step_seconds) + 1
                return (step * self.step_users, self.step_users)
            if t < ramp + self.hold_seconds:
                return (self.max_users, self.step_users)
            return None