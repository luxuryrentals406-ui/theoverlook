"""The real pixel appears once per content page; inquiry clicks are not leads."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]

class MetaPixel(unittest.TestCase):
    def test_content_pages_initialize_once_and_track_one_pageview(self):
        pages = [p for p in ROOT.rglob('*.html') if '.git' not in p.parts and '<!-- Meta Pixel Code -->' in p.read_text()]
        self.assertEqual(len(pages), 18)
        for p in pages:
            s = p.read_text()
            head = s.split('</head>')[0]
            self.assertEqual(head.count("fbq('init', '1113575654229940')"), 1, p)
            self.assertEqual(head.count("fbq('track', 'PageView')"), 1, p)
            self.assertIn('https://connect.facebook.net/en_US/fbevents.js', head)
            self.assertNotIn('<noscript><img', head)
            self.assertIn('www.facebook.com/tr?id=1113575654229940&amp;ev=PageView', s.split('<body>')[1])

    def test_inquiry_open_and_click_are_not_reported_as_leads(self):
        for name in ('core.js', 'inquire.js'):
            self.assertNotRegex((ROOT / 'assets/js' / name).read_text(), r"fbq\([^;]*['\"]Lead['\"]")

    def test_privacy_discloses_advertising_tracking(self):
        s = (ROOT / 'privacy/index.html').read_text()
        self.assertIn('Meta Pixel', s)
        self.assertIn('first-party cookies', s)
        self.assertNotIn('It runs no analytics', s)
        self.assertNotIn('It runs no advertising tags', s)
