import unittest

from calc import clamp, divide, percent


class CalcTest(unittest.TestCase):
    def test_divide(self):
        self.assertEqual(divide(10, 4), 2.5)

    def test_percent(self):
        self.assertEqual(percent(1, 3), 33.33333333333333)

    def test_clamp(self):
        self.assertEqual(clamp(15, 0, 10), 10)
