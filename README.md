[![codecov](https://codecov.io/gh/6figuress/TCP/graph/badge.svg?token=9M193G924T)](https://codecov.io/gh/6figuress/TCP)

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
3. Update the `llm_address` in `wrapper.py` if needed (default: "192.168.91.12:11434")
4. Place your workflow JSON file in the `workflows` directory

## Usage

### Starting the Server

```bash
uv run server.py
```

The server will start on `http://0.0.0.0:5000` by default.

## API Endpoints

### POST /api/texture

Generates a textured 3D model from a text prompt using ComfyUI.

**Request:**
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

**Error Responses:**
- `400 Bad Request`: Missing required parameters
- `500 Internal Server Error`: Workflow file not loaded or execution failed

### POST /api/adventure

Generates a fantasy story using the Mistral LLM with server-sent events (SSE).

**Request:**
```json
{
    "user_prompt": "Your story prompt here"
}
```

**Response:**
Server-sent events stream with the following format:
```json
{
    "text": "Generated story content..."
}
```

**Error Responses:**
- `400 Bad Request`: Missing user prompt
- `500 Internal Server Error`: LLM connection or processing error

## Testing and Benchmarking

### Running Tests
```bash
uv run pytest
```

### Benchmarking Script

The project includes a benchmarking script to test the texture generation with various prompts:

```bash
uv run scripts/benchmarking.py
```

The script:
- Processes a predefined list of prompts
- Saves generated GLB files
- Provides success/failure statistics
- Creates output in `benchmark_output` directory

### Visualization Script

A Blender-based visualization script is included to compare different model versions:

```bash
uv run scripts/visualization.py
```

The script:
- Compares GLB files from three different benchmark outputs
- Creates side-by-side renders
- Saves comparison images in `visualization_output` directory

Features:
- Automatic camera positioning
- Professional lighting setup

## Project Structure
```
TCP/
├── server.py               # Main entrypoint script
├── src/
│   └── wrapper.py          # API implementation
├── scripts/
│   ├── benchmarking.py     # Performance testing
│   └── visualization.py    # Blender visualization
├── tests/
│   └── wrapper_test.py     # Test suite
├── workflows/              # ComfyUI workflow configurations
└── README.md
```

The codebase is organized as follows:
- `server.py`: Main entrypoint script
- `src/wrapper.py`: API implementation
- `tests/wrapper_test.py`: Test suite
- `workflows/`: Directory for ComfyUI workflow configurations
- `scripts/`: Additional scripts for benchmarking and visualization
