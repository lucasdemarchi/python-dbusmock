#!/usr/bin/python3

# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 3 of the License, or (at your option) any
# later version.  See http://www.gnu.org/copyleft/lgpl.html for the full text
# of the license.

__author__ = 'Martin Pitt'
__email__ = 'martin.pitt@ubuntu.com'
__copyright__ = '(c) 2012 Canonical Ltd.'
__license__ = 'LGPL 3+'

import unittest
import sys
import subprocess

import dbusmock


p = subprocess.Popen(['which', 'upower'], stdout=subprocess.PIPE)
p.communicate()
have_upower = (p.returncode == 0)


class TestCLI(dbusmock.DBusTestCase):
    '''Test running dbusmock from the command line'''

    @classmethod
    def setUpClass(klass):
        klass.start_system_bus()
        klass.start_session_bus()
        klass.system_con = klass.get_dbus(True)
        klass.session_con = klass.get_dbus()

    def setUp(self):
        self.p_mock = None

    def tearDown(self):
        if self.p_mock:
            self.p_mock.terminate()
            self.p_mock.wait()
            self.p_mock = None

    def test_session_bus(self):
        self.p_mock = subprocess.Popen([sys.executable, '-m', 'dbusmock',
                                        'com.example.Test', '/', 'TestIface'])
        self.wait_for_bus_object('com.example.Test', '/')

    def test_system_bus(self):
        self.p_mock = subprocess.Popen([sys.executable, '-m', 'dbusmock',
                                        '--system', 'com.example.Test', '/', 'TestIface'])
        self.wait_for_bus_object('com.example.Test', '/', True)

    def test_template_system(self):
        self.p_mock = subprocess.Popen([sys.executable, '-m', 'dbusmock',
                                        '--system', '-t', 'upower'],
                                       stdout=subprocess.PIPE,
                                       universal_newlines=True)
        self.wait_for_bus_object('org.freedesktop.UPower', '/org/freedesktop/UPower', True)

        # check that it actually ran the template, if we have upower
        if have_upower:
            out = subprocess.check_output(['upower', '--dump'],
                                          universal_newlines=True)
            self.assertRegex(out, 'on-battery:\s+no')
            self.assertRegex(out, 'can-suspend:\s+yes')

            mock_out = self.p_mock.stdout.readline()
            self.assertTrue('EnumerateDevices' in mock_out, mock_out)

        self.p_mock.stdout.close()

    def test_no_args(self):
        p = subprocess.Popen([sys.executable, '-m', 'dbusmock'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             universal_newlines=True)
        (out, err) = p.communicate()
        self.assertEqual(out, '')
        self.assertTrue('must specify NAME' in err, err)
        self.assertNotEqual(p.returncode, 0)

    def test_help(self):
        p = subprocess.Popen([sys.executable, '-m', 'dbusmock', '--help'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             universal_newlines=True)
        (out, err) = p.communicate()
        self.assertEqual(err, '')
        self.assertTrue('INTERFACE' in out, out)
        self.assertTrue('--system' in out, out)
        self.assertEqual(p.returncode, 0)


if __name__ == '__main__':
    # avoid writing to stderr
    unittest.main(testRunner=unittest.TextTestRunner(stream=sys.stdout, verbosity=2))
