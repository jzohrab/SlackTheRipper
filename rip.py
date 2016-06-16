import yaml
from optparse import OptionParser
import sys
import json
import datetime
import slacker
import unicodedata
import requests.packages.urllib3
import re

from slacker import Slacker, Channels

def rip(flags):

    requests.packages.urllib3.disable_warnings()
    
    with open(flags.tokenfile) as f:
        config = yaml.load(f.read())
    private_token = config['token']

    def get_unixtime(s):
        d = datetime.datetime.strptime(s, "%Y-%m-%d")
        return float(d.strftime("%s"))
    
    oldest = get_unixtime(flags.startdate)
    latest = get_unixtime(flags.enddate)
    
    slack = Slacker(private_token)

    response = slack.users.list()
    users = response.body['members']
    udict = {}
    for id, name in [(u['id'], u['name']) for u in users]:
        udict[str(id)] = str(name)
    inv_udict = {v: k for k, v in udict.iteritems()}

    history_provider = slacker.Channels(token = private_token)
    channel_id = history_provider.get_channel_id(flags.channel)

    if channel_id is None:
        history_provider = slacker.IM(token = private_token)
        ims = history_provider.list().body['ims']
        im_dict = {}
        for imid, userid in [(i['id'], i['user']) for i in ims]:
            im_dict[userid] = imid
        channel_id = im_dict[inv_udict[flags.channel]]

    if channel_id is None:
        print 'Don''t know channel {0}.'.format(flags.channel)
        sys.exit(1)

    msgs = []
    _do_rip(slack, history_provider, channel_id, oldest, latest, udict, msgs)

    msgs.reverse()
    return msgs


def _do_rip(slack, ch, ch_id, oldest, latest, udict, msgs = []):

    print 'Fetching messages for {0}, latest = {1}'.format(ch_id, oldest)
    resp = ch.history(channel=ch_id, oldest=oldest, latest=latest)
    add_msgs = resp.body['messages']
    
    def msg_pred(msg):
        if u'subtype' in m:
            if m['subtype'] == 'channel_join':
                return False
        return True

    def clean_msg(msg):

        def normalize(s):
            s = unicodedata.normalize('NFD', s).encode('ascii','ignore')
            userids = re.findall(r'<@(.*?)>', s)
            for uid in userids:
                if '|' in uid:
                    uid = uid.split('|')[0]
                s = s.replace('<@' + uid + '>', '@' + udict[uid])
            return s

        t = ''
        userkey = ''
        ts = str(msg['ts'])
        
        try:
            if u'user' in msg and u'text' in msg:
                t = normalize(msg['text'])
                userkey = msg['user']
                return (udict[userkey], t, ts)

            if u'username' in msg:
                t = normalize(msg['text'])
                return (msg['username'], t, ts)

            if u'attachments' in msg:
                tmp = msg[u'attachments']
                if u'fallback' in tmp[0]:
                    t = normalize(tmp[0]['fallback'])
                elif u'text' in tmp[0]:
                    t = normalize(tmp[0]['text'])
                elif u'pretext' in tmp[0]:
                    t = normalize(tmp[0]['pretext'])

                if t == '':
                    raise ValueError('no message found?')
                return ('BOT', t, ts)

            raise ValueError('logic error')
        except Exception, e:
            print 'Failed at message {0}'.format(msg)
            raise

    add_msgs = map(clean_msg, [m for m in add_msgs if msg_pred(m)])
    msgs.extend(add_msgs)

    oldest_returned_message = float(add_msgs[-1][2])
    
    if resp.body['has_more'] and oldest_returned_message > oldest:
        _do_rip(slack, ch, ch_id, oldest, oldest_returned_message, udict, msgs)

    return msgs


def parse_args(command_line_args):
  """Populate flags from the command-line arguments."""

  today = datetime.date.today()
  enddate = today + datetime.timedelta(days = 1)
  startdate = today + datetime.timedelta(days = -7)
  
  _parser = OptionParser()
  _parser.add_option('-t', '--tokenfile',
                     dest='tokenfile',
                     help='file containing token (structure: token.yml.template)',
                     default='./token.yml')
  _parser.add_option('-c', '--channel',
                     dest='channel',
                     help='channel/DM to rip (e.g., \'general\', \'slackbot\')',
                     default='general')
  _parser.add_option('-s', '--start',
                     dest='startdate',
                     help='Date (yyyy-mm-dd), defaults to 1 week before today',
                     default = str(startdate))
  _parser.add_option('-e', '--end',
                     dest='enddate',
                     help='Date (yyyy-mm-dd), defaults to today',
                     default = str(enddate))
  _parser.add_option('--debug', help='enable debug-level logging', dest='debug')

  flags, unused_args = _parser.parse_args(command_line_args)
  if (len(unused_args) != 0):
      raise ValueError('unused/invalid args? {0}', unused_args)

  return flags


def main(args):
    flags = parse_args(args)
    msgs = rip(flags)
    print '{0} messages'.format(len(msgs))
    for m in msgs:
        print '{0}: {1}'.format(m[0], m[1])


if __name__ == '__main__':
    # Start main program.
    # Pass in command-line args (except for first entry, which is the script name).
    # Note that OptionParser slices sys.argv in this way as well,
    # ref https://docs.python.org/2/library/optparse.html.

    main(sys.argv[1:])    
