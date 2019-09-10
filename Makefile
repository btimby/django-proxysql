install:
	pip install pipenv
	pipenv install --dev

test:
	cd django_proxysql && pipenv run -- coverage run --include="backends/*" manage.py test main

coveralls:
	cd django_proxysql && pipenv run -- coveralls
