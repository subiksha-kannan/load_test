TEST      ?= $(error TEST is required, e.g. TEST=triton-metadata-attr-singapore)
ENV_FILE  := tests/$(TEST)/env.sh
CONTEXT   := $(shell sh -c '. $(ENV_FILE) && echo $$CONTEXT')
NAMESPACE := $(shell sh -c '. $(ENV_FILE) && echo $$NAMESPACE')
KUBECTL    = kubectl --context=$(CONTEXT) -n $(NAMESPACE)
DEPLOY     = loadtest-$(TEST)

.PHONY: deploy diff tail portforward status delete

deploy:
	kubectl --context=$(CONTEXT) apply -k tests/$(TEST)
	$(KUBECTL) rollout status deploy/$(DEPLOY)

diff:
	kubectl --context=$(CONTEXT) diff -k tests/$(TEST) || true

tail:
	$(KUBECTL) logs -f deploy/$(DEPLOY)

portforward:
	@echo "Open http://localhost:8089"
	$(KUBECTL) port-forward svc/$(DEPLOY) 8089:8089

status:
	$(KUBECTL) get deploy,pods,svc -l app=loadtest

delete:
	kubectl --context=$(CONTEXT) delete -k tests/$(TEST)