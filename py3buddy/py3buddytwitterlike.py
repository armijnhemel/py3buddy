#!/usr/bin/env python3

# Demo program to show how to use the py3buddy module with Twitter
# DBus version
#
# Uses python3-twitter (package name on Fedora) from:
# https://github.com/bear/python-twitter
#
# Copyright 2017-2019 - Armijn Hemel for Tjaldur Software Governance Solutions
# SPDX-Identifier: MIT

import sys
import os
import argparse
import configparser
import time
import calendar
import pydbus
import twitter


def main(argv):
    parser = argparse.ArgumentParser()

    # options for the commandline
    parser.add_argument("-c", "--config", action="store", dest="cfg",
                        help="path to configuration file", metavar="FILE")
    parser.add_argument("-k", "--key", action="store", dest="key",
                        help="consumer key", metavar="KEY")
    parser.add_argument("-s", "--secret", action="store", dest="secret",
                        help="consumer secret", metavar="SECRET")
    parser.add_argument("-t", "--token", action="store", dest="token",
                        help="access token", metavar="KEY")
    parser.add_argument("-a", "--accesssecret", action="store", dest="accesssecret",
                        help="access secret", metavar="SECRET")
    args = parser.parse_args()

    # first some sanity checks for the configuration file
    if args.cfg is None:
        parser.error("Configuration file missing")

    if not os.path.exists(args.cfg):
        parser.error("Configuration file does not exist")

    if args.key is None:
        parser.error("Consumer key missing")

    if args.secret is None:
        parser.error("Consumer secret missing")

    if args.token is None:
        parser.error("Access token missing")

    if args.accesssecret is None:
        parser.error("Access secret missing")

    # then parse the configuration file
    config = configparser.ConfigParser()

    configfile = open(args.cfg, 'r')

    try:
        config.readfp(configfile)
    except Exception:
        print("Cannot read configuration file", file=sys.stderr)
        sys.exit(1)

    buddy_config = {}
    for section in config.sections():
        if section == 'ibuddy':
            try:
                productid = int(config.get(section, 'productid'))
                buddy_config['productid'] = productid
            except:
                pass

            buddy_config['reset_position'] = False
            try:
                reset_position_val = config.get(section, 'reset_position')
                if reset_position_val == 'yes':
                    buddy_config['reset_position'] = True
            except:
                pass
        if section == 'twitter':
            pass

    # get a reference to DBus
    bus = pydbus.SessionBus()

    # register a callback for messages that are received
    try:
        ibuddy = bus.get("nl.tjaldur.IBuddy", "/nl/tjaldur/IBuddy")
    except:
        ibuddy = None

    # get notifications
    notifications = bus.get('.Notifications')

    # create a twitter api endpoint
    api = twitter.Api(consumer_key=args.key,
                      consumer_secret=args.secret,
                      access_token_key=args.token,
                      access_token_secret=args.accesssecret,
                      sleep_on_rate_limit=True)

    # set of timestamps to ignore
    retweetsignorelist = set()
    verbose = True

    while True:
        curtime = calendar.timegm(time.gmtime())
        if verbose:
            print("Current time:", time.asctime(time.localtime(curtime)))
            sys.stdout.flush()

        retweets = api.GetRetweetsOfMe()
        for r in retweets:
            # only process the most recent ones that happened in the last 15 minutes = 900 seconds
            if curtime - r.created_at_in_seconds > 900:
                continue
            retweetdata = r.AsDict()
            if retweetdata['id'] in retweetsignorelist:
                continue
            if ibuddy != None:
                try:
                    ibuddy.ExecuteBuddyCommand("YELLOW:HEART:WINGSHIGH:GO:SLEEP:NOHEART:PURPLE:WINGSLOW:GO:SLEEP:RESET")
                except:
                    pass
            retweetsignorelist.add(retweetdata['id'])
            time.sleep(0.5)
        time.sleep(60)

    # finally reset the i-buddy again
    ibuddy.ExecuteBuddyCommand("RESET")

if __name__ == "__main__":
    main(sys.argv)
