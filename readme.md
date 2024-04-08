# SSL Checker
This Python script can be used to check the expiry date of website certificates and to send Slack messages based on an expiry interval.

## Getting started
### Installing packages and venv setup
Install the required packages
```
apt install build-essential libssl-dev libffi-dev
apt install python3-dev python3-venv python3-pip python3-setuptools
```

Clone the repository, create the python environment and install required pip packages
```
git clone
cd ./ssl-checker
python3 -m venv sslenv
source sslenv/bin/activate
pip install -r requirements.txt
deactivate
```

### Environment variables and tokens
Create in the root folder a file called `.env` with the below contents, or set them as environment variables
```
LOG_TYPE=INFO
LOG_FILE=ssl-check.log
INTERVAL=30
CHANNEL_ID=C0XXXXXX
SLACK_BOT_TOKEN=test_token
CONFLUENCE_PAGE=https://atlassian.net/some-page
```
*LOG_TYPE* can be one of: `ERROR`, `WARNING`, `INFO`, `DEBUG`
*INTERVAL* in days
*CHANNEL_ID* bot needs to be added to private channels
*SLACK_BOT_TOKEN* Slack OAuth token

## Usage
```
# Run the script
./ssl-checker/sslenv/bin/python3 ./ssl-check/main.py
# or
source ./ssl-checker/sslenv/bin/activate
python3 ./ssl-check/main.py

# Arguments
.main.py -h         # Show help
.main.py -v         # Show console output
.main.py --verbose  # Show console output

```
