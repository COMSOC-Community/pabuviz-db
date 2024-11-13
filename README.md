# Pabuviz

[Pabuviz.org](https://pabuviz.org) is a visualization platform for participatory budgeting (PB).
It provides intuitive and visually appealing comparison tools based on real-life data from past PB
elections. It can be used as a helper tool when discussing possible voting rules for PB.

This repository contains the Django project implementing the database used by the website.
It works hand-in-hand with the [pabuviz-web](https://github.com/COMSOC-Community/pabuviz-web) repository,
which contains the React application implementing the website for [pabuviz.org](https://pabuviz.org).

You can access the API by querying [db.pabuviz.org/api](https://db.pabuviz.org/api). The documentation
for the api is available directly at this link.

## Development/Deployment

The database is implemented as a [Django](https://www.djangoproject.com/) project. It acts as an
API that is queried by the website to retrieve the information it needs.

### Getting Started

Whether you are starting local development for pabuviz or you are setting up a server 
to host the database you need to initialise the project by implementing the following steps.

#### Local Settings

Parameterise the local settings by creating a `pb_prototype\local_settings.py` file that looks like this:
```
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret! And update this fake one!
SECRET_KEY = 'secret'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# For production, update with the actual URL host
ALLOWED_HOSTS = [""]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'pabuviz.db'),
    },
    'user_submitted': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'pabuviz_users.db'),
    }
}

STATIC_ROOT = "static/"

CORS_ALLOWED_ORIGINS = [
    "https://url.where.visualisation.site.is.org",
]

````

#### Python Setup

Install python libraries (depending on which database backend is used, you might install more packages accordingly):

```
pip install numpy django djangorestframework django-cors-headers pabutools
```

#### Database Setup

To create the databases, run the following:

```
python manage.py makemigrations
python manage.py migrate
python manage.py migrate --database user_submitted
python manage.py initialize_db 
python manage.py initialize_db --database user_submitted
```

You can then populate the database with precomputed example data (adding elections will take some time):

```
python manage.py add_election -d pabulib_samples/ -v 3
python manage.py import_election_properties -i pabulib_samples/Res_Election_InstanceProperties.csv -p pabulib_samples/Res_Election_ProfileProperties.csv
python manage.py import_rule_results pabulib_samples/Res_RuleResults.csv
python manage.py import_rule_result_properties pabulib_samples/Res_RuleResult_Properties.csv
```

It is also possible to populate it with your own .pb files and compute the properties:

```
python manage.py add_election -d <path to .pb file directory> -v 3
python manage.py compute_election_properties -v 3
python manage.py compute_rule_results -v 3
python manage.py compute_rule_result_properties -v 3
```

### Update the Server

- SSH to the server
- Add your GitHub ssh key to the agent: `ssh-add ~/.ssh/your_key`
- Move to the folder of the Django project: `cd django/pabiviz-db`
- Pull the git: `git pull`
- If static files have been updated:
  - `source ../venv/bin/activate`
  - `python manage.py collectstatic`
- If the database needs updating:
  - `source ../venv/bin/activate`
  - `python manage.py makemigrations`
  - `python manage.py migrate`
- In any case, restart the uwsgi:
  - `cd`
  - `./restart_uwsgi.sh`
- Log out from the server 