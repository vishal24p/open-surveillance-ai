import tempfile
import unittest
from pathlib import Path

from surveillance.config import get_droidcam_index, get_person_confidence


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


class GetPersonConfidenceTests(unittest.TestCase):
    def test_env_file_confidence_is_used(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env_path = Path(directory) / ".env"
            env_path.write_text("PERSON_CONFIDENCE=0.80\n", encoding="utf-8")

            self.assertEqual(get_person_confidence(env_path), 0.80)

    def test_missing_confidence_is_rejected_without_a_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            env_path = Path(directory) / ".env"
            env_path.write_text("DROIDCAM_INDEX=1\n", encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "PERSON_CONFIDENCE is missing"):
                get_person_confidence(env_path)

    def test_invalid_confidence_is_rejected(self) -> None:
        for value in ("sheet", "nan", "inf", "-0.1", "1.1"):
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory:
                env_path = Path(directory) / ".env"
                env_path.write_text(f"PERSON_CONFIDENCE={value}\n", encoding="utf-8")

                with self.assertRaisesRegex(RuntimeError, "PERSON_CONFIDENCE"):
                    get_person_confidence(env_path)


if __name__ == "__main__":
    unittest.main()
