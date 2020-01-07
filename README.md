# slack-message-deleter
Automatically Delete Slack messages in all Channels, Groups and DMs

Just a simple script to delete your messages in Slack.

You need to change a few constants in the file which you can get from the Slack workspace when you login via a browser.

Simply use the Dev Tools in Chrome to inspect the network traffic for any XHR request which uses the Slack API.  e.g. conversations.history.

Look in the Headers tab and you'll find these constant values :

TOKEN - This is in the Form Data section

COOKIE - This is found in the Request Headers section

The last value you'll need is to set the USER constant, which you can find if you go to your profile page and copy the string from the last part of the URL.

e.g. https://app.slack.com/client/XXXXXXXXX/YYYYYYYY/user_profile/[YOUR USER STRING HERE]
