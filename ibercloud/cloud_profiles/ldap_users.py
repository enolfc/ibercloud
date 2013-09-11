import ldap
import ldap.modlist as modlist
from django.conf import settings
from django.contrib.auth.hashers import make_password


def get_ldap_conn(server=None, bind_dn=None, passwd=None):
    # Options
    opts = getattr(settings, 'CLOUD_PROFILES_LDAP_OPTIONS', {})
    for opt in opts.items():
        ldap.set_option(opt[0], opt[1])
    if not server:
        server = settings.CLOUD_PROFILES_LDAP_SERVER_URI
    if not bind_dn:
        bind_dn = settings.CLOUD_PROFILES_LDAP_BIND_DN
    if not passwd:
        passwd = settings.CLOUD_PROFILES_LDAP_BIND_PASSWORD
    conn = ldap.initialize(server)
    conn.simple_bind_s(bind_dn, passwd)
    return conn


def check_user_password(dn, passwd):
    try:
        get_ldap_conn(bind_dn=dn, passwd=str(passwd))
        return True
    except ldap.LDAPError:
        return False

def reset_user_password(dn, password):
    conn = get_ldap_conn()
    ldif = modlist.modifyModlist({'userpassword': 'fake'},
                                 {'userpassword': str(password)})
    conn.modify_s(dn, ldif)


def change_user_password(dn, old_pwd, new_pwd):
    conn = get_ldap_conn(bind_dn=dn, passwd=str(old_pwd))
    ldif = modlist.modifyModlist({'userpassword': str(old_pwd)},
                                 {'userpassword': str(new_pwd)})
    conn.modify_s(dn, ldif)


def delete_user(dn):
    conn = get_ldap_conn()
    conn.delete_s(dn)


def create_user(dn, email, name, uid):
    conn = get_ldap_conn()
    user_info = {'uid': email.encode('ascii', 'replace'),
                 'cn': name.encode('ascii', 'replace'),
                 'uidnumber': str(uid),
                 'gidnumber': str(uid),
                 'objectclass': ('account',
                                 'posixAccount',
                                 'top',
                                 'shadowAccount'),
                 'homedirectory': '/',
                 'shadowlastchange': '538',
                 'shadowmin': '0',
                 'shadowmax': '999999',
                 'shadowwarning': '22',
                 'shadowinactive': '15',
                 'shadowexpire': '-1',
                 'shadowflag': '0',
                 'userpassword': make_password(None).encode('ascii', 'ignore'),
                 }
    print user_info
    ldif = modlist.addModlist(user_info)
    conn.add_s(dn, ldif)
