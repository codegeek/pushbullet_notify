# -*- coding: utf-8 -*-
# Author: Guillermo Castro <github AT codegeek DOT info>
# IRC: CodeGeek AT freenode
#
# This plugin sends push notifications to pushbullet when somebody says your nickname, etc.
# Requires Weechat 0.3.5

#   Copyright [2020] [Guillermo Castro]
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

# script variables
SCRIPT_NAME = "pushbullet_notify"
SCRIPT_AUTHOR = "Guillermo Castro <github AT codegeek DOT info>"
SCRIPT_VERSION = "0.1"
SCRIPT_LICENSE = "Apache2.0"
SCRIPT_DESCRIPTION = "Weechat push notification to Pushbullet"
PUSHBULLET_URL = "https://api.pushbullet.com/v2/pushes"

# Validate we are running inside of weechat
import_ok = True
try:
    import weechat
except ImportError:
    print("This script must run under WeeChat.")
    import_ok = False
try:
    import requests
except ImportError as message:
    print("Missing package(s) for %s: %s" % (SCRIPT_NAME, message))
    import_ok = False

# script settings
settings = {
    "pushbullet_token" : (
        "",
        "Pushbullet access token (required)"),
    "send_highlights" : (
        "on", 
        "send highlighted messages"),
    "send_priv_msg" : (
        "on"
        "send private messages"),
    "nick_separator" : (
        ": ",
        "separator to use for messages"),
    "ignore_nicks" : (
        "*status",
        "Nicks to ignore private message from (comma separated)")
}

def message_cb(data, buffer, date, tags, displayed, highlight, prefix, message):
    sendstatus = None
    # Only send notification when away.
    if weechat.buffer_get_string(buffer, 'localvar_away'):
        token = weechat.config_get_plugin('pushbullet_token')
        if (weechat.buffer_get_string(buffer, "localvar_type") == "private" and weechat.config_get_plugin('send_priv_msg') == "on"):
            ignorenicks = weechat.config_get_plugin('ignore_nicks')
            if ignorenicks and is_nick_in_list(ignorenicks, prefix):
                pass
            else:
                # title: Private message from <localvar_server>@<prefix>
                # body: <message>
                title = "Private message from %s@%s" % (weechat.buffer_get_string(buffer, "localvar_server"), prefix)
                sendstatus = send_notification(token, title, message)
        elif (int(highlight) and weechat.buffer_get_string(buffer, "localvar_type") == "channel" and weechat.config_get_plugin('send_highlights') == "on"):
            # title: Message from <localvar_server>@<localvar_channel>
            # body: <prefix>: <message>
            title = "Message from %s@%s" % (weechat.buffer_get_string(buffer, "localvar_server"), weechat.buffer_get_string(buffer, "localvar_channel"))
            body = prefix + weechat.config_get_plugin('nick_separator') + message
            sendstatus = send_notification(token, title, body)
    # Print status to buffer if push failed
    if sendstatus:
        weechat.prnt("", sendstatus)
    return weechat.WEECHAT_RC_OK

def send_notification(token, title, body):
    status = None
    if token:
        response = requests.post(PUSHBULLET_URL, headers = {
            "Access-Token": token
        }, json={
            "type": "note",
            "title": title,
            "body": body
        })
        if not response:
            status = "Invalid response: {0}".format(response.reason)
    else:
        status = "Pushbullet token hasn't been set. Message ignored."
    return status

def is_nick_in_list(list, nick):
    for i in range(len(list)):
        if list[i] == nick:
            return True
    return False

def script_main():
    if not weechat.register(SCRIPT_NAME, SCRIPT_AUTHOR, SCRIPT_VERSION, SCRIPT_LICENSE, SCRIPT_DESCRIPTION, "", ""):
        return
    version = weechat.info_get('version_number', '') or 0
    for option, value in settings.items():
        if not weechat.config_is_set_plugin(option):
            weechat.config_set_plugin(option, value[0])
        if int(version) >= 0x00030500:
            weechat.config_set_desc_plugin(
                option, '%s (default: "%s")' % (value[1], value[0]))
    weechat.hook_print("", "irc_privmsg", "", 1, "message_cb", "")

if __name__ == "__main__" and import_ok:
    script_main()
    weechat.prnt("", "Script %s loaded. Make sure config option 'pushbullet_token' is set." % SCRIPT_NAME)