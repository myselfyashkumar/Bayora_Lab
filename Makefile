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
	docker compose down -v

.PHONY: new up test demo showcase report serve publish down
