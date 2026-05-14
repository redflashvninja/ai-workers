.PHONY: install setup serve chat test lint

install:
	pip install -r requirements.txt

setup:
	python setup_google.py

serve:
	python main.py serve

chat:
	python main.py chat

markets:
	python main.py markets "$(q)"

agenda:
	python main.py agenda --days 7

lint:
	python -m py_compile agents/*.py integrations/*.py app/server.py main.py config.py
	@echo "All files compile OK"
