import unittest

from pagerduty import auth_method

class AuthMethodBaseTest(unittest.TestCase):

    @property
    def auth_method_class(self):
        return auth_method.AuthMethod

    def new_auth_method(self):
        return self.auth_method_class("token")


def AuthMethodTest(AuthMethodBaseTest):

    def test_auth_header(self):
        am = self.new_auth_method()
        with self.assertRaises(NotImplementedError):
            ah = am.auth_header

    def test_auth_param(self):
        am = self.new_auth_method()
        with self.assertRaises(NotImplementedError):
            ap = am.auth_param

class HeaderAuthMethodTest(AuthMethodBaseTest):

    @property
    def auth_method_class(self):
        return auth_method.HeaderAuthMethod

    def test_auth_param(self):
        am = self.new_auth_method()
        self.assertEqual({}, am.auth_param)

class BodyParameterAuthMethodTest(AuthMethodBaseTest):

    @property
    def auth_method_class(self):
        return auth_method.BodyParameterAuthMethod

    def test_auth_header(self):
        am = self.new_auth_method()
        self.assertEqual({}, am.auth_header)

class PassThruHeaderAuthMethodTest(AuthMethodBaseTest):

    @property
    def auth_method_class(self):
        return auth_method.PassThruHeaderAuthMethod

    def test_auth_header(self):
        am = self.new_auth_method()
        self.assertEqual({"Authorization": "token"}, am.auth_header)
