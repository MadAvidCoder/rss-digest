# RSS Digest
![Hackatime](https://hackatime-badge.hackclub.com/U081TBVQLCX/rss-digest)
![License](https://img.shields.io/github/license/madavidcoder/rss-digest)
![Created At](https://img.shields.io/github/created-at/madavidcoder/rss-digest)
![Top Language](https://img.shields.io/github/languages/top/madavidcoder/rss-digest)
![Commits](https://img.shields.io/github/commit-activity/t/madavidcoder/rss-digest)
![Last Commit](https://img.shields.io/github/last-commit/madavidcoder/rss-digest)
![Website Status](https://img.shields.io/website?url=https%3A%2F%2Frss.madavidcoder.hackclub.app)

**RSS Digest is an RSS aggregator that composes a daily HTML digest of new articles from selected RSS feeds. View the archive [here](https://rss.madavidcoder.hackclub.app)!**

## Usage
RSS Digest will automatically create and send out a digest at 8:00AM each day. You can view an archive of past digests at [https://rss.madavidcoder.hackclub.app](https://rss.madavidcoder.hackclub.app). If you wish to join (or leave) the digest mailing list, and you're part of HackClub, please [DM me](https://hackclub.slack.com/team/U081TBVQLCX). Configuration of included feeds and email recipients is done via the Admin Dashboard ([https://rss.madavidcoder.hackclub.app/admin](https://rss.madavidcoder.hackclub.app/admin)) on the web app, which requires an admin password to use. 

## Tech Stack
- **Core:** Modular Python 3 App
- **Web Dashboard:** Flask
- **Email Formatting:** Jinja2
- **Web Server:** Gunicorn
- **Database:** PostgreSQL
- **Mailing:** SMTP via smptlib
- **RSS Processer:** feedparser
- **Hosting:** [HackClub Nest](https://hackclub.app)

## Setup
In order to use RSS Digest yourself, first clone the repo, and install dependencies: 
```bash
git clone https://github.com/madavidcoder/rss-digest.git

cd rss-digest
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
You will also need to create a PostgreSQL database and a `.env` file within `/rss-digest`, containing all the variables listed below.

To create and send a digest once, run `python3 main.py` (having activated the virtual environment).
If you want to get daily digests, I advise setting up a cron job to automate running this.

In order to access the web dashboard, run `python3 web.py` (again, ensure you've activated the virtual environment), and go to `localhost:42329` or `localhost:42329/admin`. If you wish to use this more often, I would recommend that you switch to a production server (e.g. gunicorn) and use a systemd job to keep it running.

## Environment Variables
Create a `.env` file containing all these variables, with the values set to suit your application.
```dotenv
DB_URL=postgresql://<YOUR-DATABASE-URL>

EMAIL_FROM=<EMAIL TO SEND FROM>
EMAIL_PASSWORD=<SMTP PASSWORD>
EMAIL_TO=<DEFAULT RECIPIENT EMAIL>

SMTP_SERVER=<SMTP SERVER TO SEND FROM>
SMTP_PORT=<SMTP SERVER PORT NUMBER>
SMTP_USERNAME=<YOUR SMTP USERNAME>

FROM_NAME='Your Daily RSS Digest'
SUBJECT_PREFIX=[RSS]

FEED_URLS=https://hackaday.com/blog/feed/,https://www.livescience.com/feeds.xml,https://www.nasa.gov/news-release/feed/

DEBUG=false
SEND_INDIVIDUALLY=true

DRY_RUN=false
SKIP_SMTP_AUTH=false

MAX_ENTRIES_PER_FEED=15
MAX_ITEMS=50

ADMIN_PASSWORD=<ADMIN DASHBOARD PASSWORD>
```

## License
RSS Digest is licensed under the [MIT License](https://github.com/MadAvidCoder/rss-digest/blob/main/LICENSE). You are free to use, copy, modify, and/or publish this project, or any part thereof, for commercial or non-commercial purposes. Attribution is appreciated, but not required.
