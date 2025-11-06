# RSS Digest
![Hackatime](https://hackatime-badge.hackclub.com/U081TBVQLCX/rss-digest)
![License](https://img.shields.io/github/license/madavidcoder/rss-digest)
![Created At](https://img.shields.io/github/created-at/madavidcoder/rss-digest)
![Top Language](https://img.shields.io/github/languages/top/madavidcoder/rss-digest)
![Commits](https://img.shields.io/github/commit-activity/t/madavidcoder/rss-digest)
![Last Commit](https://img.shields.io/github/last-commit/madavidcoder/rss-digest)
![Website Status](https://img.shields.io/website?url=https%3A%2F%2Frss.madavidcoder.hackclub.app)
---
**RSS Digest is an RSS aggregator that composes a daily HTML digest of new articles from selected RSS feeds.**

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

## License
RSS Digest is licensed under the MIT License. You are free to use, copy, modify, and/or publish this project, or any part thereof, for commercial or non-commercial purposes. Attribution is appreciated, but not required.