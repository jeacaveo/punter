# Run tests and generate coverage report.

coverage run --source=. -m unittest -v
coverage report -m
