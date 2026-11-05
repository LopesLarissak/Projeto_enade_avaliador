from types import SimpleNamespace

from app.api import auth


class FakeConnection:
    def __init__(self, server, user=None, password=None, **kwargs):
        self.user = user
        self.password = password
        self.entries = []
        self.result = {"result": 0, "description": "success"}
        self.bound = False

    def bind(self):
        if self.user == "cn=service,dc=example,dc=org":
            self.bound = self.password == "service-password"
        else:
            self.bound = self.password == "valid-password"
        if not self.bound:
            self.result = {"result": 49, "description": "invalidCredentials"}
        return self.bound

    def search(self, search_base, search_filter, search_scope, attributes):
        assert search_base == "ou=people,dc=example,dc=org"
        assert search_scope == auth.SUBTREE
        assert attributes == ["uid", "cn", "memberOf"]
        self.search_filter = search_filter
        self.entries = [
            SimpleNamespace(
                entry_dn="uid=test,ou=people,dc=example,dc=org",
                memberOf=["cn=professores,ou=groups,dc=example,dc=org"],
            )
        ]
        return True

    def unbind(self):
        self.bound = False


def configure_fake_ldap(monkeypatch, password="valid-password"):
    connections = []

    def create_connection(*args, **kwargs):
        connection = FakeConnection(*args, **kwargs)
        connections.append(connection)
        return connection

    monkeypatch.setattr(auth, "LDAP_USER_DN", "cn=service,dc=example,dc=org")
    monkeypatch.setattr(auth, "LDAP_PASSWORD", "service-password")
    monkeypatch.setattr(auth, "LDAP_USER_BASE", "ou=people,dc=example,dc=org")
    monkeypatch.setattr(auth, "Connection", create_connection)
    monkeypatch.setattr(auth, "Server", lambda host: host)
    return password, connections


def test_authenticate_ldap_returns_teacher_role(monkeypatch):
    password, _ = configure_fake_ldap(monkeypatch)

    result = auth.authenticate_ldap("test", password)

    assert result == {"username": "test", "role": "PROFESSOR"}


def test_authenticate_ldap_escapes_username_filter(monkeypatch):
    password, connections = configure_fake_ldap(monkeypatch)

    auth.authenticate_ldap("test*)(uid=*)", password)

    assert connections[0].search_filter == "(uid=test\\2a\\29\\28uid=\\2a\\29)"


def test_authenticate_ldap_rejects_invalid_password(monkeypatch):
    configure_fake_ldap(monkeypatch)

    assert auth.authenticate_ldap("test", "wrong-password") is None


def test_authenticate_ldap_rejects_empty_credentials(monkeypatch):
    configure_fake_ldap(monkeypatch)

    assert auth.authenticate_ldap("", "password") is None
    assert auth.authenticate_ldap("test", "") is None
