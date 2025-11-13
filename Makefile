%: build

build: pagerduty/* pyproject.toml
	rm -f dist/* && uv build

docs/index.html: build pyproject.toml pagerduty/* CHANGELOG.rst sphinx/source/*
	rm -fr ./docs && cd sphinx && uv run make html && cd .. && mv sphinx/build/html ./docs && touch ./docs/.nojekyll

docs: docs/index.html build

testpublish: build
	./publish-test.sh

publish: build
	uv run twine upload dist/*.tar.gz dist/*.whl
