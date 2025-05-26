# python -m pip install --upgrade twine
# python -m pip install --upgrade build
python -m build
# rm -rf dist/*
twine upload dist/* --non-interactive -u __token__ -p $PYPI_TOKEN 
