%: build

build: pagerduty/* pyproject.toml
	rm -f dist/* && python3 -m build

docs/index.html: build pyproject.toml pagerduty/* CHANGELOG.rst sphinx/source/*
	rm -fr ./docs && cd sphinx && make html && cd .. && mv sphinx/build/html ./docs && touch ./docs/.nojekyll

docs: docs/index.html pagerduty/__pycache__

# Require the module be compiled first so metadata can be used:
pagerduty/__pycache__:
	pip install .

testpublish: build
	./publish-test.sh

publish: build
	twine upload dist/*.tar.gz dist/*.whl
