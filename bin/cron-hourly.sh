#!/usr/bin/env bash

# Look up the recently published videos, and create issues in the github repo.

# A script to run as a scheduled CRON task, every hour at the seventh minute
# 07 * * * * web bin/cron-hourly.sh > /dev/null 2> /dev/null

today="$(date +'%A %d %B %Y')"
title="JLM Captions Github Bot"
email="antoine.goutenoir@gmail.com"

export PYTHONIOENCODING="utf8"

source venv/bin/activate

python bin/create-issues.py |& tee create-issues.log

if [ ${PIPESTATUS[0]} -ne 0 ] ; then
  cat create-issues.log | mail -s "${title} Create Issue Failure" ${email}
  exit 1
fi
