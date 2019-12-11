install:
	pip install pipenv
	pipenv install --dev

test:
	pipenv run -- coverage run --include="django_proxysql/backends/*" django_proxysql/manage.py test main

coveralls:
	pipenv run -- coveralls

clean:
	rm -rf dist build *.egg-info

publish:
	$(MAKE) clean
	pipenv run python setup.py sdist
	pipenv run twine upload dist/django-proxysql-?.?.tar.gz
