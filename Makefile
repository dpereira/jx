.PHONY: test

gargantua:
	@PYTHONPATH=src/ python src/jx test/json/gargantua.json

glossary:
	@PYTHONPATH=src/ python src/jx test/json/glossary.json

flat:
	@PYTHONPATH=src/ python src/jx test/json/flat.json
