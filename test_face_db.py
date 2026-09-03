import tempfile
import unittest

import numpy as np

import face_db


class FaceDatabaseTest(unittest.TestCase):
    def test_round_trip_and_safe_name(self):
        with tempfile.TemporaryDirectory() as directory:
            face_db.DB_DIR = directory
            face_db.refresh_cache()

            self.assertEqual(face_db.add_face("Test User", np.array([1.0, 0.0])), 1)
            self.assertEqual(face_db.recognize_face(np.array([1.0, 0.0]))[0], "Test User")
            with self.assertRaises(ValueError):
                face_db.add_face("../outside", np.array([1.0, 0.0]))
            self.assertTrue(face_db.delete_person("Test User"))


if __name__ == "__main__":
    unittest.main()
