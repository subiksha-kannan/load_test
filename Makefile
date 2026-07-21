TEST      ?= $(error TEST is required, e.g. TEST=triton-metadata-attr-g4)
ENV_FILE  := tests/$(TEST)/env.sh
CONTEXT   := $(shell sh -c '. $(ENV_FILE) && echo $$CONTEXT')
NAMESPACE := $(shell sh -c '. $(ENV_FILE) && echo $$NAMESPACE')
KUBECTL    = kubectl --context=$(CONTEXT) -n $(NAMESPACE)
DEPLOY     = loadtest-$(TEST)

.PHONY: sync deploy diff tail portforward status delete

# Kustomize cannot read files outside the test dir — copy shared modules in.
sync:
	cp shared/triton_http.py shared/payloads.py tests/$(TEST)/

deploy: sync
	kubectl --context=$(CONTEXT) apply -k tests/$(TEST)
	$(KUBECTL) rollout status deploy/$(DEPLOY)

diff: sync
	kubectl --context=$(CONTEXT) diff -k tests/$(TEST) || true

tail:
	$(KUBECTL) logs -f deploy/$(DEPLOY)

portforward:
	@echo "Open http://localhost:8089"
	$(KUBECTL) port-forward svc/$(DEPLOY) 8089:8089

status:
	$(KUBECTL) get deploy,pods,svc -l app=loadtest

delete: sync
	kubectl --context=$(CONTEXT) delete -k tests/$(TEST)
