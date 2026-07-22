PYTHON ?= python3
PLUGIN_ARCHIVE := dist/dreamteam-claude-code-plugin-0.4.4.zip

.PHONY: sync validate test compile check measure build smoke release

sync:
	$(PYTHON) scripts/sync_claude_adapter.py

validate:
	$(PYTHON) scripts/validate.py

test:
	$(PYTHON) -m unittest discover -s tests -v

compile:
	$(PYTHON) -m compileall dreamteam adapters/claude-code/plugins/dreamteam

check: sync
	git diff --exit-code
	$(MAKE) validate test compile

measure:
	$(PYTHON) scripts/measure.py

build:
	$(PYTHON) scripts/build_release.py

smoke:
	$(PYTHON) scripts/smoke_plugin_artifact.py $(PLUGIN_ARCHIVE)

release: check measure build smoke
