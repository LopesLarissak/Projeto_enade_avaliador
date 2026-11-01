from ldap3 import Server, Connection, SUBTREE
from app.config import LDAP_HOST, LDAP_BASE_DN, LDAP_USER_BASE

def authenticate_ldap(username: str, password: str):
    if not username or not password:
        return None
    server = Server(LDAP_HOST)
    admin = Connection(server, user=None, password=None)
    # Busca o DN do usuário. Em laboratório, configure usuários e grupos no LDAP.
    from ldap3 import BASE, ANONYMOUS
    try:
        admin = Connection(server, authentication=ANONYMOUS, raise_exceptions=True)
        admin.bind()
        admin.search(LDAP_USER_BASE, f"(uid={username})", SUBTREE, attributes=["uid", "cn", "memberOf"])
        if not admin.entries:
            return None
        user_dn = admin.entries[0].entry_dn
        user_conn = Connection(server, user=user_dn, password=password, raise_exceptions=True)
        if not user_conn.bind():
            return None
        groups = [str(x) for x in getattr(admin.entries[0], "memberOf", [])]
        role = "PROFESSOR" if any("professor" in g.lower() for g in groups) else "ESTUDANTE"
        return {"username": username, "role": role}
    except Exception:
        return None
