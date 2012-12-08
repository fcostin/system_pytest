system_tests:
	py.test --cov footils --cov-report term-missing --test-data-dir footils_test_data test_footils/

.PHONY: system_tests
