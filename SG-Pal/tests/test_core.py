import io, tempfile, unittest, sys, json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from PIL import Image
from core import Store,normalise,parse_response
from app import App
from ui import render
class Tests(unittest.TestCase):
 def test_rewards_persist_and_no_duplicate(self):
  with tempfile.TemporaryDirectory() as folder:
   path=Path(folder)/'progress.json'; s=Store(path)
   self.assertTrue(s.discover('chope','a')); self.assertFalse(s.discover('chope','a'))
   self.assertEqual(s.data['xp'],10); self.assertTrue(s.activate('chope'))
   self.assertFalse(s.finish('chope','a')); self.assertTrue(s.finish('chope','b'))
   self.assertFalse(s.finish('chope','c')); self.assertEqual(Store(path).data['xp'],35)
 def test_image_normalisation(self):
  out=io.BytesIO(); Image.new('RGBA',(1600,1200),'red').save(out,'PNG')
  with Image.open(io.BytesIO(normalise(out.getvalue()))) as im:
   self.assertEqual(im.size,(1280,960)); self.assertEqual(im.mode,'RGB')
 def test_response_rejects_incomplete_and_unknown_id(self):
  with self.assertRaises(RuntimeError): parse_response({'status':'incomplete'})
  obj={'culture_id':'fake','confidence':'high','verified':False,'observation':'x'}
  with self.assertRaises(ValueError): parse_response({'status':'completed','output':[{'content':[{'type':'output_text','text':json.dumps(obj)}]}]})
 def test_low_confidence_never_rewards(self):
  with tempfile.TemporaryDirectory() as folder:
   a=App(data_dir=folder); a.photo=b'test'
   a.handle('recognised',{'culture_id':'chope','confidence':'low','verified':False,'observation':'Unclear'})
   self.assertEqual(a.store.data['xp'],0); self.assertIsNone(a.cid)
 def test_quest_failure_and_success(self):
  with tempfile.TemporaryDirectory() as folder:
   a=App(data_dir=folder); a.store.discover('chope','old'); a.store.activate('chope')
   a.quest_mode=True; a.photo=b'new'
   obj={'culture_id':'chope','confidence':'low','verified':True,'observation':'Unclear'}
   a.handle('recognised',obj); self.assertEqual(a.store.data['xp'],10)
   obj['confidence']='high'; a.handle('recognised',obj); self.assertEqual(a.store.data['xp'],35)
 def test_demo_isolation_and_all_screens(self):
  with tempfile.TemporaryDirectory() as folder:
   live=App(data_dir=folder); demo=App(demo=True,data_dir=folder)
   demo.store.discover('chope','demo'); self.assertEqual(live.store.data['xp'],0)
   demo.cid='chope'; demo.result={'observation':'Visible tissue packet.'}; demo.error='Network unavailable'
   for screen in ['home','log','quest','pal','result','detail','verified','error','busy','capture_help']:
    demo.screen=screen; self.assertEqual(render(demo).size,(320,240))
if __name__=='__main__': unittest.main()
