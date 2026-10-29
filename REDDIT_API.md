# Reddit Data API usage in this project

This project includes one component that uses the **official Reddit Data
API**: a personal, read-only **topic-discovery** helper for the channel
owner's own video-production research.

- Code: `src/discovery_main.py` (CLI) and `src/modules/reddit_discovery.py`
- Library: [PRAW](https://praw.readthedocs.io/) with an OAuth2 **script**
  app registered to the owner's own Reddit account (u/SellLucky671).

## What it does

Runs once a day on the owner's own Windows PC (Task Scheduler). For each
of ten fixed public subreddits (r/aww, r/NatureIsFuckingLit,
r/nextfuckinglevel, r/AnimalsBeingBros, r/Eyebleach, r/likeus,
r/MadeMeSmile, r/Unexpected, r/HumansBeingBros, r/BeAmazed) it reads the
current hot listing of each (limit set in local config), keeps only
video posts above a score
threshold, and writes a local JSON candidate list: post ID, subreddit,
title, score, comment count, permalink, media URL, timestamp. A seen-ID
file prevents duplicates across days. The owner personally reviews the
list to choose topics for original commentary videos; published videos
credit and link the original Reddit threads.

## What it never does

- No posting, commenting, voting, messaging, following, or any other
  write action on Reddit.
- No querying of user profiles or histories, and no collection of
  personal data. A post's author name is kept only as part of that
  post's public metadata so the original poster can be credited.
- No sale, sharing, publication, or other redistribution of the
  collected data, and no use of the data to train AI models.

## Data handling

- Storage: local JSON files on the owner's PC only.
- Retention: candidate lists are temporary working files, deleted in
  routine cleanup. The seen file stores post IDs only.
- Deletions: every run reads live listings only, so deleted or removed
  posts stop appearing and are never re-fetched.
- Volume: roughly 10–40 read requests per day; PRAW honours Reddit's
  rate-limit headers.
- Identity: the app authenticates as the owner's own account with a
  descriptive User-Agent identifying the tool and its owner (set in
  local config), and credentials live in a local `.env` file that is
  never committed.

## Why not Devvit

Devvit hosts apps that run inside Reddit. This component is a
standalone local script in an off-platform desktop workflow (scheduled
on a home PC, writing local files for other local tools), so the Data
API script-app route is the applicable one.
