include common.mk

# Our directories
API_DIR = server
DB_DIR = data
SEC_DIR = security
REQ_DIR = .
TEST_DIRS = server states

FORCE:

prod: all_tests github

github: FORCE
	- git commit -a
	git push origin master

all_tests: FORCE
	@for dir in $(TEST_DIRS); do \
		echo "=== $$dir ==="; \
		PYTHONPATH=$(CURDIR) $(MAKE) -C $$dir tests || exit 1; \
	done

dev_env: FORCE
	pip install -r $(REQ_DIR)/requirements-dev.txt
	@echo "You should set PYTHONPATH to: "
	@echo $(shell pwd)

docs: FORCE
	cd $(API_DIR); make docs
