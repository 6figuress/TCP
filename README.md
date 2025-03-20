[![codecov](https://codecov.io/gh/6figuress/TCP/branch/main/graph/badge.svg?token=W25GRHWTS0)](https://codecov.io/gh/6figuress/TCP)

# 3D Model Texturing API

This API provides a service to apply AI-generated textures to 3D models using ComfyUI as a backend. It processes text prompts to generate textures and returns textured 3D models in GLB format.

## Features

- Text-to-texture generation using AI
- Automatic 3D model texturing
- GLB format conversion
- Websocket-based execution monitoring
- Temporary file management
- Base64 encoded response for easy client-side handling

## Prerequisites

- Python 3.10 or higher
- uv (Python package installer)
- ComfyUI server running on the network
- Blender (used for GLB conversion)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/6figuress/TCP
cd TCP
```

2. Setup project and install dependencies using uv:
```bash
uv sync
```

## Configuration

1. Ensure your ComfyUI server is running and accessible
2. Update the `server_address` in `wrapper.py` if needed (default: "192.168.91.13:8188")
3. Place your workflow JSON file in the `workflows` directory as `paint3d.json`

## Usage

### Starting the Server

```bash
uv run server.py
```

The server will start on `http://0.0.0.0:5000` by default.

### API Endpoints

#### POST /api/texture

Generate a textured 3D model from a prompt.

**Request Body:**
```json
{
    "user_prompt": "Your texture description here"
}
```

**Response:**
```json
{
    "status": "success",
    "message": "Generation completed",
    "user_prompt": "Your texture description here",
    "glb_data": "base64_encoded_glb_data"
}
```

## Testing

Run the test suite using pytest:
```bash
uv run pytest
```

## Error Handling

The API includes comprehensive error handling for:
- Missing parameters
- Workflow file issues
- Execution failures
- File processing errors
- Network communication issues

## Development

The codebase is organized as follows:
- `src/wrapper.py`: Main API implementation
- `tests/wrapper_test.py`: Test suite
- `workflows/`: Directory for ComfyUI workflow configurations
