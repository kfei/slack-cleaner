# -*- coding: utf-8 -*-

import argparse


class Args():
    def __init__(self):
        p = argparse.ArgumentParser(prog='slack-cleaner')

        # Token
        p.add_argument('--token', required=True,
                       help='Slack API token (https://api.slack.com/web)')

        # Rate limit
        p.add_argument('--rate', type=int,
                       help='Delay between API calls (in seconds)')

        # Type
        g_type = p.add_mutually_exclusive_group(required=True)
        g_type.add_argument('--message', action='store_true',
                            help='Delete messages')
        g_type.add_argument('--file', action='store_true',
                            help='Delete files')

        # Channel, DM or group
        g_chan = p.add_mutually_exclusive_group(required=True)
        g_chan.add_argument('--channel',
                            help='Channel name\'s, e.g., general')
        g_chan.add_argument('--direct',
                            help='Direct message\'s name, e.g., sherry')
        g_chan.add_argument('--group',
                            help='Private group\'s name')

        # Conditions
        p.add_argument('--user',
                       help='Delete messages from certain user')
        p.add_argument('--bot', action='store_true',
                       help='Delete messages from bots')
        p.add_argument('--after',
                       help='Delete messages newer than this time (YYYYMMDD)')
        p.add_argument('--before',
                       help='Delete messages older than this time (YYYYMMDD)')

        # Perform or not
        p.add_argument('--perform', action='store_true',
                       help='Perform the task')

        args = p.parse_args()

        self.token = args.token

        self.rate_limit = args.rate

        self.delete_message = args.message
        self.delete_file = args.file

        self.channel_name = args.channel
        self.direct_name = args.direct
        self.group_name = args.group

        self.user_name = args.user
        self.bot = args.bot
        self.start_time = args.after
        self.end_time = args.before

        self.perform = args.perform
