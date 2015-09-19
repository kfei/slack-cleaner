# -*- coding: utf-8 -*-

from datetime import datetime
import logging
import pprint
import sys
import time

from slacker import Slacker

from slack_cleaner.utils import Colors, Counter, TimeRange
from slack_cleaner.args import Args


# Get and parse command line arguments
args = Args()
time_range = TimeRange(args.start_time, args.end_time)

# Nice slack API wrapper
slack = Slacker(args.token)

# So we can print slack's object beautifully
pp = pprint.PrettyPrinter(indent=4)

# Count how many items we deleted
counter = Counter()

# Initial logger
logger = logging.getLogger('slack-cleaner')
logger.setLevel(10)

# Log deleted messages/files if we're gonna actually perform the task
if args.perform:
    ts = datetime.now().strftime('%Y%m%d-%H%M%S')
    file_log_handler = logging.FileHandler('slack-cleaner.' + ts + '.log')
    logger.addHandler(file_log_handler)

# And always display on console
stderr_log_handler = logging.StreamHandler()
logger.addHandler(stderr_log_handler)


def get_id_by_name(list_dict, key_name):
    for d in list_dict:
        if d['name'] == key_name:
            return d['id']


def clean_channel(channel_id, time_range, user_id=None, bot=False):
    # Setup time range for query
    oldest = time_range.start_ts
    latest = time_range.end_ts

    _api_end_point = None
    # Set to the right API end point
    if args.channel_name:
        _api_end_point = slack.channels.history
    elif args.direct_name:
        _api_end_point = slack.im.history
    elif args.group_name:
        _api_end_point = slack.groups.history

    has_more = True
    while has_more:
        res = _api_end_point(channel_id, latest, oldest).body
        if not res['ok']:
            logger.error('Error occurred on Slack\'s API:')
            pp.pprint(res)
            sys.exit(1)

        messages = res['messages']
        has_more = res['has_more']

        if len(messages) == 0:
            print 'No more messsages'
            break

        for m in messages:
            # Prepare for next page query
            latest = m['ts']

            # Delete user messages
            if m['type'] == 'message':
                # Delete user messages
                if m.get('user'):
                    # No matter whos message, just delete
                    if user_id is None:
                        delete_message_on_channel(channel_id, m)
                    # Delete message belong to certain user
                    elif m.get('user') == user_id:
                        delete_message_on_channel(channel_id, m)

                # Delete bot messages
                if bot and m.get('subtype') == 'bot_message':
                    delete_message_on_channel(channel_id, m)

            # Exceptions
            else:
                print 'Wierd message'
                pp.pprint(m)

        if args.rate_limit:
            time.sleep(args.rate_limit)


def delete_message_on_channel(channel_id, message):
    # Actually perform task
    if args.perform:
        try:
            # No response is good response
            # FIXME: Why this behaviour differ from Slack's documantation?
            slack.chat.delete(channel_id, message['ts'])
        except:
            logger.error(Colors.YELLOW + 'Failed to delete ->' + Colors.ENDC)
            pp.pprint(message)
            return

        logger.warning(Colors.RED + 'Deleted message -> ' + Colors.ENDC
                       + (message.get('user') or '_')
                       + ' : '
                       + message['text'])

        if args.rate_limit:
            time.sleep(args.rate_limit)

    # Just simulate the task
    else:
        logger.warning(Colors.YELLOW + 'Will delete message -> ' + Colors.ENDC
                       + (message.get('user') or '_')
                       + ' : '
                       + message['text'])

    counter.increase()


def get_user_id_by_name(name):
    res = slack.users.list().body
    if not res['ok']:
        return
    members = res['members']
    if len(members) > 0:
        return get_id_by_name(members, name)


def get_channel_id_by_name(name):
    res = slack.channels.list().body
    if not res['ok']:
        return
    channels = res['channels']
    if len(channels) > 0:
        return get_id_by_name(channels, name)


def get_direct_id_by_name(name):
    res = slack.im.list().body
    if not res['ok']:
        return
    ims = res['ims']
    if len(ims) > 0:
        _user_id = get_user_id_by_name(name)
        for i in ims:
            if i['user'] == _user_id:
                return i['id']


def get_group_id_by_name(name):
    res = slack.groups.list().body
    if not res['ok']:
        return
    groups = res['groups']
    if len(groups) > 0:
        return get_id_by_name(groups, name)


def message_cleaner():
    _channel_id = None
    _user_id = None

    # If channel's name is supplied
    if args.channel_name:
        _channel_id = get_channel_id_by_name(args.channel_name)

    # If DM's name is supplied
    if args.direct_name:
        _channel_id = get_direct_id_by_name(args.direct_name)

    # If channel's name is supplied
    if args.group_name:
        _channel_id = get_group_id_by_name(args.group_name)

    if _channel_id is None:
        sys.exit('Channel, direct message or private group not found')

    # If user's name is also supplied
    if args.user_name:
        _user_id = get_user_id_by_name(args.user_name)
        if _user_id is None:
            sys.exit('User not found')

    # Delete messages on certain channel
    clean_channel(_channel_id, time_range, _user_id, args.bot)


def file_cleaner():
    # TODO
    print 'File deletion is not implemented yet'


def main():
    # Dispatch
    if args.delete_message:
        message_cleaner()
    elif args.delete_file:
        file_cleaner()

    # Compose result string
    result = Colors.GREEN + str(counter.total) + Colors.ENDC
    if args.delete_message:
        result += ' message(s)'
    elif args.delete_file:
        result += ' file(s)'

    if not args.perform:
        result += ' will be cleaned.'
    else:
        result += ' cleaned.'

    # Print result
    logger.info('\n' + result + '\n')

    if not args.perform:
        logger.info('Now you can re-run this program with `--perform`'
                    + ' to actually perform the task.' + '\n')


if __name__ == '__main__':
    main()
