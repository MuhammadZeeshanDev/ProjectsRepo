import unittest
from quantumsafe.permissions import ROLES,may_run,may_manage_users,require_role,PermissionDenied
from quantumsafe.ml_decision_support import summarize_training,practical_guidance
class TestProfessionalRoles(unittest.TestCase):
 def test_only_two_roles(self):self.assertEqual(ROLES,('Admin','Researcher'))
 def test_permissions(self):
  self.assertTrue(may_run('Admin'));self.assertTrue(may_run('Researcher'))
  self.assertFalse(may_run('Viewer'));self.assertFalse(may_manage_users('Researcher'))
 def test_legacy_rejected(self):
  with self.assertRaises(PermissionDenied):require_role('Viewer',ROLES)
 def test_ai_no_model_or_raw_data(self):
  d={'algorithm':'Random Forest','split':'70/30','heldout':{'macro_f1':.9,'false_positive_rate':.02},'folds':[{'macro_f1':.91},{'macro_f1':.89}],'pipeline':object(),'raw_rows':['secret']}
  clean=summarize_training(d);self.assertNotIn('pipeline',clean);self.assertNotIn('raw_rows',clean)
  self.assertIn('NOT DEPLOYED',practical_guidance(clean))
if __name__=='__main__':unittest.main()
