EXP_ID = $(shell cat experiments/current/exp_id 2>/dev/null)
export EXP_ID

new:      ## fresh keys, salt and canaries
	python3 tools/new_experiment.py

up:       ## build and start every container
	docker compose up -d --build

test:     ## attack our own platform, print the pass/fail table
	bash tests/run_tests.sh

demo: new up   ## one command from nothing to a running lab
	@echo "Lab running. Next: make test"

down:     ## stop and delete containers, networks and volumes
	docker compose down -v

.PHONY: new up test demo down
