import unittest

from calc import divide, percent


class CalcTest(unittest.TestCase):
    def test_divide(self):
        self.assertEqual(divide(10, 4), 2.5)

    def test_divide_by_zero(self):
        with self.assertRaises(ValueError):
            divide(1, 0)

    def test_percent(self):
        self.assertAlmostEqual(percent(1, 3), 33.33, places=2)
