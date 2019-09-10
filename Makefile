install:
	pip install pipenv
	pipenv sync -d

test:
	cd django_proxysql && pipenv run -- coverage run --include="django_proxysql/*" manage.py test django_proxysql

coveralls:
	cd django_proxysql && pipenv run -- coveralls
