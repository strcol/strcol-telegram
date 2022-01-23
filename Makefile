install: requirements.txt
	python3 -m venv venv
	./venv/bin/python3 install -r requirements.txt

run: venv
	./venv/bin/python3 -B app.py