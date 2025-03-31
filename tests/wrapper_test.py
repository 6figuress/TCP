import json
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
    assert wrapper.server_address == "192.168.91.13:8188"
    assert wrapper.llm_address == "192.168.91.12:11434"


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
        response = client.post(
            "/api/texture", json={"user_prompt": "test prompt"}
        )
        assert response.status_code == 500
        assert json.loads(response.data)["error"] == "Workflow file not loaded"


@patch("websocket.WebSocket")
def test_process_prompt_execution_error(mock_ws):
    """Test handling of execution errors in process_prompt"""
    wrapper = Wrapper()
    context = {
        "temp_dir": "mock_dir"
    }  # Mock context instead of creating real directory

    ws_instance = Mock()
    mock_ws.return_value = ws_instance

    ws_instance.recv.return_value = json.dumps(
        {
            "type": "execution_error",
            "data": {"prompt_id": "test-id", "error": "Test error message"},
        }
    )

    success = wrapper.process_prompt({"test": "prompt"}, context)
    assert not success


@patch("urllib.request.urlopen")
def test_download_files_error(mock_urlopen):
    """Test handling of file download errors"""
    wrapper = Wrapper()
    context = {"temp_dir": "mock_dir"}  # Mock context
    mock_urlopen.side_effect = Exception("Download failed")

    file_paths = wrapper.download_files(context)
    assert all(path is None for path in file_paths.values())


def test_run_method():
    """Test run method parameters"""
    wrapper = Wrapper()
    with patch.object(wrapper.app, "run") as mock_run:
        wrapper.run(host="127.0.0.1", port=8080, debug=False)
        mock_run.assert_called_once_with(
            host="127.0.0.1", port=8080, debug=False
        )


@patch("os.path.exists")
@patch("shutil.rmtree")
def test_cleanup(mock_rmtree, mock_exists):
    """Test context cleanup"""
    wrapper = Wrapper()
    context = {"temp_dir": "mock_dir"}

    mock_exists.return_value = True
    wrapper.cleanup_context(context)

    mock_rmtree.assert_called_once_with("mock_dir")
