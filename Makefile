
.PHONY: clean test build

clean: 
	python setup.py clean --all
	rm -rf build dist src/yakonfig.egg-info

test: install
	python setup.py test

build: clean
	python setup.py build bdist_egg sdist

install: build
	python setup.py install

register:
        ## upload both source and binary
	python setup.py sdist bdist_egg upload

check:
	pylint -i y --output-format=parseable src/`git remote -v | grep origin | head -1 | cut -d':' -f 2 | cut -d'.' -f 1`

