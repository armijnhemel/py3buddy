#!/usr/bin/env python3

# Demo program to show how to use the py3buddy module with Twitter
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
import random
import time
import calendar
import re
import py3buddy
import twitter


def panic(ibuddy, paniccount):
    # a demo version to show some of the capabilities of
    # the iBuddy

    # first reset the iBuddy
    ibuddy.reset()

    for i in range(0, paniccount):
        # set the wings to high
        ibuddy.wings('high')

        # turn on the heart LED
        ibuddy.toggleheart(True)

        # pick a random colour for the head LED
        ibuddy.setcolour(random.choice(py3buddy.allcolours))

        # wiggle randomly
        ibuddy.wiggle(random.choice(['right', 'left', 'middle', 'middlereset']))

        # create the message, then send it, and sleep for 0.1 seconds
        ibuddy.sendcommand()
        time.sleep(0.1)

        # set the wings to low
        ibuddy.wings('low')

        # turn off the heart LED
        ibuddy.toggleheart(False)

        # pick a random colour for the head LED
        ibuddy.setcolour(random.choice(py3buddy.allcolours))

        # wiggle randomly
        ibuddy.wiggle(random.choice(['right', 'left', 'middle', 'middlereset']))
        ibuddy.sendcommand()
        time.sleep(0.1)
    # extra reset as sometimes the device doesn't respond
    ibuddy.reset()
    ibuddy.reset()


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
    parser.add_argument("-a", "--accesssecret", action="store",
                        dest="accesssecret", help="access secret",
                        metavar="SECRET")
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
        config.read_file(configfile)
    except Exception as e:
        print(f"Cannot read configuration file: {e}", file=sys.stderr)
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

    # initialize an iBuddy and check if a device was found and is accessible
    ibuddy = py3buddy.iBuddy(buddy_config)
    if ibuddy.dev is None:
        print("No iBuddy found, or iBuddy not accessible", file=sys.stderr)
        sys.exit(1)

    # create a twitter api endpoint
    api = twitter.Api(consumer_key=args.key,
                      consumer_secret=args.secret,
                      access_token_key=args.token,
                      access_token_secret=args.accesssecret,
                      sleep_on_rate_limit=True)

    # set of timestamps to ignore
    ignorelist = set()

    # loop
    magnitudere = re.compile('(\d\.\d) magnitude #earthquake')
    while(True):
        curtime = calendar.timegm(time.gmtime())
        print("Current time:", time.asctime(time.localtime(curtime)))

        # get earthquake data from a Twitter account
        quakes = api.GetUserTimeline(screen_name='quakestoday')
        for q in quakes:
            # only process the most recent ones that happened
            # in the last 15 minutes = 900 seconds
            if curtime - q.created_at_in_seconds > 900:
                continue
            quakedata = q.AsDict()
            if quakedata['id'] in ignorelist:
                continue
            magnituderes = magnitudere.match(quakedata['text'])
            if magnituderes is None:
                continue
            magnitude = float(magnituderes.groups()[0])
            shakelength = int(magnitude*2)
            if 'place' in quakedata:
                location = quakedata['place']['country']
            else:
                location = 'unspecified'
            print('Time %s, location: %s, magnitude %.1f\n' % (time.asctime(time.localtime(q.created_at_in_seconds)), location, magnitude))
            panic(ibuddy, shakelength)
            ignorelist.add(quakedata['id'])
            time.sleep(0.5)
        time.sleep(60)

    # finally reset the i-buddy again
    ibuddy.reset()

if __name__ == "__main__":
    main(sys.argv)
