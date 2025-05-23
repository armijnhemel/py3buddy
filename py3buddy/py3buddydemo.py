# Demo program to show how to use the py3buddy module
#
# Copyright 2017-2019 - Armijn Hemel for Tjaldur Software Governance Solutions
# SPDX-Identifier: MIT

import sys
import os
import argparse
import configparser
import random
import time
import py3buddy


def panic(ibuddy, paniccount):
    # a demo version to show some of the capabilities of the iBuddy

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

        # random wiggle
        ibuddy.wiggle(random.choice(['right', 'left', 'middle', 'middlereset']))
        ibuddy.sendcommand()
        time.sleep(0.1)

    # extra reset as sometimes the device doesn't respond
    ibuddy.reset()
    ibuddy.reset()


# demo code to loop through the 8 available colours for the head LED
# good to train people what colour to pick for the dice
def colourloop(ibuddy, loopcount):
    ibuddy.reset()
    for i in range(0, loopcount):
        for c in py3buddy.allcolours:
            ibuddy.setcolour(c)
            ibuddy.sendcommand()
            time.sleep(1)
    ibuddy.reset()
    ibuddy.reset()


def dice(ibuddy, dicecount):
    # turn iBuddy into an 8 sided dice with colours
    ibuddy.reset()
    dicecounter = 1
    chosencolour = None
    for i in range(0, dicecount):
        # pick a random colour for the head LED
        chosencolour = random.choice(py3buddy.allcolours)
        ibuddy.setcolour(chosencolour)
        # create the message, then send it, and sleep for 0.1 seconds
        if dicecounter == dicecount:
            ibuddy.toggleheart(True)
        dicecounter += 1
        ibuddy.sendcommand()
        time.sleep(0.1)
    if chosencolour == py3buddy.NOCOLOUR:
        print("iBuddy chose: no colour!\n")
    elif chosencolour == py3buddy.RED:
        print("iBuddy chose: red!\n")
    elif chosencolour == py3buddy.BLUE:
        print("iBuddy chose: blue!\n")
    elif chosencolour == py3buddy.GREEN:
        print("iBuddy chose: green!\n")
    elif chosencolour == py3buddy.CYAN:
        print("iBuddy chose: cyan!\n")
    elif chosencolour == py3buddy.YELLOW:
        print("iBuddy chose: yellow!\n")
    elif chosencolour == py3buddy.PURPLE:
        print("iBuddy chose: purple!\n")
    elif chosencolour == py3buddy.WHITE:
        print("iBuddy chose: white!\n")
    time.sleep(5)
    # extra reset as sometimes the device doesn't respond
    ibuddy.reset()
    ibuddy.reset()


def main(argv):
    parser = argparse.ArgumentParser()

    # options for the commandline
    parser.add_argument("-c", "--config", action="store", dest="cfg",
                        help="path to configuration file", metavar="FILE")
    args = parser.parse_args()

    # first some sanity checks for the configuration file
    if args.cfg is None:
        parser.error("Configuration file missing")

    if not os.path.exists(args.cfg):
        parser.error("Configuration file does not exist")

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

    # initialize an iBuddy and check if a device was found and is accessible
    ibuddy = py3buddy.iBuddy(buddy_config)
    if ibuddy.dev is None:
        print("No iBuddy found, or iBuddy not accessible", file=sys.stderr)
        sys.exit(1)

    print("\npy3buddy demo scripts\n")
    print("Demo 1: PANIC!\n")
    panic(ibuddy, 10)

    looptimes = 4
    print("Demo 2: Looping through all available colours %d times\n" % looptimes)
    colourloop(ibuddy, looptimes)

    print("Demo 3: Playing dice\n")
    dice(ibuddy, 60)

    print("Demo 4: Executing commands\n")
    cmds = ["WHITE:WINGSHIGH:HEART:GO:SLEEP",
            "RED:WINGSLOW:GO:SLEEP:NOHEART:LEFT:GO:SLEEP:RESET",
            "::BLUE:GO:SHORTSLEEP"]
    for cmd in cmds:
        print("Executing: ", cmd)
        ibuddy.executecommand(cmd)
    ibuddy.reset()

if __name__ == "__main__":
    main(sys.argv)
