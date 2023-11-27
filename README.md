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


```
pip install numpy django djangorestframework django-cors-headers pabutools

python manage.py makemigrations
python manage.py migrate
python manage.py migrate --database user_submitted
python manage.py initialize_db 
python manage.py initialize_db --database user_submitted
python manage.py add_election -d <path to .pb file directory> -v 3
python manage.py compute_election_properties -v 3
python manage.py compute_rule_results -v 3
python manage.py compute_rule_result_properties -v 3
```
