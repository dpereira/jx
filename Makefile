.PHONY: test

glossary:
	@PYTHONPATH=src/ python src/jx test/json/glossary.json

flat:
	@PYTHONPATH=src/ python src/jx test/json/flat.json

big:
	@PYTHONPATH=src/ python src/jx test/json/big.json
