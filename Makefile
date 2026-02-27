check:
	git status
	git branch

start:
	streamlit run app.py

add:
	git status
	git add .
	git status
	git config user.name "AnvayB"
	git config user.email "anvay.bhanap@gmail.com"

# git commit -m "message"


push:
	git push origin main

main:
	git checkout main
	git branch
	git pull

user-reset:
	git config user.name "AnvayB"
	git config user.email "anvay.bhanap@gmail.com"

user-check:
	git config user.name
	git config user.email

test:
	curl -X POST https://mood-development-dashboard-production.up.railway.app/webhook/sms \
  -d "Body=had a really productive day" \
  -d "From=+14081234567"
