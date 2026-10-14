"""Test runtime."""

import unittest

from PIL import Image

from judge.runtime import diff_images

BLACK = (0, 0, 0, 255)


def make_image(*pixels: tuple[int, int, tuple[int, int, int, int]]) -> Image.Image:
    image = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
    for x, y, colour in pixels:
        image.putpixel((x, y), colour)
    return image


class TestDiffImages(unittest.TestCase):
    """diff_images TestCase."""

    def test_empty_images(self):
        self.assertEqual(diff_images(make_image(), make_image()), (0, 0, 0))

    def test_identical_images(self):
        image = make_image((0, 0, BLACK), (1, 1, BLACK), (2, 2, BLACK))
        self.assertEqual(diff_images(image, image.copy()), (3, 3, 3))

    def test_disjoint_drawings(self):
        submission = make_image((0, 0, BLACK), (1, 0, BLACK))
        solution = make_image((2, 3, BLACK), (3, 3, BLACK), (3, 2, BLACK))
        self.assertEqual(diff_images(submission, solution), (0, 5, 3))

    def test_overlap(self):
        submission = make_image((0, 0, BLACK), (1, 0, BLACK), (2, 0, BLACK))
        solution = make_image((1, 0, BLACK), (2, 0, BLACK), (3, 0, BLACK))
        self.assertEqual(diff_images(submission, solution), (2, 4, 3))

    def test_alpha_only_difference(self):
        submission = make_image((0, 0, (255, 0, 0, 255)), (1, 0, BLACK))
        solution = make_image((0, 0, (255, 0, 0, 128)), (1, 0, BLACK))
        self.assertEqual(diff_images(submission, solution), (1, 2, 2))

    def test_colour_with_zero_alpha_counts(self):
        submission = make_image((0, 0, (10, 0, 0, 0)))
        solution = make_image()
        self.assertEqual(diff_images(submission, solution), (0, 1, 0))
        self.assertEqual(diff_images(submission, submission.copy()), (1, 1, 1))

    def test_returns_plain_ints(self):
        result = diff_images(make_image((0, 0, BLACK)), make_image())
        self.assertTrue(all(type(value) is int for value in result))
