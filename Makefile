PYTHONPATH := ..

run_example:
	cd example && $(MAKE)

.IGNORE: run_example
