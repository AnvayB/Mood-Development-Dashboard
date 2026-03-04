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

log:
	curl -X POST https://mood-development-dashboard-production.up.railway.app/webhook/sms \
  -d "Body=$(filter-out log,$(MAKECMDGOALS))" \
  -d "From=+14081234567"

# Catch-all so the message isn't treated as a missing target
%:
	@:
