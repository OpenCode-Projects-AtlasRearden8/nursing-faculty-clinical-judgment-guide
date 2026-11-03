.PHONY: build test site clean serve

build:
	python3 tools/build.py

test: build
	python3 tests/test_build.py

site: build

serve:
	python3 -m http.server 8000 --directory site

clean:
	rm -rf site
