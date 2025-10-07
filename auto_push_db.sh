#!/bin/bash
# Auto-commit and push tvguide.db if it has changed
cd /workspaces/tv_project
if git status --porcelain | grep 'tvguide.db'; then
  git add tvguide.db
  git commit -m "Auto-update tvguide.db"
  git push
else
  echo "No changes in tvguide.db to commit."
fi
