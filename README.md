
### Databases

#### When using MySQL

 Use `private_settings.py`

```bash
 brew install mysql
```

#### When using SQLite


```python
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}
```

### migration 

```bash
python manage.py migrate
```

### server run

```bash
python manage.py runserver
```

## Pre-commit
### installation
```
pip install pre-commit
```
```
pre-commit install
```
### run
- If you want to run it against all files
  ```
  pre-commit run --all-files
  ```
- Other cases: ```git commit``` will be automatically executed

  ```
  git commit -m "{COMMIT MESSAGE}"
  
  git add {changed files}
  
  # repeat
  git commit -m "{COMMIT MESSAGE}"
  ```
