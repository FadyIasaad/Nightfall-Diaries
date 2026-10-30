import os
import unittest
from pathlib import Path
from unittest.mock import patch
from studio import publish
from studio.one_click import MODES
from studio.util import read

class AutoUploadV41Tests(unittest.TestCase):
    def setUp(self):
        self.config=read('cloud_config.json')

    def test_manual_default_upload_mode_exists(self):
        self.assertEqual(MODES[0],'generate_and_upload')

    def test_public_without_secret_downgrades_before_upload(self):
        with patch.dict(os.environ,{},clear=True):
            y,fall=publish.resolved_upload_config(self.config,'youtube')
            f,fall2=publish.resolved_upload_config(self.config,'facebook')
            self.assertEqual(y['platform_modes']['youtube'],'private')
            self.assertEqual(f['platform_modes']['facebook'],'DRAFT')
            self.assertTrue(fall and fall2)
            self.assertEqual(self.config['platform_modes']['youtube'],'public')
            self.assertEqual(self.config['platform_modes']['facebook'],'PUBLISHED')

    def test_public_with_explicit_secret_kept(self):
        with patch.dict(os.environ,{'DRAMA_ALLOW_UNREVIEWED_PUBLIC':'true'}):
            y,fall=publish.resolved_upload_config(self.config,'youtube')
            f,fall2=publish.resolved_upload_config(self.config,'facebook')
            self.assertEqual(y['platform_modes']['youtube'],'public')
            self.assertEqual(f['platform_modes']['facebook'],'PUBLISHED')
            self.assertFalse(fall or fall2)

    def test_tiktok_inbox_never_claims_public(self):
        with patch.dict(os.environ,{'DRAMA_ALLOW_UNREVIEWED_PUBLIC':'true'}):
            t,fall=publish.resolved_upload_config(self.config,'tiktok')
            self.assertEqual(t['platform_modes']['tiktok'],'inbox')
            self.assertFalse(fall)

    def test_youtube_private_fallback_is_used_by_adapter(self):
        fake_queue={'uploads':{},'rendered':{}}
        calls=[]
        def fake_adapter(path,title,desc,config):
            calls.append(config['platform_modes']['youtube'])
            return {'status':'staged','id':'x'}
        with patch.dict(os.environ,{},clear=True), patch.object(publish,'read',return_value=fake_queue), \
             patch.object(publish,'save'), patch.object(publish,'checkpoint'), \
             patch.dict(publish.ADAPTERS,{'youtube':fake_adapter}):
            result=publish.upload_all('S01_the_last_little_fox_E01',Path('/tmp/a.mp4'),'Title','Desc',self.config,platforms=['youtube'],allow_safe_fallback=True)
        self.assertEqual(calls,['private'])
        self.assertEqual(result['youtube']['status'],'staged')
        self.assertIn('fallback_reason',result['youtube'])

    def test_duplicate_upload_is_not_retried(self):
        fake_queue={'uploads':{'E01':{'youtube':{'status':'staged','id':'already'}}},'rendered':{}}
        with patch.object(publish,'read',return_value=fake_queue), patch.dict(publish.ADAPTERS,{'youtube':lambda *args: self.fail('should not upload')}):
            result=publish.upload_all('E01',None,'Title','Desc',self.config,platforms=['youtube'],allow_safe_fallback=True)
        self.assertEqual(result['youtube']['status'],'not_retried')

if __name__=='__main__':unittest.main()
