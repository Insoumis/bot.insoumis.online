#!/usr/bin/env bash

# Back up the captions, commit them to git and push to github.
# Don't run this if you don't know what you are doing.
# Look at backup.sh or youtube.py instead.

# A script to run as a scheduled CRON task, every day at 23:50
# 50 23 * * * web bin/cron-daily.sh > /dev/null 2> /dev/null

today="$(date +'%A %d %B %Y')"
title="JLM Captions Backup"
email="antoine.goutenoir@gmail.com"

export PYTHONIOENCODING="utf8"

source venv/bin/activate

# The following git clone requires this in your .ssh/config
# This allows us non-interactive authentication with github
# Host insoumis.github.com
#   HostName github.com
#   User git
#   IdentityFile ~/.ssh/RobotInsoumis/id_rsa

rm -Rf jlm-video-subtitles/
git clone git@insoumis.github.com:jlm2017/jlm-video-subtitles.git
cd jlm-video-subtitles
git config user.name RobotInsoumis
git config user.email robot.insoumis@gmail.com
cd ..

python bin/youtube.py --action download \
                      --directory ../jlm-video-subtitles/subtitles \
                      |& tee download.log

if [ ${PIPESTATUS[0]} -ne 0 ] ; then
  cat download.log | mail -s "${title} Download Failure" ${email}
  exit 1
fi

cd jlm-video-subtitles

git add subtitles

git commit -m "Sauvegarde du ${today}."

git push origin master |& tee ../git-push.log

if [ ${PIPESTATUS[0]} -ne 0 ] ; then
  cat ../git-push.log | mail -s "${title} Push Failure" ${email}
  exit 1
fi