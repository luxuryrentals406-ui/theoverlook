#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""tools/repetition.py — the no-repeating rule. Run: python3 -m unittest tools/tests/test_repetition.py"""
import os, sys, tempfile, unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import repetition as R


def page(body):
    f = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8")
    f.write(f"<html><head><title>x</title></head><body><header>Weddings 200 guests</header>"
            f"<main>{body}</main><footer>parking for 75 cars</footer></body></html>")
    f.close()
    return R.page_text(f.name)


class Counting(unittest.TestCase):
    def test_square_feet_and_amps_are_not_guest_counts(self):
        t = page("<p>A 3,200 sq ft pavilion and 200 AMP service for 200 guests.</p>")
        self.assertEqual(R.offer_counts(t)["200 guests"], 1)

    def test_chrome_reviews_and_hidden_duplicates_do_not_count(self):
        t = page('<blockquote>The built-in bar was great</blockquote>'
                 '<div class="mq__run" aria-hidden="true"><span>One group at a time</span></div>'
                 '<p>The built-in bar is permanent.</p>')
        c = R.offer_counts(t)
        self.assertEqual(c["built-in bar"], 1)
        self.assertEqual(c["one group at a time"], 0)
        self.assertEqual(c["parking for 75"], 0)          # only in the footer

    def test_company_name_is_not_a_helicopter_mention(self):
        t = page("<p>Arrivals through WestSlope Helicopters. A helicopter transfer.</p>")
        self.assertEqual(R.offer_counts(t)["helicopter"], 1)


class Budget(unittest.TestCase):
    def test_third_mention_fails_and_core_promise_gets_three(self):
        t = page("<p>Parking for 75 cars.</p><p>Room for 75 cars.</p><p>75 cars again.</p>"
                 "<p>One group.</p><p>one group.</p><p>one group.</p>")
        over = {k: (n, cap) for k, n, cap in R.over_budget(t)}
        self.assertEqual(over["parking for 75"], (3, 2))
        self.assertNotIn("one group at a time", over)

    def test_shared_sentences_across_pages(self):
        a = page("<p>The estate is booked for one group at a time, all week long.</p>")
        b = page("<p>The estate is booked for one group at a time, all week long.</p><p>Other.</p>")
        self.assertEqual(len(R.shared_sentences({"a.html": a, "b.html": b})), 1)


if __name__ == "__main__":
    unittest.main()
