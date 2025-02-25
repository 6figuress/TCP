import json
from unittest.mock import patch

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


def test_texture_endpoint_missing_parameters(client):
    """Test texture endpoint with missing parameters"""

    # test with empty request
    response = client.post("/api/texture", json={})
    assert response.status_code == 400
    assert json.loads(response.data)["error"] == "Missing required parameters"

    # test with only mesh_filepath
    response = client.post("/api/texture", json={"mesh_filepath": "test.obj"})
    assert response.status_code == 400
    assert json.loads(response.data)["error"] == "Missing required parameters"

    # test with only user_prompt
    response = client.post("/api/texture", json={"user_prompt": "test prompt"})
    assert response.status_code == 400
    assert json.loads(response.data)["error"] == "Missing required parameters"


@patch("src.wrapper.run")
def test_texture_endpoint_successful_request(mock_run, client):
    """Test texture endpoint with valid parameters"""

    # mock successful command execution
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Success output"

    test_data = {"mesh_filepath": "test.obj", "user_prompt": "test prompt"}

    response = client.post("/api/texture", json=test_data)
    assert response.status_code == 200
    assert json.loads(response.data)["output"] == "Success output"


@patch("src.wrapper.run")
def test_texture_endpoint_command_failure(mock_run, client):
    """Test texture endpoint when command fails"""

    # mock failed command execution
    mock_run.return_value.returncode = 1
    mock_run.return_value.stderr = "Error output"

    test_data = {"mesh_filepath": "test.obj", "user_prompt": "test prompt"}

    response = client.post("/api/texture", json=test_data)
    assert response.status_code == 500
    assert json.loads(response.data)["error"] == "Error output"


@patch("src.wrapper.run")
def test_texture_endpoint_with_extra_parameters(mock_run, client):
    """Test texture endpoint with additional parameters"""

    # mock successful command execution
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Success output"

    test_data = {
        "mesh_filepath": "test.obj",
        "user_prompt": "test prompt",
        "resolution": "512",
        "quality": "high",
    }

    response = client.post("/api/texture", json=test_data)
    assert response.status_code == 200

    # Verify the command was called with extra parameters
    mock_run.assert_called_once()
    cmd_args = mock_run.call_args[0][0]
    assert "--resolution 512" in cmd_args
    assert "--quality high" in cmd_args


@patch("src.wrapper.run")
def test_texture_endpoint_exception_handling(mock_run, client):
    """Test texture endpoint exception handling"""

    # mock an exception during command execution
    mock_run.side_effect = Exception("Test exception")

    test_data = {"mesh_filepath": "test.obj", "user_prompt": "test prompt"}

    response = client.post("/api/texture", json=test_data)
    assert response.status_code == 500
    assert json.loads(response.data)["error"] == "Test exception"


def test_run_method():
    """Test run method parameters"""

    wrapper = Wrapper()
    with patch.object(wrapper.app, "run") as mock_run:
        wrapper.run(host="127.0.0.1", port=8080, debug=False)
        mock_run.assert_called_once_with(host="127.0.0.1", port=8080, debug=False)
