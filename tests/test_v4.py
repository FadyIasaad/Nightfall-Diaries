import unittest
from pathlib import Path
from unittest.mock import patch
from studio.story import all_series,series_files
from studio.shot_plan import get_shot_plan,speech_from_plan
from studio.one_click import choose
from studio.util import read

class V4Checks(unittest.TestCase):
    def test_e01_has_eight_cinematic_shots(self):
        m=all_series()[0]; _,eps,c=series_files(m);ep=eps['episodes'][0]
        plan=get_shot_plan(m,ep,read('seasons/S01_the_last_little_fox/scripts/E01.json'),c)
        self.assertEqual(len(plan['shots']),8)
        self.assertEqual(plan['shots'][3]['prop'],'blue_feather')
        self.assertEqual(len(speech_from_plan(plan)['scenes']),8)
    def test_next_episode_not_advanced_on_preview(self):
        q={'rendered':{},'uploads':{},'last_preview':{'episode_id':'S01_the_last_little_fox_E01'}}
        self.assertEqual(choose(q,'auto')[1]['episode'],1)
    def test_explicit_episode_selection(self):
        self.assertEqual(choose({'rendered':{}},'S02_the_boy_who_forgot_tomorrow_E01')[0]['series_order'],2)
    def test_shot_character_voice_identity(self):
        m=all_series()[0];_,eps,cast=series_files(m)
        plan=get_shot_plan(m,eps['episodes'][0],read('seasons/S01_the_last_little_fox/scripts/E01.json'),cast)
        names={c['id'] for c in cast['characters']}
        self.assertTrue(all(s['character_id'] in names for s in plan['shots']))
        self.assertEqual(next(c for c in cast['characters'] if c['id']=='s01_ember')['voice']['voice_id'],'am_puck')
if __name__=='__main__':unittest.main()
