## Slack Purge

**Fork of:** [https://github.com/martinmaskell/slack-message-deleter](https://github.com/martinmaskell/slack-message-deleter)

### Required Variables

To get the required variables you need to sign in to the Slack browser client: 
[https://app.slack.com/client/T3ZEVSZHT](https://app.slack.com/client/T3ZEVSZHT).


``USER`` 

Found by inspecting your username's element

You will see a ``href`` attribute with a URL similar to this: 
``href="/team/A1B2C3D4"`` - it is the second half of this URL 
("A1B2C3D4" in this example) that is the value you need.

``TOKEN``

Found by inspecting the Network tab of the Dev Tools.

Click on the request starting with "conversations.mark",
and on the 'headers' tab, scroll until you see "Form Data".
You will see something similar to this:
``token: abcd-1234567890-0987654321-1234567890-098abcdefghijklmnop3212345``.
It is the value (starting with "abcd" in this example) that you need.

``COOKIE``

In the same request data window described above, in the 'Request Headers'
section, you should see something similar to this:
``cookie: b=.123abc123acb123abc123acb; _ga=GA1.1.123abc123acb123abc123acb; _fbp=fb.1.123456...``.
This will be a very long value - and it's the entire gigantic string you need.

``CHANNEL``

Found within the browser URL bar.

Click on the channel you want to target, and you should see something similar to this in the URL bar:
``https://app.slack.com/client/A1B2C3D4/D1C2B3A4``. It is the last ID ("D1C2B3A4" in this example) 
that you need.


### Running

Open a command window, and navigate to the folder that the script is located in
(probably the same directory that this readme file is in).

Run: ``python slack-message-deleter.py``

