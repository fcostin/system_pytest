system_tests:
	py.test --cov footils --cov-report term-missing --test-data-dir footils_test_data footils_tests/

.PHONY: system_tests
