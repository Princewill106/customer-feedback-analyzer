import csv
import unittest

import main


class FeedbackTests(unittest.TestCase):
    def test_negation(self):
        self.assertLess(main.sentiment("not good"), 0)
        self.assertGreater(main.sentiment("really great and friendly"), 0)

    def test_delivery_is_top_issue(self):
        _, summary = main.analyse(list(csv.DictReader(open("sample_feedback.csv"))))
        self.assertEqual(summary[0]["theme"], "delivery")


if __name__ == "__main__":
    unittest.main()
