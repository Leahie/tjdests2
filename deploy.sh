echo "Starting deploy"
dos2unix deploy.sh
dos2unix manage.py
echo "Converting line endings"
cd /mnt/c/Users/leahz/OneDrive/Desktop/Quizlet/ATC4/tjdests
git pull
echo "Pulled latest changes"
pip install --user pipenv
echo "Installed pipenv"
TMPDIR=/site/tmp pipenv sync
echo "Synced dependencies"
pipenv run ./manage.py migrate
pipenv run ./manage.py collectstatic --no-input
echo "Deploy complete. Restart the site process to wrap up."
