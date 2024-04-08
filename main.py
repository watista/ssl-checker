#!bin/python3

#   This file is owned by Saysimple B.V.
#   Author: Wouter Paas <wouter@saysimple.com>
#   Date 21-11-2022
#   Some more text...

import os
import json
import time
import datetime
import argparse
import logging
from dotenv import load_dotenv
from dateutil.parser import parse
from urllib.request import ssl, socket
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def setLogging(consoleLogging=False):

    # Set logging format and config
    logging.root.handlers = []
    if os.getenv("LOG_TYPE") == "DEBUG":
        fmt = "%(levelname)s:%(name)s:%(asctime)s - %(message)s - {%(pathname)s:%(lineno)d}"
    else:
        fmt = "%(levelname)s:%(name)s:%(asctime)s - %(message)s"
    logging.basicConfig(filename=os.getenv("LOG_FILE"), level=logging.os.getenv("LOG_TYPE"), format=fmt, datefmt='%d-%m-%Y %H:%M:%S')

    # Set console logging
    if consoleLogging:
        console = logging.StreamHandler()
        console.setLevel(logging.os.getenv("LOG_TYPE"))
        console.setFormatter(logging.Formatter(fmt))
        logging.getLogger("").addHandler(console)


def sendLogMessage(dtype, msg):

    # Log according to type
    if dtype == "error":
        logging.error(msg)
    elif dtype == "warning":
        logging.warning(msg)
    elif dtype == "info":
        logging.info(msg)
    else:
        logging.debug(msg)


def sendSlackMessage(client, msg, mlist=False, mtype=False):

    # Create the block message depending on expiry or error message
    if mlist and mtype == "expire":
        block=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":bell: *Website certificates to expire* :bell:\n\nGoodmorning, here is a list of the certificates which are going to expire within {os.getenv('INTERVAL')} days."
                }
            },
            {
                "type": "divider"
            }
        ]

        for i in range(len(mlist)):
            block.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<https://{mlist[i][0]}|{mlist[i][0]}>*\nGoing to expire in *{mlist[i][1]}* days!"
                }
            })

        block.append(
            {
                "type": "divider"
            })

        block.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"See the following Confluence page for a detailed overview for all certificates\n*<{os.getenv('CONFLUENCE_PAGE')}|Confluence | SSL Certificaten>* "
                }
            })

    elif mlist and mtype == "error":
        block=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":x: *Website certificates errors* :x:\n\nGoodmorning, here is a list of the certificates for which errors occurred."
                }
            },
            {
                "type": "divider"
            }
        ]

        for i in range(len(mlist)):
            block.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*<https://{mlist[i][0]}|{mlist[i][0]}>*\nError: *{mlist[i][1]}*"
                }
            })

            # Log the exception
            sendLogMessage("error", f"{mlist[i][0]} - {mlist[i][1]}")

    else:
        block=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": msg
                }
            }
        ]

    # Send the message to the channel
    try:
        response = client.chat_postMessage(
            channel=os.getenv("CHANNEL_ID"),
            blocks=block,
            text=msg
        )

    # Catch Slack error and log it
    except SlackApiError as e:
        sendLogMessage("error", e.response["error"])


if __name__ == '__main__':

    # Parse arguments and console logging if enabled
    parser = argparse.ArgumentParser(description='SSL Check script')
    parser.add_argument('--verbose', action='store_true', help='Enable console logging')
    parser.add_argument('-v', action='store_true', help='Enable console logging')
    args = parser.parse_args()
    console = args.v or args.verbose

    # Init
    load_dotenv()
    client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
    setLogging(console)

    expiry_list = []
    error_list = []

    # Loop through normal sites from the file sites.json
    for hostname in json.load(open('sites.json','r'))["sites"]:

        # Create the SSL connection to read the certificate info
        context = ssl.create_default_context()

        # Catch SSL handshake/timeout errors
        try:
            with socket.create_connection((hostname, 443)) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as conn:
                    certificate = conn.getpeercert()

                    # Check if required data exists, send message on error
                    if not certificate["notAfter"]:
                        sendSlackMessage(client, f":x: Certificate doesn't contain an expiry date for website: <https://{hostname}|{hostname}> :x:")
                        continue

                    # Get the expiry date and convert it to unix timestamp
                    date = parse(certificate["notAfter"])
                    expiry_ts = time.mktime(datetime.datetime.strptime(str(date.date()), "%Y-%m-%d").timetuple())

                    # Calculate how many days until expiry
                    still_valid = ((((expiry_ts - time.time()) / 60) / 60) / 24)

                    # Add site to array if certificate is going to expire within 30 days
                    if still_valid < int(os.getenv("INTERVAL")):
                        expiry_list.append([hostname, round(still_valid)])

        except Exception as e:
            error_list.append([hostname, e])

    # Loop through special sites from the file sites.json
    with open('sites.json','r') as shostname:
        data = json.load(shostname)
        for i in range(len(data["special"])):
            skey = list(data["special"].keys())[i]
            svalue = list(data["special"].values())[i]

            # Get the expiry date and convert it to unix timestamp
            expiry_ts = time.mktime(datetime.datetime.strptime(svalue, "%d-%m-%Y").timetuple())

            # Calculate how many days until expiry
            still_valid = ((((expiry_ts - time.time()) / 60) / 60) / 24)

            # Add site to array if certificate is going to expire within 30 days
            if still_valid < int(os.getenv("INTERVAL")):
                expiry_list.append([skey, round(still_valid)])

    # Send Slack message if any site are going to expire
    if expiry_list:
        sendSlackMessage(client, "Expiry list", expiry_list, "expire")

    # Send Slack message if any errors
    if error_list:
        sendSlackMessage(client, "Error list", error_list, "error")

