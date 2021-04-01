PKG := btype
PKG_VERS := 0.1.0
PKG_DEPS := \
		setup.cfg \
		setup.py \
		$(PKG)/*.py

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
	sudo pip3 uninstall -y $(PKG)
	sudo pip3 install dist/$(PKG)-$(PKG_VERS)-py3-none-any.whl

.PHONY: uninstall
uninstall:
	sudo pip3 uninstall $(PKG)

dist/$(PKG)-$(PKG_VERS)-py3-none-any.whl: $(PKG_DEPS) Makefile
	python3 setup.py --quiet sdist bdist_wheel
	python3 -m twine check $@
