import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'SourceCode'))
from quantumsafe import research_catalog as c
from quantumsafe.ai_research_advisor import build_context,local_advice
class TestMajor(unittest.TestCase):
    def test_both_splits_v3(self):
        data=c.load('v3','CV folds / Original')
        self.assertIn('70_30',c.options(data,'Split'))
        self.assertIn('80_20',c.options(data,'Split'))
    def test_models_v3(self):
        data=c.load('v3','All CV records')
        self.assertIn('Random Forest',c.options(data,'Model'))
        self.assertIn('XGBoost',c.options(data,'Model'))
    def test_v4_models(self):
        data=c.load('v4','CV records (468)')
        self.assertTrue({'Random Forest','XGBoost','LightGBM'}.issubset(set(c.options(data,'Model'))))
    def test_folds(self):
        data=c.load('v4','CV records (468)')
        self.assertGreaterEqual(len(c.options(data,'Fold')),3)
    def test_selection(self):
        data=c.load('v4','CV records (468)')
        selected=c.select(data,model='LightGBM',split='70_30',fold='1',balancing='Original')
        self.assertGreater(len(selected),0)
        self.assertTrue(all(r['Model']=='LightGBM' and r['Fold']=='1' and r['Split']=='70_30' for r in selected))
    def test_local_grounding(self):
        ctx=build_context('v4','CV records (468)',model='Random Forest',split='70_30',fold='1')
        self.assertGreater(ctx['count'],0)
        self.assertIn('historical',local_advice(ctx).lower())
    def test_invalid(self):
        with self.assertRaises(ValueError):c.get_path('v9','notafile')
if __name__=='__main__':unittest.main()
