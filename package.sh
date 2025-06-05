# python -m pip install --upgrade twine
# python -m pip install --upgrade build
rm -rf dist/*
python -m build
twine upload dist/* --non-interactive -u __token__ -p $PYPI_TOKEN 
