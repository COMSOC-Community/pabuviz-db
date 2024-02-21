# pb-database

## Get started:

Parameterise the local settings by creating a `pb_prototype\local_settings.py` that looks like this:
```
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'secret'


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["url.where.hosted.org"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
    },
    'user_submitted': {
        'ENGINE': 'django.db.backends.mysql',
    }
}

STATIC_ROOT = "/path/to/static/files"

CORS_ALLOWED_ORIGINS = [
    "https://url.where.visualisation.site.is.org",
]

````


install python libraries (depending on which database backend is used, you might install more packages accordingly):

```
pip install numpy django djangorestframework django-cors-headers pabutools
```


setup the database:

```
python manage.py makemigrations
python manage.py migrate
python manage.py migrate --database user_submitted
python manage.py initialize_db 
python manage.py initialize_db --database user_submitted
```

populate the database with precomputed example data (adding elections will take some time):

```
python manage.py add_election -d pabulib_samples/ -v 3
python manage.py import_election_properties -i pabulib_samples/Res_Election_InstanceProperties.csv -p pabulib_samples/Res_Election_ProfileProperties.csv
python manage.py import_rule_results pabulib_samples/Res_RuleResults.csv
python manage.py import_rule_result_properties pabulib_samples/Res_RuleResult_Properties.csv
```

or populate it with your own .pb files and compute the properties:

```
python manage.py add_election -d <path to .pb file directory> -v 3
python manage.py compute_election_properties -v 3
python manage.py compute_rule_results -v 3
python manage.py compute_rule_result_properties -v 3
```
