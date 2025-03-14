import json
import os
from subprocess import CompletedProcess, run
from urllib import request

from flask import Flask, jsonify, request as flask_request

class Wrapper:
    def __init__(self) -> None:
        self.app: Flask = Flask(__name__)

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

                # Update node 153 (main CLIPTextEncode) with user prompt
                if "153" in prompt:  # Access node directly by its ID
                    prompt["153"]["inputs"]["text"] = user_prompt

                # Queue the prompt to ComfyUI
                try:
                    self.queue_prompt(prompt)
                    return jsonify({
                        "status": "success",
                        "message": "Prompt queued successfully",
                        "user_prompt": user_prompt
                    })
                except Exception as e:
                    return jsonify({"error": f"Failed to queue prompt: {str(e)}"}), 500

            except Exception as e:
                return jsonify({"error": str(e)}), 500

    def queue_prompt(self, prompt):
        """
        Queue a prompt to ComfyUI
        """
        p = {"prompt": prompt}
        data = json.dumps(p).encode('utf-8')
        req = request.Request("http://192.168.91.13:8188/prompt", data=data)
        request.urlopen(req)

    def run(self, host="0.0.0.0", port=5000, debug=True):
        self.app.run(host=host, port=port, debug=debug)
