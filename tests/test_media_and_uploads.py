import unittest, tempfile, os, json
from unittest.mock import patch
from pathlib import Path
import numpy as np, soundfile as sf
from studio.story import all_series,series_files
from studio.video import make_video
from studio.publish import MissingCredentials,_check_public,youtube,facebook,tiktok
from studio.season_factory import _invent,_new_voices

class AdapterChecks(unittest.TestCase):
 def test_no_youtube_credentials(self):
  with patch.dict(os.environ,{},clear=True):
   with self.assertRaises(MissingCredentials):youtube(Path('/tmp/none.mp4'),'title','desc',{'platform_modes':{'youtube':'private'},'publish_unreviewed':False})
 def test_no_fb_credentials(self):
  with patch.dict(os.environ,{},clear=True):
   with self.assertRaises(MissingCredentials):facebook(Path('/tmp/none.mp4'),'title','desc',{'platform_modes':{'facebook':'DRAFT'},'publish_unreviewed':False})
 def test_public_needs_both_controls(self):
  with patch.dict(os.environ,{},clear=True):
   with self.assertRaises(Exception):_check_public('public',False)
 def test_new_series_original_fallback(self):
  data=_invent({'theme':'ocean'},3)
  self.assertEqual(len(data['episodes']),10)
  self.assertGreaterEqual(len(data['characters']),3)
  self.assertTrue(len(set(_new_voices(data['characters']+[{'role':'narrator'}],set())))==4)
 def test_media_smoke_fast(self):
  m=all_series()[0];_,eps,cast=series_files(m);ep=eps['episodes'][0]
  script={'scenes':[{'character_id':cast['characters'][0]['id'],'text':'The blue feather is the clue.'}]}
  with tempfile.TemporaryDirectory() as d:
   root=Path(d)
   sf.write(root/'narration.wav',np.zeros(24000,dtype='float32'),24000)
   conf={'video':{'width':720,'height':1280,'fps':24,'min_seconds':.8,'max_seconds':2}}
   mp4,duration=make_video(m['series_id'],m,ep,script,cast,root/'narration.wav',[1.0],root,conf)
   self.assertTrue(mp4.exists());self.assertGreater(mp4.stat().st_size,5000)
   self.assertTrue(.8<duration<1.2)
if __name__=='__main__':unittest.main()
