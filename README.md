# addvideotoyoutubeplaylist
Lambda function to parse a Slack channel for youtube links, then add them to a youtube playlist


This uses AWS Lambda with a Python 2.7 runtime. Because it's not an actual slash command, and Slack itself doesn't need to post to the channel, it doesn't require the use of API Gateway.

I use this with a CloudWatch Alarm Action to run it every hour, on the hour. It'll scrape the last hour of posts in my Slack's #music channel and add any youtube links to the playlist.

Don't forget to replace CLIENT_ID_HERE PLAYLIST_ID etc with your own.
