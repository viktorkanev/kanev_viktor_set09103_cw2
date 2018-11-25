# newsroom
A full-featured blog-like web-app

## Prerequisites
You need Python v3.0 or above installed on your client machine as well as any additional modules.
To install all required modules:
```bash
pip3 install -r requirements.txt
```

## Running The Application
To start the application

First navigate to the project folder
```bash
$ cd 'project folder'
```

```bash
$ FLASK_APP=app.py
$ FLASK_ENV=environment  
```

Then

```bash
$ python -m flask run --host=0.0.0.0 --port 'assigned port'
```

or if running on local machine:

```bash
$ python run.py
```

Usually the assigned port is 5000
Your application should run on port 5000 , so in your browser just go to [http://127.0.0.1:5000](http://127.0.0.1:5000)