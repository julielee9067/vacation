# 근태관리 프로젝트

## 설치

### Python 가상환경 및 패키지

- git 받아오기

  ```bash
  git clone git@git.alluser.net:sogang/isds.git
  ```

- Python 가상환경 설치

  ```bash
  cd isds
  virtualenv -p python3 myenv
  source myenv/bin/activate
  ```

- Python 패키지 설치

  ```bash
  pip install -r requirements.txt
  ```



### 데이터베이스

#### Mysql 사용 시

 mysql이 없을 경우 따로 설치합니다. 접속정보는 `private_settings.py` 에 입력합니다.

**OSX의 경우**

```bash
 brew install mysql
```

#### SQLite 사용 시

`private_settings.py` 에 `DATABASES` 부분을 아래 정보로 입력합니다.

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



### private_settings.py 

`isds/private_settings.py.example` 파일을 `private_settings.py`로 변경 후 데이터베이스 계정 및 스키마 등 접속 정보를 입력합니다. `private_settings.py` 파일은 `settings.py`에서 import 되도록 정의되어 있습니다.

```bash
cd isds
cp private_settings.py.example private_settings.py
```

#### SECRET_KEY 입력

SECRET_KEY는 어떤 값을 입력하셔도 상관 없습니다. 다만 보안 상 예측하기 어려운 값으로 입력하는 것이 좋으며 [Djecrety](https://djecrety.ir/) 사이트에서 자동 생성한 값을 사용하실 수 있습니다.



### migration 실행

```bash
python manage.py migrate
```



## 실행

### migration

```
python manage.py migrate
```

### 서버 실행

```bash
python manage.py runserver
```

## Pre-commit 설치 및 실행 방법
### 설치
```
pip install pre-commit
```
```
pre-commit install
```
### 실행
- 모든 파일에 대해 실행하고 싶은 경우
  ```
  pre-commit run --all-files
  ```
- 이외의 경우 터미널에서 ```git commit``` 을 실행하면 자동으로 파일 체크

  ```
  git commit -m "{COMMIT MESSAGE}"
  # 여기서 파일 체크 및 자동 변환
  
  git add {변경된 파일들}
  
  # 다시 commit 및 반복
  git commit -m "{COMMIT MESSAGE}"
  ```
