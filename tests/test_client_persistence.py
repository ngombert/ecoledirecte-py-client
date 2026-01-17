"""
Tests for Client persistence mechanisms (client.py).
"""

import pytest
import json
import os

from ecoledirecte_py_client import Client


@pytest.mark.asyncio
class TestClientPersistence:
    """Tests for device token and QCM cache persistence."""

    async def test_device_token_save(self, temp_files):
        """Test saving device tokens to file."""
        client = Client(**temp_files)

        cn = "test_cn_token"
        cv = "test_cv_token"

        client._save_device_tokens(cn, cv)

        # Verify file was created and contains correct data
        assert os.path.exists(temp_files["device_file"])

        with open(temp_files["device_file"], "r") as f:
            data = json.load(f)

        assert data["cn"] == cn
        assert data["cv"] == cv

        await client.close()

    async def test_device_token_load(self, temp_files):
        """Test loading device tokens from file."""
        # Pre-create device file
        device_data = {"cn": "saved_cn", "cv": "saved_cv"}
        with open(temp_files["device_file"], "w") as f:
            json.dump(device_data, f)

        client = Client(**temp_files)

        # Tokens should be loaded when requested
        cn, cv = client._load_device_tokens()
        assert cn == "saved_cn"
        assert cv == "saved_cv"

        await client.close()

    async def test_device_token_disabled(self, tmp_path):
        """Test that device persistence can be disabled."""
        client = Client(device_file=None, qcm_file=str(tmp_path / "qcm.json"))

        # Try to save tokens
        client._save_device_tokens("cn", "cv")

        # No file should be created
        # Client should handle this gracefully

        await client.close()

    async def test_qcm_cache_save(self, temp_files):
        """Test saving QCM answers to cache."""
        client = Client(**temp_files)

        question = "Test question?"
        answer = "Test answer"

        client._save_qcm_answer(question, answer)

        # Verify file was created
        assert os.path.exists(temp_files["qcm_file"])

        with open(temp_files["qcm_file"], "r") as f:
            data = json.load(f)

        assert question in data
        assert answer in data[question]

        await client.close()

    async def test_qcm_cache_load(self, temp_files):
        """Test loading QCM cache from file."""
        # Pre-create QCM cache
        qcm_data = {
            "Question 1?": ["Answer 1"],
            "Question 2?": ["Answer 2a", "Answer 2b"],
        }
        with open(temp_files["qcm_file"], "w") as f:
            json.dump(qcm_data, f)

        client = Client(**temp_files)

        # Cache should be loaded
        assert client._load_qcm_cache() == qcm_data

        await client.close()

    async def test_qcm_cache_append(self, temp_files):
        """Test appending new answers to existing QCM cache."""
        # Pre-create QCM cache with existing answer
        qcm_data = {"Question?": ["Answer1"]}
        with open(temp_files["qcm_file"], "w") as f:
            json.dump(qcm_data, f)

        client = Client(**temp_files)

        # Save a new answer for the same question
        client._save_qcm_answer("Question?", "Answer2")

        # Load and verify both answers are present
        with open(temp_files["qcm_file"], "r") as f:
            data = json.load(f)

        assert "Answer1" in data["Question?"]
        assert "Answer2" in data["Question?"]

        await client.close()

    async def test_qcm_cache_disabled(self, tmp_path):
        """Test that QCM cache can be disabled."""
        client = Client(device_file=str(tmp_path / "device.json"), qcm_file=None)

        # Try to save QCM answer
        client._save_qcm_answer("Question?", "Answer")

        # Should handle gracefully without error

        await client.close()

    async def test_persistence_with_missing_files(self, tmp_path):
        """Test that client handles missing persistence files gracefully."""
        # Point to non-existent files
        device_file = str(tmp_path / "nonexistent_device.json")
        qcm_file = str(tmp_path / "nonexistent_qcm.json")

        client = Client(device_file=device_file, qcm_file=qcm_file)

        # Should initialize without errors
        assert client.cn is None
        assert client.cv is None
        assert client._load_qcm_cache() == {}

        await client.close()

    async def test_persistence_with_invalid_json(self, temp_files):
        """Test handling of corrupted JSON files."""
        # Create invalid JSON file
        with open(temp_files["device_file"], "w") as f:
            f.write("{ invalid json }")

        client = Client(**temp_files)

        # Should handle gracefully without crashing
        # Might log error but should not raise exception

        await client.close()
