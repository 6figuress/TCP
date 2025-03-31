import base64
import json
import os
import tempfile
import uuid
from urllib import request

import websocket
from flask import Flask, Response, jsonify
from flask import request as flask_request
from flask_cors import CORS


class Wrapper:
    def __init__(self) -> None:
        self.app: Flask = Flask(__name__)
        # Add CORS support
        CORS(
            self.app,
            resources={
                r"/api/*": {
                    "origins": [
                        "http://localhost:5173",
                        "http://127.0.0.1:5173",
                        "http://localhost:8888",
                        "http://127.0.0.1:8888",
                        "http://frontend:8888"
                    ],
                    "methods": ["POST", "OPTIONS"],
                    "allow_headers": ["Content-Type", "Accept"],
                }
            },
        )

        self.server_address = "192.168.91.13:8188"
        self.llm_address = "192.168.91.12:11434"

        # Load the workflow JSON file
        workflow_path: str = os.path.join(
            "workflows", "paint3d-optimized-pretrained.json"
        )
        # workflow_path: str = os.path.join("workflows", "paint3d-optimized.json")
        try:
            with open(workflow_path, "r") as f:
                self.workflow = json.load(f)
        except Exception as e:
            print(f"Error loading workflow file: {e}")
            self.workflow = None

        @self.app.route("/api/texture", methods=["POST", "OPTIONS"])
        def texture():
            """Mesh texturing endpoint that interfaces with ComfyUI"""
            # Handle OPTIONS request for CORS preflight
            if flask_request.method == "OPTIONS":
                return jsonify({"status": "ok"})

            try:
                # Create unique context for this request
                request_context = self.create_request_context()

                # Get request data
                data = flask_request.get_json()
                user_prompt: str = data.get("user_prompt")

                # Validate input
                if not user_prompt:
                    return jsonify(
                        {"error": "Missing required parameters"}
                    ), 400
                if self.workflow is None:
                    return jsonify({"error": "Workflow file not loaded"}), 500

                # Create a copy of the workflow to modify
                prompt = self.workflow.copy()

                # Update the prompt text
                prompt["4"]["inputs"]["text"] = (
                    f"{user_prompt}, painting, high quality, colorful"
                )
                print(f"Setting prompt text: {user_prompt}")

                # Update the seed
                prompt["9"]["inputs"]["seed"] = str(uuid.uuid4().int % (2**32))

                # Step 1: Process the prompt and wait for completion
                print("Step 1: Processing prompt...")
                success = self.process_prompt(prompt, request_context)

                if not success:
                    return jsonify({"error": "Prompt execution failed"}), 500

                # Step 2: Download and convert files
                print("Step 2: Processing files...")
                try:
                    glb_data = self.process_and_convert_to_glb(request_context)
                    glb_base64 = base64.b64encode(glb_data).decode("utf-8")
                except Exception as e:
                    return jsonify(
                        {"error": f"File processing failed: {str(e)}"}
                    ), 500

                self.cleanup_context(request_context)

                # Step 3: Return response
                return jsonify(
                    {
                        "status": "success",
                        "message": "Generation completed",
                        "user_prompt": user_prompt,
                        "glb_data": glb_base64,
                    }
                )

            except Exception as e:
                print(f"Error in texture endpoint: {str(e)}")
                return jsonify({"error": str(e)}), 500

        @self.app.route("/api/adventure", methods=["POST", "OPTIONS"])
        def adventure():
            if flask_request.method == "OPTIONS":
                return jsonify({"status": "ok"})

            try:
                data = flask_request.get_json()
                user_prompt = data.get("user_prompt")

                if not user_prompt:
                    return jsonify({"error": "Missing user prompt"}), 400

                system_prompt = """You are a masterful fantasy storyteller, crafting immersive, vivid, and emotionally compelling adventures. Your task is to generate an engaging fantasy story based on the provided main character's name. The story should be richly descriptive, full of mystery, danger, and wonder, drawing the reader into a world filled with unique landscapes, magical elements, and intriguing characters.

                Guidelines:
                - **Character Development:** Create a compelling main character with strengths, weaknesses, and a sense of growth throughout the journey.
                - **Supporting Cast:** Introduce intriguing allies, mentors, rivals, and villains who interact meaningfully with the protagonist.
                - **World-Building:** Describe breathtaking landscapes, ancient ruins, hidden realms, and mystical creatures. Use all five senses to make the world feel alive.
                - **Mystery & Wonder:** Weave a sense of the unknown—enigmatic prophecies, lost civilizations, hidden artifacts, or secrets waiting to be uncovered.
                - **Danger & Conflict:** The journey should include perilous trials—treacherous landscapes, cunning foes, and moral dilemmas that test the hero's resolve.
                - **Narrative Flow:** Maintain an engaging pace with moments of tension, triumph, and introspection. Every chapter should advance the adventure meaningfully.

                Your goal is to **captivate and immerse** the reader, making them feel as if they are living the adventure alongside the protagonist."""

                def generate():
                    try:
                        url = f"http://{self.llm_address}/api/generate"
                        data = {
                            "model": "mistral",
                            "prompt": f"System: {system_prompt}\n\nHuman: {user_prompt}\n\nAssistant:",
                            "stream": True,
                        }

                        # Make request using urllib
                        req = request.Request(
                            url,
                            data=json.dumps(data).encode("utf-8"),
                            headers={"Content-Type": "application/json"},
                        )

                        with request.urlopen(req) as response:
                            for line in response:
                                if line:
                                    json_response = json.loads(line.decode())
                                    if "response" in json_response:
                                        yield f"data: {json.dumps({'text': json_response['response']})}\n\n"

                    except Exception as e:
                        yield f"data: {json.dumps({'error': str(e)})}\n\n"

                return Response(
                    generate(),
                    mimetype="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Headers": "Content-Type",
                    },
                )

            except Exception as e:
                return jsonify({"error": str(e)}), 500

    def cleanup_context(self, context):
        """Clean up request-specific resources"""
        try:
            if os.path.exists(context["temp_dir"]):
                import shutil

                shutil.rmtree(context["temp_dir"])
        except Exception as e:
            print(f"Error cleaning up context: {e}")

    def create_request_context(self):
        """Create a unique context for each request"""
        return {"temp_dir": tempfile.mkdtemp(), "client_id": str(uuid.uuid4())}

    def queue_prompt(self, prompt, context):
        """Queue a prompt to ComfyUI"""
        p = {"prompt": prompt, "client_id": context["client_id"]}
        data = json.dumps(p).encode("utf-8")
        req = request.Request(f"http://{self.server_address}/prompt", data=data)
        return json.loads(request.urlopen(req).read())

    def verify_execution(self, ws, prompt_id):
        """Verify that the prompt execution completed successfully"""
        execution_success = False
        final_node = False

        while True:
            out = ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                print(f"Received message: {message}")

                if message["type"] == "executing":
                    data = message["data"]
                    if data["prompt_id"] == prompt_id:
                        if data["node"] is None:
                            print("Final node reached")
                            final_node = True
                        else:
                            print(f"Processing node: {data['node']}")

                elif message["type"] == "execution_success":
                    data = message["data"]
                    if data["prompt_id"] == prompt_id:
                        print("Execution success received")
                        execution_success = True

                elif message["type"] == "execution_error":
                    data = message["data"]
                    if data["prompt_id"] == prompt_id:
                        print(
                            f"Execution error: {data.get('error', 'Unknown error')}"
                        )
                        return False

                # Only return True when both conditions are met
                if execution_success and final_node:
                    print("Workflow completely finished")
                    return True

    def download_files(self, context):
        """Download the required files from the server"""
        # files = {
        #     "obj": "base_duck.obj",
        #     "mtl": "base_duck.mtl",
        #     "texture": "albedo.png",
        # }
        files = {
            "obj": "final_rubber_duck.obj",
            "mtl": "final_rubber_duck.mtl",
            "texture": "albedo.png",
        }

        file_paths = {}

        for file_type, filename in files.items():
            try:
                url = f"http://{self.server_address}/download/{filename}"
                response = request.urlopen(url)

                # Save to temporary directory
                save_path = os.path.join(context["temp_dir"], filename)

                with open(save_path, "wb") as f:
                    f.write(response.read())

                file_paths[file_type] = save_path

            except Exception as e:
                print(f"Error downloading {filename}: {e}")
                file_paths[file_type] = None

        return file_paths

    def process_and_convert_to_glb(self, context):
        """Alternative method that uses external shell script to convert OBJ to GLB"""
        files = self.download_files(context)

        try:
            # Call the external conversion script
            obj_path = files["obj"]
            conversion_script = "scripts/obj_gltf.sh"

            # Make sure the script is executable
            os.chmod(conversion_script, 0o755)

            # Run the conversion script with temp directory
            import subprocess

            result = subprocess.run(
                [conversion_script, obj_path, context["temp_dir"]],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                raise Exception(f"Conversion script failed: {result.stderr}")

            gltf_path = os.path.join(
                context["temp_dir"],
                os.path.splitext(os.path.basename(obj_path))[0] + ".glb",
            )

            # Read the generated GLTF file
            with open(gltf_path, "rb") as f:
                gltf_data = f.read()

            return gltf_data

        except Exception as e:
            print(f"Detailed error in GLTF conversion: {str(e)}")
            import traceback

            print(f"Traceback: {traceback.format_exc()}")
            raise Exception(f"Error converting to GLTF: {str(e)}")

    def process_prompt(self, prompt, context):
        """Process the prompt and verify execution"""
        try:
            # First, queue the prompt and get prompt_id
            print("Queueing prompt...")
            queue_response = self.queue_prompt(prompt, context)
            prompt_id = queue_response["prompt_id"]
            print(f"Prompt queued with ID: {prompt_id}")

            # Then connect to websocket to monitor execution
            ws = websocket.WebSocket()
            ws.settimeout(300)  # 5 minutes timeout
            ws.connect(
                f"ws://{self.server_address}/ws?clientId={context['client_id']}"
            )

            # Wait for execution to complete
            print("Waiting for execution to complete...")
            while True:
                out = ws.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    print(f"Received message: {message}")

                    # Check if this message is relevant to our prompt
                    if "data" in message and "prompt_id" in message["data"]:
                        if message["data"]["prompt_id"] == prompt_id:
                            # Handle different message types
                            if message["type"] == "execution_start":
                                print("Execution started")
                            elif message["type"] == "executing":
                                node = message["data"].get("node")
                                if node:
                                    print(f"Processing node: {node}")
                                else:
                                    print("Final node reached")
                            elif message["type"] == "execution_error":
                                error = message["data"].get(
                                    "error", "Unknown error"
                                )
                                print(f"Execution failed: {error}")
                                return False
                            elif message["type"] == "execution_success":
                                print("Execution completed successfully")
                                return True

        except Exception as e:
            print(f"Error in process_prompt: {str(e)}")
            return False
        finally:
            try:
                ws.close()
            except:
                pass

    def run(self, host="0.0.0.0", port=5000, debug=True):
        self.app.run(host=host, port=port, debug=debug)
