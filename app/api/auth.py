from ldap3 import Connection, SUBTREE, Server
from ldap3.utils.conv import escape_filter_chars

from app.config import LDAP_HOST, LDAP_PASSWORD, LDAP_USER_BASE, LDAP_USER_DN


def authenticate_ldap(username: str, password: str):
    if not username or not password:
        return None

    if not LDAP_USER_DN or not LDAP_PASSWORD:
        raise RuntimeError("LDAP service account is not configured.")

    server = Server(LDAP_HOST)
    admin = Connection(
        server,
        user=LDAP_USER_DN,
        password=LDAP_PASSWORD,
        raise_exceptions=False,
    )
    user_conn = None

    try:
        if not admin.bind():
            description = admin.result.get("description", "unknown error")
            raise RuntimeError(f"LDAP service bind failed: {description}")

        search_filter = f"(uid={escape_filter_chars(username)})"
        if not admin.search(
            LDAP_USER_BASE,
            search_filter,
            SUBTREE,
            attributes=["uid", "cn", "memberOf"],
        ):
            description = admin.result.get("description", "unknown error")
            raise RuntimeError(f"LDAP user search failed: {description}")

        if not admin.entries:
            return None

        entry = admin.entries[0]
        user_conn = Connection(
            server,
            user=entry.entry_dn,
            password=password,
            raise_exceptions=False,
        )
        if not user_conn.bind():
            if user_conn.result.get("result") == 49:
                return None
            description = user_conn.result.get("description", "unknown error")
            raise RuntimeError(f"LDAP user bind failed: {description}")

        groups = [str(group) for group in getattr(entry, "memberOf", [])]
        role = (
            "PROFESSOR"
            if any("professor" in group.lower() for group in groups)
            else "ESTUDANTE"
        )
        return {"username": username, "role": role}
    finally:
        if user_conn is not None:
            user_conn.unbind()
        admin.unbind()
