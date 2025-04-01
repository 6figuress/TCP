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
├── patch/       # Patch for ComfyUI
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

### ComfyUI Installation Steps

As the patched ComfyUI Docker image is not publicly available, the following steps are provided to build and run the patched ComfyUI container:

1. Clone the ComfyUI Docker project:
```bash
git clone https://github.com/YanWenKun/ComfyUI-Docker
cd ComfyUI-Docker
```

2. Create a storage directory:
```bash
mkdir -p storage
```

3. Run the ComfyUI container:
```bash
docker run -it --rm \
  --name comfy3d-pt25 \
  --gpus all \
  -p 8188:8188 \
  -v "$(pwd)"/storage:/root \
  -e CLI_ARGS="" \
  yanwk/comfyui-boot:comfy3d-pt25
```

4. Replace the server script:
```bash
# In another terminal
docker cp /path/to/TCP/patch/server.py comfy3d-pt25:/root/user-scripts/server.py
```

5. Install Custom Nodes:
   - Access the ComfyUI web interface at `http://localhost:8188`
   - Navigate to the Manager tab
   - Install [ComfyUI-Paint3D-Nodes](https://github.com/6figuress/ComfyUI-Paint3D-Nodes/tree/master)
   - Install all required dependent custom nodes as specified in the repository

6. Install Required Models:
   - Follow the model installation guide at [ComfyUI-Paint3D-Nodes](https://github.com/6figuress/ComfyUI-Paint3D-Nodes/tree/master)
   - Place the models in the appropriate directories as specified

7. Restart the container:
```bash
docker restart comfy3d-pt25
```

### Verification
- Access `http://localhost:8188` to ensure the ComfyUI server is running
- Check that Paint3D nodes are available in the node list
- Verify that all required models are properly loaded

### Troubleshooting
- If custom nodes aren't visible, check the ComfyUI console for installation errors
- Ensure all required models are properly downloaded and placed in the correct directories
- Check Docker logs: `docker logs comfy3d-pt25`
