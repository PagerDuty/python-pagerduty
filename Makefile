%: build

build: pagerduty/* pyproject.toml
	rm -f dist/* && python3 -m build

docs/index.html: pagerduty/* README.rst CHANGELOG.rst sphinx/source/conf.py sphinx/source/*.rst
	rm -fr ./docs && cd sphinx && make html && cd .. && mv sphinx/build/html ./docs && touch ./docs/.nojekyll

docs: docs/index.html

testpublish: build
	./publish-test.sh

publish: build
	twine upload dist/*.tar.gz dist/*.whl
