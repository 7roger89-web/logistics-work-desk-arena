import os, sys, unittest
from unittest.mock import patch
sys.path.insert(0, '.')

WRITE_PERMS = set(('shipment_create', 'shipment_update', 'shipment_delete', 'customer_create', 'customer_update', 'customer_delete', 'user_create', 'user_create', 'user_update', 'user_delete', 'admin_access'))

class LG01EnvSecurityTests(unittest.TestCase):
    def test_validate_allows_dev(self):
        import core.config as c
        c.validate_mongo_identity()

    def test_validate_rejects_prod(self):
        import core.config as c
        old = c.MONGO_DB_NAME
        c.MONGO_DB_NAME = 'logistics_db'
        try:
            with self.assertRaises(RuntimeError) as ctx:
                c.validate_mongo_identity()
            self.assertIn('PRODUCTION', str(ctx.exception))
        finally:
            c.MONGO_DB_NAME = old

    def test_validate_rejects_empty_db(self):
        import core.config as c
        old = c.MONGO_DB_NAME
        c.MONGO_DB_NAME = ''
        try:
            with self.assertRaises(RuntimeError):
                c.validate_mongo_identity()
        finally:
            c.MONGO_DB_NAME = old

    def test_validate_rejects_unknown_db(self):
        import core.config as c
        old = c.MONGO_DB_NAME
        c.MONGO_DB_NAME = 'totally_unknown_db'
        try:
            with self.assertRaises(RuntimeError):
                c.validate_mongo_identity()
        finally:
            c.MONGO_DB_NAME = old

    def test_actor_never_admin(self):
        import core.auth as a
        with patch.object(a, 'current_user', return_value={}):
            self.assertEqual(a.current_actor(), 'system')

    def test_assert_permission_denied_for_viewer(self):
        import core.auth as a
        user = {'username': 'viewer1', 'display_name': 'V1', 'role': 'viewer'}
        with patch.object(a, 'current_user', return_value=user):
            with self.assertRaises(a.PermissionDeniedError):
                a.assert_permission('finance_approve')

    def test_anonymous_role_has_no_write_perms(self):
        import core.auth as a
        anon = a.ROLE_PERMISSIONS.get('anonymous', set())
        self.assertEqual(anon and WRITE_PERMS, set())

if __name__ == '__main__':
    unittest.main()
