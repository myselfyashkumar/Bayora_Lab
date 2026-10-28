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

showcase: ## guided plain-English demo (add AUTO=1 to run without pauses)
	python3 tools/showcase.py $(if $(AUTO),--auto,)

report:   ## rebuild the visual report for the latest run
	python3 tools/report.py

serve:    ## serve the reports at http://localhost:8080/latest_report.html
	python3 -m http.server 8080 --directory evidence

publish:  ## copy the latest report into docs/ for the GitHub Pages site
	cp evidence/latest_report.html docs/report.html
	@echo "Copied. Now: git add docs && git commit -m 'Update report' && git push"

down:     ## stop and delete containers, networks and volumes
	docker compose down -v --remove-orphans

COMPOSE_REAL = docker compose -f docker-compose.yml -f docker-compose.ollama.yml

up-real:  ## start everything with the real model (keeps current keys)
	$(COMPOSE_REAL) up -d --build

demo-real: new up-real  ## new experiment + real model
	@echo "Real-model lab running. Next: make warmup, make measure, make test"

warmup:   ## load the model into memory so the first reply is not slow
	docker compose exec -T model python -c "import httpx; print(httpx.post('http://127.0.0.1:8002/generate', json={'prompt':'hello'}, timeout=180).json())"

measure:  ## time the model and print a safe REPLY_DEADLINE_S
	docker compose exec -T model python - < tools/measure_model.py

.PHONY: new up test demo showcase report serve publish down up-real demo-real warmup measure
