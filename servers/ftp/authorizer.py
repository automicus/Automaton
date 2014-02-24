try:
    from hashlib import md5
except ImportError:
    from md5 import new as md5  # Python < 2.5
from pyftpdlib.authorizers import DummyAuthorizer, AuthenticationFailed


class HumbleAuthorizer(DummyAuthorizer):
    """
        This custom authorizer runs similar to the default
        except that it requires that passwords be in MD5
        hash form instead of clear text.
        """
    def validate_authentication(self, username, password, handler):
        """Raises AuthenticationFailed if supplied username and
            password don't match the stored credentials, else return
            None.
            """
        hash = md5(password).hexdigest()
        msg = "Authentication failed."
        if not self.has_user(username):
            if username == 'anonymous':
                msg = "Anonymous access not allowed."
            raise AuthenticationFailed(msg)
        if username != 'anonymous':
            if self.user_table[username]['pwd'] != hash:
                raise AuthenticationFailed(msg)
