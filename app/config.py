import os
KAFKA = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
ELASTIC_URL = os.getenv("ELASTIC_URL", "http://elasticsearch:9200")
LDAP_HOST = os.getenv("LDAP_HOST", "ldap://localhost:389")
LDAP_BASE_DN = os.getenv("LDAP_BASE_DN", "dc=example,dc=org")
LDAP_USER_BASE = os.getenv("LDAP_USER_BASE", "ou=people,dc=example,dc=org")
LDAP_USER_DN = os.getenv("LDAP_USER_DN", "cn=admin,dc=example,dc=org")
LDAP_PASSWORD = os.getenv("LDAP_PASSWORD", "")
