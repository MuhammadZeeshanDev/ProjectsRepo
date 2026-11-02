import unittest
from quantumsafe.local_prolog_ai import analyze, normalize_evidence

class LocalAdvisorTests(unittest.TestCase):
    def test_no_training_and_no_events(self):
        o=analyze(prolog_executable='')
        self.assertIn('no_training',[r['rule'] for r in o['recommendations']])
        self.assertEqual(o['evidence']['blocked_events'],0)
    def test_training_and_gateway(self):
        t={'algorithm':'Random Forest','split':'70/30','heldout':{'macro_f1':0.7,'false_positive_rate':0.08},'folds':[{'macro_f1':0.5},{'macro_f1':0.8}], 'truncated_to_first_rows':True}
        e=[{'decision':'ALLOW'},{'decision':'BLOCK','attack_type':'replay_attack'}]
        o=analyze(t,e,prolog_executable='')
        codes=[r['rule'] for r in o['recommendations']]
        for c in ('high_fpr','unstable_folds','truncated_dataset','blocked_incidents','known_attack_types','live_unverified'):self.assertIn(c,codes)
        self.assertNotIn('no_training',codes)
    def test_does_not_treat_allow_as_block(self):
        o=analyze(None,[{'decision':'ALLOW','attack_type':'replay_attack'}],prolog_executable='')
        self.assertEqual(o['evidence']['blocked_events'],0)
        self.assertNotIn('known_attack_types',[r['rule'] for r in o['recommendations']])
    def test_bounded_input_and_no_secret_leak(self):
        x=normalize_evidence({'heldout':{},'API_KEY':'private'},[{'decision':'ALLOW','secret':'private'}]*220)
        self.assertEqual(x['recent_gateway_events'],200)
        self.assertNotIn('private',str(x))
if __name__=='__main__':unittest.main()
