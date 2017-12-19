# PluralSight Downloader

Download and watch courses which your subscriptions in offline mode.

### Installation

Install requirements.txt

```sh
$ pip install -r requirements.txt
```

Need to add [geckodriver](https://github.com/mozilla/geckodriver/releases) to PATH for selenium.

### Config

Create config.py

```sh
Username = "yourmail@mail.com" #  your mail or username
Password = "yourpass" # your password
Delay = 7 #  sleep time in each step
TryDownloadTimes = 3 # number of crash downloads for each course
```

Edit course link in run.py

```sh
link = "https://app.pluralsight.com/player?course=xxxx&author=yyyy&name=zzzz&clip=0&mode=live"
```

### Run

```sh
$ python run.py
```

