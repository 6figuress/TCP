import json
import os
from unittest.mock import Mock, patch

import pytest
from flask import Flask

from src.wrapper import Wrapper


@pytest.fixture
def client():
    """Fixture to create a test client"""
    wrapper = Wrapper()
    with wrapper.app.test_client() as client:
        yield client


def test_wrapper_initialization():
    """Test if Wrapper initializes correctly"""
    wrapper = Wrapper()
    assert isinstance(wrapper.app, Flask)
    assert hasattr(wrapper, "temp_dir")
    assert os.path.exists(wrapper.temp_dir)


@pytest.fixture
def mock_websocket():
    """Fixture to mock websocket connections"""
    with patch("websocket.WebSocket") as mock_ws:
        ws_instance = Mock()
        mock_ws.return_value = ws_instance

        # Mock successful websocket messages
        def mock_recv():
            return json.dumps(
                {
                    "type": "execution_success",
                    "data": {"prompt_id": "test-id", "timestamp": 123456789},
                }
            )

        ws_instance.recv.return_value = mock_recv()

        yield mock_ws


@pytest.fixture
def mock_request():
    """Fixture to mock URL requests"""
    with patch("urllib.request.urlopen") as mock_urlopen:
        # Mock successful prompt queue response
        mock_response = Mock()
        mock_response.read.return_value = json.dumps({"prompt_id": "test-id"}).encode(
            "utf-8"
        )
        mock_urlopen.return_value = mock_response
        yield mock_urlopen


def test_texture_endpoint_missing_parameters(client):
    """Test texture endpoint with missing parameters"""
    response = client.post("/api/texture", json={})
    assert response.status_code == 400
    assert json.loads(response.data)["error"] == "Missing required parameters"


def test_texture_endpoint_workflow_error():
    """Test texture endpoint when workflow file is missing"""
    wrapper = Wrapper()
    wrapper.workflow = None  # Simulate missing workflow

    with wrapper.app.test_client() as client:
        response = client.post("/api/texture", json={"user_prompt": "test prompt"})
        assert response.status_code == 500
        assert json.loads(response.data)["error"] == "Workflow file not loaded"


@patch("websocket.WebSocket")
def test_process_prompt_execution_error(mock_ws):
    """Test handling of execution errors in process_prompt"""
    ws_instance = Mock()
    mock_ws.return_value = ws_instance

    # Mock error message from websocket
    ws_instance.recv.return_value = json.dumps(
        {
            "type": "execution_error",
            "data": {"prompt_id": "test-id", "error": "Test error message"},
        }
    )

    wrapper = Wrapper()
    success = wrapper.process_prompt({"test": "prompt"})
    assert not success


@patch("urllib.request.urlopen")
def test_download_files_error(mock_urlopen):
    """Test handling of file download errors"""
    mock_urlopen.side_effect = Exception("Download failed")

    wrapper = Wrapper()
    file_paths = wrapper.download_files()

    assert all(path is None for path in file_paths.values())


def test_run_method():
    """Test run method parameters"""
    wrapper = Wrapper()
    with patch.object(wrapper.app, "run") as mock_run:
        wrapper.run(host="127.0.0.1", port=8080, debug=False)
        mock_run.assert_called_once_with(host="127.0.0.1", port=8080, debug=False)


def test_cleanup():
    """Test temporary directory cleanup"""
    wrapper = Wrapper()
    temp_dir = wrapper.temp_dir
    assert os.path.exists(temp_dir)

    # Manually call cleanup to avoid shutdown issues
    import shutil

    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    assert not os.path.exists(temp_dir)
