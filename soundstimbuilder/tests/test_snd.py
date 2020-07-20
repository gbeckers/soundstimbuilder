import unittest

import numpy as np

from soundstimbuilder import Snd

class TestSnd(unittest.TestCase):

    def test_numpyframes(self):
        self.assertIsInstance(Snd(frames=[1,2,3], fs=1).frames, np.ndarray)

