import unittest, json
from datetime import datetime,timezone,timedelta
from studio.story import all_series,next_episode,neutral_script,validate_script,series_files
from studio.trends import rank,parse_traffic,theme,pick_unseen
from studio.util import read
from studio.season_factory import _valid_model

class ProjectTests(unittest.TestCase):
    def test_starter_order(self):
        ss=all_series();self.assertEqual(ss[0]['series_id'],'S01_the_last_little_fox')
        self.assertEqual(ss[1]['series_id'],'S02_the_boy_who_forgot_tomorrow')
        self.assertEqual(ss[0]['episode_count'],12);self.assertEqual(ss[1]['episode_count'],10)
    def test_next_episode_never_skips(self):
        queue={'rendered':{}}
        self.assertTrue(next_episode(queue)[1]['id'].endswith('_E01'))
        for m in all_series()[:1]:
            _,e,_=series_files(m)
            for x in e['episodes']:queue['rendered'][x['id']]={'ok':True}
        self.assertEqual(next_episode(queue)[0]['series_order'],2)
    def test_locked_voice_and_character_ids(self):
        all_ids=set()
        for m in all_series()[:2]:
            _,ep,cast=series_files(m)
            self.assertGreaterEqual(len(ep['episodes']),10)
            assert len(cast['characters'])==5
            for c in cast['characters']:
                self.assertNotIn(c['id'],all_ids);all_ids.add(c['id'])
                self.assertTrue(c['identity_spec_lock'])
                self.assertTrue(c['voice']['voice_id'])
                self.assertTrue(c.get('visual') or c['id'].endswith('narrator'))
                self.assertFalse((c['voice']['voice_id'] or '').startswith('en-US-Andrew'))
            for e in ep['episodes']:
                script=neutral_script(m,e,cast)
                validate_script(script,cast,e)
    def test_traffic(self):
        self.assertEqual(parse_traffic('200K+'),200000)
        self.assertEqual(parse_traffic('1.2M+'),1200000)
    def test_trends_select_grounded_recent_eligible(self):
        now=datetime.now(timezone.utc)
        entries=[{'title':'Mars mission','geo':'US','traffic':800000,'observed_utc':now.isoformat(),'source_url':'https://trends.google.com/trending/'},
                 {'title':'Moon telescope','geo':'GB','traffic':50000,'observed_utc':now.isoformat()},
                 {'title':'Political election','geo':'US','traffic':50000000,'observed_utc':now.isoformat()},
                 {'title':'Ocean yesterday','geo':'CA','traffic':3000000,'observed_utc':(now-timedelta(days=10)).isoformat()}]
        ranked=rank({'entries':entries},now)
        self.assertEqual(ranked[0]['topic'],'Mars mission')
        self.assertIsNone(theme('election scandal'))
        self.assertEqual(pick_unseen({'entries':entries},{'selected':[{'topic':'Mars mission'}]})['topic'],'Moon telescope')
    def test_zero_verified_trend_means_no_new_series(self):
        self.assertIsNone(pick_unseen({'entries':[]},{'selected':[]}))
    def test_invalid_auto_series_rejected(self):
        self.assertFalse(_valid_model({'episodes':[{'title':'one'}]*9,'characters':[]}))
    def test_cloud_defaults(self):
        config=read('cloud_config.json')
        self.assertTrue(config['publish_unreviewed'])
        self.assertEqual(config['platform_modes'],{'youtube':'public','facebook':'PUBLISHED','tiktok':'inbox'})
        self.assertEqual(config['upload_policy']['default_action'],'generate_and_upload')
        self.assertTrue(config['series']['auto_new_after_starters'])
        self.assertEqual(config['timezone'],'Africa/Cairo')
if __name__=='__main__':unittest.main()
