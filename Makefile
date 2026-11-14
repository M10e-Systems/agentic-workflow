PYTHON ?= python3

.PHONY: test
test:
	$(PYTHON) -c 'import unittest; import unittest.mock'
	$(PYTHON) -m unittest discover -s tools/workflow_state/tests -p 'test_*.py' -v
