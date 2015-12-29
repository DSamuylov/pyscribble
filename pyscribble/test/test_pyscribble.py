import unittest
import numpy as np

from ..main import line_pass_square
from ..main import line_pass_two_points_2d
from ..main import pixel_centers_2d


class TestMain(unittest.TestCase):

    def test_line_pass_two_points_2d(self):
        p1 = [8, 3]
        p2 = [8, 4]
        par = line_pass_two_points_2d(p1, p2)
        self.assertTrue(np.allclose(par, [1, 0, -8]))

    def test_line_pass_square_1(self):
        p1 = [-1., -1.]
        p2 = [1., 1.]
        pass_ = line_pass_square([0, 0], line_pass_two_points_2d(p1, p2))
        self.assertTrue(pass_)

    def test_line_pass_square_2(self):
        p1 = [0., 3.]
        p2 = [4., 3.]
        pass_ = line_pass_square([0, 0], line_pass_two_points_2d(p1, p2))
        self.assertFalse(pass_)

    def test_line_pass_square_3(self):
        p1 = [9, 21]
        p2 = [9, 22]
        pass_ = line_pass_square([9, 21], line_pass_two_points_2d(p1, p2))
        self.assertTrue(pass_)

    def test_line_pass_square_4(self):
        p1 = [3, 8]
        p2 = [4, 8]
        pass_ = line_pass_square([4, 8], line_pass_two_points_2d(p1, p2))
        self.assertTrue(pass_)

    def test_pixel_centers_2d_1(self):
        arr = pixel_centers_2d(0, 0, 0, 3)
        arr_ = np.array([[0, 0], [0, 1], [0, 2], [0, 3]])
        self.assertTrue(np.allclose(arr, arr_))

    def test_pixel_centers_2d_2(self):
        arr = pixel_centers_2d(0, 0, 3, 0)
        arr_ = np.array([[0, 3], [0, 2], [0, 1], [0, 0]])
        self.assertTrue(np.allclose(arr, arr_))

if __name__ == '__main__':
    unittest.main()
