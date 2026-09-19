import tempfile
import unittest
from pathlib import Path

from surveillance.camera import get_droidcam_index


class GetDroidcamIndexTests(unittest.TestCase):
    def test_env_file_index_is_used(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env_path = Path(directory) / ".env"
            env_path.write_text("DROIDCAM_INDEX=1\n", encoding="utf-8")

            self.assertEqual(get_droidcam_index(env_path), 1)

    def test_missing_env_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env_path = Path(directory) / ".env"

            with self.assertRaisesRegex(RuntimeError, ".env"):
                get_droidcam_index(env_path)

    def test_missing_index_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env_path = Path(directory) / ".env"
            env_path.write_text("OTHER_SETTING=1\n", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "DROIDCAM_INDEX"):
                get_droidcam_index(env_path)

    def test_non_number_index_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env_path = Path(directory) / ".env"
            env_path.write_text("DROIDCAM_INDEX=camera\n", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "DROIDCAM_INDEX"):
                get_droidcam_index(env_path)

    def test_negative_index_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env_path = Path(directory) / ".env"
            env_path.write_text("DROIDCAM_INDEX=-1\n", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "DROIDCAM_INDEX"):
                get_droidcam_index(env_path)


if __name__ == "__main__":
    unittest.main()
