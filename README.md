# load_test

In-cluster [Locust](https://locust.io/) load testing for Triton inference services.
Locust runs as a pod **next to Triton** inside the cluster; your laptop only opens the
web UI over a port-forward, so measured latency isn't skewed by port-forward RTT.

## File structure

```
.
├── Makefile                 # deploy / portforward / delete helpers (per-test)
├── k8s/base/                # shared Kubernetes manifests
│   ├── deployment.yaml      #   Locust pod (installs deps, runs locustfile)
│   ├── service.yaml         #   exposes the web UI on :8089
│   └── kustomization.yaml
├── shared/                  # reusable Python, edit these (copied into tests/ by `make sync`)
│   ├── triton_http.py       #   base Locust user that calls Triton over HTTP
│   └── payloads.py          #   input/payload generators (random images, tensors)
└── tests/                   # one folder per test target
    └── triton-metadata-attr-<gpu>/
        ├── env.sh           #   CONTEXT (cluster) + NAMESPACE for this target
        ├── kustomization.yaml  # env vars: TRITON_URL, LOAD_MODE, ATTRIBUTE_IDS, …
        └── locustfile.py    #   the actual test (builds inputs, defines load shape)
```

> `tests/*/triton_http.py` and `tests/*/payloads.py` are **copies** made by `make sync`
> (kustomize can't read files outside the test dir). They're gitignored — always edit
> the originals in `shared/`.

## Load modes

Set via `LOAD_MODE` in each test's `kustomization.yaml`:

| Mode | Purpose | Users | Duration |
|---|---|---|---|
| `ramp` | Find the service's throughput limit | driven automatically by `StepLoad` | ~17.5 min |
| `constant` | Compare latency at a fixed load | you set it: `users = target_RPS / USER_RPS` | ~10 min |

## How to run

```bash
# 1. Deploy the Locust pod for a test target
make deploy TEST=triton-metadata-attr-g4

# 2. Open the web UI (leave this running)
make portforward TEST=triton-metadata-attr-g4   # → http://localhost:8089

# 3. In the UI:
#    - ramp mode:     just click Start (StepLoad drives the user count)
#    - constant mode: set Number of users = target_RPS / USER_RPS, then Start
#
#    ⚠️ Smoke-test first: run 1 user for ~15s and confirm Failures = 0.
#       If not, check the Failures tab (shows the real Triton error) or `make tail`.
#
#    When done, Download Data → save BOTH the stats and failures CSVs.

# 4. Tear down
make delete TEST=triton-metadata-attr-g4
```

Swap `TEST=triton-metadata-attr-l4` to run against the other target.

### Make targets

| Target | Does |
|---|---|
| `make deploy TEST=…`      | sync shared files, then apply the manifests + wait for rollout |
| `make portforward TEST=…` | forward the web UI to `localhost:8089` |
| `make tail TEST=…`        | stream the Locust pod logs |
| `make status TEST=…`      | show deploy/pods/svc |
| `make delete TEST=…`      | remove everything for that test |

## Adding a new test target

1. Copy an existing `tests/triton-metadata-attr-<gpu>/` folder (K8s names must be lowercase).
2. Update `env.sh` (cluster `CONTEXT` + `NAMESPACE`) and `kustomization.yaml`
   (`TRITON_URL`, model params). Adjust `locustfile.py` if inputs differ.
3. Run with `make deploy TEST=<your-folder-name>`.

> **Tip:** input tensor shapes must match what the model expects. A wrong shape makes
> **every** request fail (100% failures). Verify with the 1-user smoke test before a full run.
