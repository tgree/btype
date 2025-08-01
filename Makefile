PKG := btype
PKG_VERS := 0.1.7
PKG_DEPS := \
		setup.cfg \
		setup.py \
		$(PKG)/*.py
PYTHON := python3

.PHONY: all
all: wheel

.PHONY: clean
clean:
	rm -rf dist $(PKG).egg-info build
	find . -name "*.pyc" | xargs rm
	find . -name __pycache__ | xargs rm -r

.PHONY: lint
lint: flake8 pylint

.PHONY: flake8
flake8:
	python3 -m flake8 $(PKG)

.PHONY: pylint
pylint:
	pylint -j2 $(PKG)

.PHONY: wheel
wheel: dist/$(PKG)-$(PKG_VERS)-py3-none-any.whl

.PHONY: install
install: wheel
	sudo pip3 uninstall -y $(PKG) --break-system-packages
	sudo pip3 install dist/$(PKG)-$(PKG_VERS)-py3-none-any.whl --break-system-packages

.PHONY: uninstall
uninstall:
	sudo pip3 uninstall $(PKG)

.PHONY: publish
publish: all
	$(PYTHON) -m twine upload \
		dist/$(PKG)-$(PKG_VERS)-py3-none-any.whl \
		dist/$(PKG)-$(PKG_VERS).tar.gz

dist/$(PKG)-$(PKG_VERS)-py3-none-any.whl: $(PKG_DEPS) Makefile
	python3 setup.py --quiet sdist bdist_wheel
	python3 -m twine check $@
