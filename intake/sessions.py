"""Session engine: Django's database store, with intake drafts tied to the browser.

Django can't, with one setting, end a cookie at browser close and also give the database row a
short expiry: set_expiry(0) does the first but leaves the row for SESSION_COOKIE_AGE (two
weeks). While an intake draft is in the session this store reports "expire at browser close",
so the cookie dies with the browser, and the row keeps the short expiry the intake view sets.
"""

from django.contrib.sessions.backends.db import SessionStore as DatabaseSessionStore

# Where the intake form keeps unsubmitted answers. Defined here, not in views, so the session
# engine never imports the view layer.
APPLICATION_SESSION_KEY = 'intake_application'


class SessionStore(DatabaseSessionStore):
    def get_expire_at_browser_close(self):
        return APPLICATION_SESSION_KEY in self or super().get_expire_at_browser_close()
