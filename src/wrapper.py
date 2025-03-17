import json
import os
import uuid
import websocket
from urllib import request
import trimesh
import numpy as np
from flask import Flask, jsonify, request as flask_request
import tempfile
import base64

class Wrapper:
    def __init__(self) -> None:
        self.app: Flask = Flask(__name__)
        self.server_address = "192.168.91.13:8188"
        self.client_id = str(uuid.uuid4())
        self.temp_dir = tempfile.mkdtemp()

        # Load the workflow JSON file
        workflow_path: str = os.path.join("workflows", "paint3d.json")
        try:
            with open(workflow_path, 'r') as f:
                self.workflow = json.load(f)
        except Exception as e:
            print(f"Error loading workflow file: {e}")
            self.workflow = None

        @self.app.route("/api/texture", methods=["POST"])
        def texture():
            """
            Mesh texturing endpoint that interfaces with ComfyUI.
            """
            try:
                # Get request data
                data = flask_request.get_json()
                user_prompt: str = data.get("user_prompt")

                # Validate input
                if not user_prompt:
                    return jsonify({"error": "Missing required parameters"}), 400
                if self.workflow is None:
                    return jsonify({"error": "Workflow file not loaded"}), 500

                # Create a copy of the workflow to modify
                prompt = self.workflow.copy()

                # Update the prompt text
                if "14" in prompt:
                    prompt["14"]["inputs"]["text"] = user_prompt
                    print(f"Setting prompt text: {user_prompt}")
                else:
                    return jsonify({"error": "Invalid workflow configuration"}), 500

                # Step 1: Process the prompt and wait for completion
                print("Step 1: Processing prompt...")
                success = self.process_prompt(prompt)

                if not success:
                    return jsonify({"error": "Prompt execution failed"}), 500

                # Step 2: Download and convert files
                print("Step 2: Processing files...")
                try:
                    glb_data = self.process_and_convert_to_glb()
                    glb_base64 = base64.b64encode(glb_data).decode('utf-8')
                except Exception as e:
                    return jsonify({"error": f"File processing failed: {str(e)}"}), 500

                # Step 3: Return response
                return jsonify({
                    "status": "success",
                    "message": "Generation completed",
                    "user_prompt": user_prompt,
                    "glb_data": glb_base64
                })

            except Exception as e:
                print(f"Error in texture endpoint: {str(e)}")
                return jsonify({"error": str(e)}), 500

    def queue_prompt(self, prompt):
        """
        Queue a prompt to ComfyUI
        """
        p = {"prompt": prompt, "client_id": self.client_id}
        data = json.dumps(p).encode('utf-8')
        req = request.Request(f"http://{self.server_address}/prompt", data=data)
        return json.loads(request.urlopen(req).read())

    def verify_execution(self, ws, prompt_id, timeout=300):
        """
        Verify that the prompt execution completed successfully
        """
        import time
        start_time = time.time()
        execution_success = False
        final_node = False

        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError("Execution timed out")

            out = ws.recv()
            if isinstance(out, str):
                message = json.loads(out)
                print(f"Received message: {message}")

                if message['type'] == 'executing':
                    data = message['data']
                    if data['prompt_id'] == prompt_id:
                        if data['node'] is None:
                            print("Final node reached")
                            final_node = True
                        else:
                            print(f"Processing node: {data['node']}")

                elif message['type'] == 'execution_success':
                    data = message['data']
                    if data['prompt_id'] == prompt_id:
                        print("Execution success received")
                        execution_success = True

                elif message['type'] == 'execution_error':
                    data = message['data']
                    if data['prompt_id'] == prompt_id:
                        print(f"Execution error: {data.get('error', 'Unknown error')}")
                        return False

                # Only return True when both conditions are met
                if execution_success and final_node:
                    print("Workflow completely finished")
                    return True

    def download_files(self):
        """
        Download the required files from the server
        """
        files = {
            'obj': 'base_duck.obj',
            'mtl': 'base_duck.mtl',
            'texture': 'albedo.png'
        }

        file_paths = {}

        for file_type, filename in files.items():
            try:
                url = f"http://{self.server_address}/download/{filename}"
                response = request.urlopen(url)

                # Save to temporary directory
                save_path = os.path.join(self.temp_dir, filename)

                with open(save_path, 'wb') as f:
                    f.write(response.read())

                file_paths[file_type] = save_path

            except Exception as e:
                print(f"Error downloading {filename}: {e}")
                file_paths[file_type] = None

        return file_paths

    def process_and_convert_to_glb(self):
        """
        Download files and convert them to GLB format
        """
        # Download the files
        files = self.download_files()

        try:
            # Load the OBJ file with texture
            mesh = trimesh.load(
                files['obj'],
                file_type='obj',
                material_properties={
                    'map_Kd': files['texture']
                }
            )

            # Export as GLB
            glb_path = os.path.join(self.temp_dir, 'output.glb')
            mesh.export(glb_path, file_type='glb')

            # Read the GLB file
            with open(glb_path, 'rb') as f:
                glb_data = f.read()

            # Clean up temporary files
            for file_path in files.values():
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
            if os.path.exists(glb_path):
                os.remove(glb_path)

            return glb_data

        except Exception as e:
            raise Exception(f"Error converting to GLB: {str(e)}")

    def process_prompt(self, prompt):
        """
        Process the prompt and verify execution
        """
        try:
            # First, queue the prompt and get prompt_id
            print("Queueing prompt...")
            queue_response = self.queue_prompt(prompt)
            prompt_id = queue_response['prompt_id']
            print(f"Prompt queued with ID: {prompt_id}")

            # Then connect to websocket to monitor execution
            ws = websocket.WebSocket()
            ws.settimeout(300)  # 5 minutes timeout
            ws.connect(f"ws://{self.server_address}/ws?clientId={self.client_id}")

            # Wait for execution to complete
            print("Waiting for execution to complete...")
            while True:
                out = ws.recv()
                if isinstance(out, str):
                    message = json.loads(out)
                    print(f"Received message: {message}")

                    # Check if this message is relevant to our prompt
                    if 'data' in message and 'prompt_id' in message['data']:
                        if message['data']['prompt_id'] == prompt_id:
                            # Handle different message types
                            if message['type'] == 'execution_start':
                                print("Execution started")
                            elif message['type'] == 'executing':
                                node = message['data'].get('node')
                                if node:
                                    print(f"Processing node: {node}")
                                else:
                                    print("Final node reached")
                            elif message['type'] == 'execution_error':
                                error = message['data'].get('error', 'Unknown error')
                                print(f"Execution failed: {error}")
                                return False
                            elif message['type'] == 'execution_success':
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

    def __del__(self):
        """
        Cleanup temporary directory when the object is destroyed
        """
        try:
            import shutil
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except:
            # Ignore errors during shutdown
            pass
