CLI := python3 plugins/inquiry/cli/inquiry.py

.PHONY: sync test hub serve validate-registry

# spec/schemas is canonical; the plugin ships a copy because installed plugins are self-contained.
sync:
	rm -rf plugins/inquiry/cli/inquiry/schemas
	cp -R spec/schemas plugins/inquiry/cli/inquiry/schemas

test: sync
	python3 -m unittest discover -s tests -v

hub: sync
	$(CLI) hub --registry registry/projects --out site/data/projects.json

serve: hub
	python3 -m http.server -d site 8000

validate-registry: sync
	@for f in registry/projects/*.json; do $(CLI) validate --registry-entry $$f || exit 1; done
