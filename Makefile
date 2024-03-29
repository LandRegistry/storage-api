unittest:
	if [ -z ${report} ]; then py.test; else py.test --junitxml=test-output/unit-test-output.xml --cov-report=html:test-output/unit-test-cov-report; fi

integrationtest:
	py.test --junitxml=test-output/integration-test-output.xml integration_tests

run:
	python3 manage.py runserver

lint:
	flake8 ./
