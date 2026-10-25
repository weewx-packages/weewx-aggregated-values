#    Copyright (c) 2025 Rich Bell <bellrichm@gmail.com>
#
#    See the file LICENSE.txt for your full rights.
#

""" Installer for AggregatedValues service.

To uninstall run
weectl extension uninstall -y AggregatedValues
"""

from io import StringIO

import configobj
import os
import stat
import weewx

from weecfg.extension import ExtensionInstaller

VERSION = "1.1.10"

def fatal_error(error_str):
    """ Print an error and abort the install. """
    print()
    print(error_str)
    print()
    print()
    raise weewx.UnsupportedFeature("Fatal Error")

def loader():
    """ Load and return the extension installer. """
    return AggregatedValuesInstaller()


class AggregatedValuesInstaller(ExtensionInstaller):
    """ The extension installer. """
    def __init__(self):

        install_dict = {
            'version': VERSION,
            'name': 'AggregatedValues',
            # add a leading space, so that long versions does not run into the description
            'description': ' Calculate aggregated values that other extensions can then use without duplicating functionality and database lookups',
            'author': "John Smith",
            'author_email': "deltafoxtro256+AggregatedValues@gmail.com",
            'files': [('bin/user', ['bin/user/AggregatedValues.py'])]
        }

        install_dict['prep_services'] = 'user.AggregatedValues.AggregatedValuesService'

        super().__init__(install_dict)

    def configure(self, engine):
        """ Create the cache directory and save its location in the config. """

        if engine.config_dict is None:
            fatal_error("engine.config_dict is None, can't continue...")

        data_dir = engine.config_dict.get("WEEWX_ROOT", None)
        if data_dir is None or not os.path.isdir(data_dir):
            fatal_error("Failed to determine where to store AggregatedValues cache files, you may need to set WEEWX_ROOT in weewx.conf")

        statinfo = os.stat(data_dir)
        data_uid = statinfo.st_uid
        data_gid = statinfo.st_gid

        cache_dir = os.path.join(data_dir, "AggregatedValues")

        if os.path.exists(cache_dir) and not os.path.isdir(cache_dir):
            os.remove(cache_dir)

        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)

        if not os.path.exists(cache_dir):
            fatal_error("Failed to create the directory for the AggregatedValues cache files, can't continue...")

        desired_mode = stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH | stat.S_ISGID
        current_mode = os.stat(cache_dir).st_mode

        if current_mode != desired_mode | stat.S_IFDIR:
            os.chmod(cache_dir, desired_mode)

        statinfo = os.stat(cache_dir)
        cache_uid = statinfo.st_uid
        cache_gid = statinfo.st_gid

        if cache_uid != data_uid or cache_gid != data_gid:
            os.chown(cache_dir, data_uid, data_gid)
            for fn in os.listdir(cache_dir):
                os.chown(os.path.join(cache_dir, fn), data_uid, data_gid)

        current_mode = os.stat(cache_dir).st_mode
        statinfo = os.stat(cache_dir)
        cache_uid = statinfo.st_uid
        cache_gid = statinfo.st_gid

        if current_mode != desired_mode | stat.S_IFDIR or cache_uid != data_uid or cache_gid != data_gid:
            fatal_error("Failed to set the correct permissions for the AggregatedValues cache directory, can't continue...")

        service_dict = engine.config_dict.get("AggregatedValues", None)
        if service_dict is None:
            engine.config_dict["AggregatedValues"] = {}
            service_dict = engine.config_dict.get("AggregatedValues")

        if service_dict.get("cache_dir") != cache_dir:
            service_dict["cache_dir"] = cache_dir

        if engine.dry_run:
            engine.printer.out(engine.config_dict)
            engine.printer.out("-" * 72)
            return False

        return True
