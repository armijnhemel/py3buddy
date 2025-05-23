#!/usr/bin/env python3

# Demo program to show how to use the py3buddy module with DBus and expose
# it to other programs on the session DBus
#
# Uses python3-gobject-base and python3-pydbus (package names from Fedora)
#
# Copyright 2017-2019 - Armijn Hemel for Tjaldur Software Governance Solutions
# SPDX-Identifier: MIT

import sys
import os
import argparse
import configparser
import py3buddy
import pydbus
import gi


# wrap an iBuddy inside a DBus service
class IBuddyDbusService(object):
    """
    <node>
    <interface name='nl.tjaldur.IBuddy'>
    <method name='ExecuteBuddyCommand'>
    <arg type='s' name='command' direction='in'/>
    </method>
    <method name='Quit'/>
    </interface>
    </node>
        """

    # make sure the iBuddy is available for the commands
    def __init__(self, ibuddy, loop):
        self.ibuddy = ibuddy
        self.loop = loop

    def ExecuteBuddyCommand(self, command):
        self.ibuddy.executecommand(command)
        self.ibuddy.reset()

    def Quit(self):
        self.loop.quit()


def main(argv):
    parser = argparse.ArgumentParser()

    # options for the commandline
    parser.add_argument("-c", "--config", action="store",
                        dest="cfg", help="path to configuration file",
                        metavar="FILE")
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
        if section == 'twitter':
            pass

    # initialize an iBuddy and check if a device was found and is accessible
    ibuddy = py3buddy.iBuddy(buddy_config)
    if ibuddy.dev is None:
        print("No iBuddy found, or iBuddy not accessible", file=sys.stderr)
        sys.exit(1)

    loop = gi.repository.GObject.MainLoop()
    # get a reference to the session DBus and expose the iBuddy on it
    bus = pydbus.SessionBus()
    bus.publish("nl.tjaldur.IBuddy", IBuddyDbusService(ibuddy, loop))

    loop.run()

    # finally reset the i-buddy again
    ibuddy.reset()

if __name__ == "__main__":
    main(sys.argv)
