"""Facebook Page resolution without uploads, accidental pages or leaked tokens."""
import unittest
from unittest.mock import Mock

from pilot.facebook_page_auth import PageAuthError, resolve_nightfall_page


def reply(data):
    result = Mock(ok=True)
    result.json.return_value = data
    return result


class FacebookPageTokenSafetyTests(unittest.TestCase):
    def test_user_token_resolves_only_verified_nightfall_page(self):
        session = Mock()
        calls = []

        def get(url, *, headers, params, timeout):
            calls.append((url, headers["Authorization"], params["fields"]))
            if url.endswith("/me") and params["fields"] == "id,name":
                return reply({"id": "USER_123", "name": "Facebook User"})
            if url.endswith("/me/accounts"):
                return reply({"data": [
                    {"id": "WRONG", "name": "Other Page", "access_token": "bad-token"},
                    {"id": "PAGE_123", "name": "Nightfall Diaries",
                     "access_token": "correct-page-token"}]})
            if url.endswith("/PAGE_123"):
                self.assertEqual(headers["Authorization"], "Bearer correct-page-token")
                return reply({"id": "PAGE_123", "name": "Nightfall Diaries"})
            raise AssertionError("Unexpected read-only call")

        session.get.side_effect = get
        result = resolve_nightfall_page(
            session=session, token="user-token", expected_id="PAGE_123")
        self.assertEqual(result["id"], "PAGE_123")
        self.assertEqual(result["access_token"], "correct-page-token")
        self.assertEqual(result["source"], "user_token_resolved_to_page_token")
        self.assertEqual(len(calls), 3)
        session.post.assert_not_called()

    def test_wrong_expected_page_rejected_without_posting(self):
        session = Mock()
        session.get.side_effect = [
            reply({"id": "PERSON", "name": "Another User"}),
            reply({"data": [{"id": "PAGE_123", "name": "Nightfall Diaries",
                             "access_token": "secret"}]}),
        ]
        with self.assertRaises(PageAuthError):
            resolve_nightfall_page(
                session=session, token="user-token", expected_id="WRONG_ID")
        session.post.assert_not_called()

    def test_ambiguity_blocks_automatic_page_choice(self):
        session = Mock()
        session.get.side_effect = [
            reply({"id": "PERSON", "name": "Another User"}),
            reply({"data": [
                {"id": "PAGE1", "name": "Nightfall Diaries", "access_token": "t1"},
                {"id": "PAGE2", "name": "Nightfall Diaries", "access_token": "t2"},
            ]}),
        ]
        with self.assertRaises(PageAuthError):
            resolve_nightfall_page(session=session, token="user-token",
                                   expected_id="")
        session.post.assert_not_called()

    def test_verified_existing_page_token_uses_no_user_page_list(self):
        session = Mock()
        session.get.side_effect = [
            reply({"id": "PAGE", "name": "Nightfall Diaries"}),
            reply({"id": "PAGE", "category": "Entertainment"}),
        ]
        result = resolve_nightfall_page(
            session=session, token="page-token", expected_id="PAGE")
        self.assertEqual(result["id"], "PAGE")
        self.assertEqual(result["access_token"], "page-token")
        self.assertEqual(result["source"], "verified_page_token")
        self.assertEqual(session.get.call_count, 2)
        session.post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
