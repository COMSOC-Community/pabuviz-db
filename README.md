# pb-database

## Get started:
```
pip install numpy django djangorestframework django-cors-headers pabutools

python manage.py makemigrations
python manage.py migrate
python manage.py initialize_db
python manage.py add_election -d <path to .pb file directory> -v 3
python manage.py compute_properties -v 3

python manage.py runserver
```
