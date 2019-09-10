install:
	pip install pipenv
	pipenv install --dev

test:
	cd django_proxysql && pipenv run -- coverage run --include="backends/*" manage.py test main

coveralls:
	cd django_proxysql && pipenv run -- coveralls

clean:
	rm -rf dist build *.egg-info

publish:
	$(MAKE) clean
	pipenv run python setup.py sdist
	pipenv run twine upload dist/django-proxysql-?.?.tar.gz
