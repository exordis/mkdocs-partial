# Develop

## Virtual Environment

### Mac
```
python3 -m pip install --upgrade pip
python3 -m pip install virtualenv
python3 -m venv env
source env/bin/activate
python -m pip install -e .
python -m pip install -e '.[lint]'
python -m pip install -e '.[test]'
deactivate
```

# Run linter
```
python -m isort .
python -m flake8 .
black .
pylint --jobs 0 . --recursive y .
```

# Run tests
### Run/Debug tests in Pycharm
```
1) Set environment variables in Configurations by list from main.py 
2) Remove line "addopts = --cov=synchronizer/ --cov-report=term-missing" in setup.cfg because of "--cov" debug breakpoints not working for local pytest runs
```

## Docker Container

### Create dotenv file
with name Makefile.env
```
GITLAB_API_TOKEN=<token value>
ARGOCD_PROD_SECRET=<token value>
ARGOCD_UAT_SECRET=<token value>
ARGOCD_QA_SECRET=<token value>
```
### start container
start python docker container
```
docker run --rm -it -v ${PWD}:/wrk -w /wrk python:3.11-alpine /bin/sh
```
### dependencies
run inside running container to install all required dependencies
```
/wrk # ./prepare.sh
```
### commands
run inside running container 
to install dependencies
```
make install
```
to run linters
```
make lint
```

to run tests
```
make test
```

to run compliance for notifications
```
make compliance subsystem=notifications repository=service-notifications-api
```