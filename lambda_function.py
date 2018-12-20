'''
This function handles a Slack slash command and echoes the details back to the user.

Follow these steps to configure the slash command in Slack:

  1. Navigate to https://<your-team-domain>.slack.com/services/new

  2. Search for and select "Slash Commands".

  3. Enter a name for your command and click "Add Slash Command Integration".

  4. Copy the token string from the integration settings and use it in the next section.

  5. After you complete this blueprint, enter the provided API endpoint URL in the URL field.


Follow these steps to encrypt your Slack token for use in this function:

  1. Create a KMS key - http://docs.aws.amazon.com/kms/latest/developerguide/create-keys.html.

  2. Encrypt the token using the AWS CLI.
     $ aws kms encrypt --key-id alias/<KMS key name> --plaintext "<COMMAND_TOKEN>"

  3. Copy the base-64 encoded, encrypted key (CiphertextBlob) to the kmsEncyptedToken variable.

  4. Give your function's role permission for the kms:Decrypt action.
     Example:
       {
         "Version": "2012-10-17",
         "Statement": [
           {
             "Effect": "Allow",
             "Action": [
               "kms:Decrypt"
             ],
             "Resource": [
               "<your KMS key ARN>"
             ]
           }
         ]
       }

Follow these steps to complete the configuration of your command API endpoint

  1. When completing the blueprint configuration select "POST" for method and
     "Open" for security on the Endpoint Configuration page.

  2. After completing the function creation, open the newly created API in the
     API Gateway console.

  3. Add a mapping template for the application/x-www-form-urlencoded content type with the
     following body: { "body": $input.json("$") }

  4. Deploy the API to the prod stage.

  5. Update the URL for your Slack slash command with the invocation URL for the
     created API resource in the prod stage.
'''


import boto3
from base64 import b64decode
from urlparse import parse_qs
import logging
import json
import urllib
import urllib2
import time

expected_token = "REDACTED"
#input expected token here

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def grab_latest_messages():
    print("Grabbing last hour of messages...")
    latest = time.time()
    oldest = latest - 3600
    latest = str(latest)
    oldest = str(oldest)
    history = urllib2.urlopen("https://slack.com/api/channels.history?token=REDACTED&channel=CHANNEL_ID_FOR_SLACK_CHANNEL&pretty=1&latest=" + latest + "&oldest=" + oldest)
    history_parsed = json.load(history)
    messages = history_parsed["messages"]
    while history_parsed["has_more"] == True:
        latest = messages[-1]["ts"]
        history = urllib2.urlopen("https://slack.com/api/channels.history?token=REDACTED&channel=CHANNEL_ID_FOR_SLACK_CHANNEL&pretty=1&latest=" + latest + "&oldest=" + oldest)
        history_parsed = json.load(history)
        messages.append(history_parsed["messages"][0])
    return messages

def find_youtube_links(messages):
    links = []
    default = "N/A"
    print("Finding youtube links in messages...")
    for message in messages:
        if "attachments" in message and message["attachments"][0].get("service_name",default) == "YouTube":
            links.append(message["attachments"][0]["from_url"])
    return links

def strip_ids_from_links(links):
    ids = []
    print("Removing video ids from links...")
    video_identifier = "v="
    shortened_url_identifier = ".be/"
    for link in links:
        id_position = link.find(video_identifier) + 2
        if id_position == 1:
            id_position = link.find(shortened_url_identifier) + 4
        and_position = link.find("&")
        q_position = link.find("?", id_position)
        if q_position == -1 and and_position == -1:
            ids.append(link[id_position:])
        elif and_position != -1 or and_position < q_position:
            ids.append(link[id_position:and_position])
        elif q_position != -1 or q_position < and_position:
            ids.append(link[id_position:q_position])
    return ids

def add_videos_to_playlist(videos):
    access_token = get_access_token()
    print("Adding videos to playlists...")
    for video in videos:
        req = urllib2.Request('https://www.googleapis.com/youtube/v3/playlistItems?part=snippet')
        req.add_header('Content-Type', 'application/json')
        req.add_header('Authorization', 'Bearer ' + access_token)
        data = { "snippet": {
                             "playlistId": "PLAYLIST_ID_HERE",
                             "resourceId":  {
                                             "videoId": video,
                                             "kind": "youtube#video"
                                            }
                            }
                }
        try:
            response = urllib2.urlopen(req, json.dumps(data))
        except urllib2.HTTPError as err:
            print(err.code)

def get_access_token():
    print("Getting access token...")
    url = "https://accounts.google.com/o/oauth2/token"
    values = {"client_id" : "CLIENT_ID_HERE",
                "client_secret" : "CLIENT_SECRET_HERE",
                "refresh_token" : "REFRESH_TOKEN_HERE",
                "grant_type" : "refresh_token" }
    data = urllib.urlencode(values)
    req = urllib2.Request(url)
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    response = urllib2.urlopen(req, data)
    output = response.read()
    outputjs = json.loads(output)
    return outputjs["access_token"]

def lambda_handler(event, context):
    print("Beginning script...")
    messages = grab_latest_messages()
    links = find_youtube_links(messages)
    videos = strip_ids_from_links(links)
    add_videos_to_playlist(videos)
