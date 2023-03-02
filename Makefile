# Install all packages, including our own editable package.
install: 
	@pip3 install -e .

# Uninstall all packages in current environment.
uninstall:
	@bash -c 'pip uninstall -r <(pip freeze) -y'

# List all installed packages.
# We don't add our own editable package because
# pip dumps it as a git URL and not a relative path.
# Can be used to generate requirements.txt file
# with `make freeze > requirements.txt`.
freeze:
	@pip3 freeze | sed '/^-e.*/d'

# Run all tests
test:
	@python3 -m unittest discover tests/

clean:
	# Delete all __pycache__ folders
	find . -type d -name __pycache__ -exec rm -r {} \+
