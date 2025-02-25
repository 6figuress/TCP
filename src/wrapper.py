from subprocess import CompletedProcess, run

from flask import Flask, jsonify, request


class Wrapper:
    """
    This class exposes a simple API to interact with the Paint-it CLI.
    """

    def __init__(self) -> None:
        """
        Constructor of the Wrapper class.

            Parameters:
                None

            Returns:
                None
        """

        # initialize Flask app
        self.app: Flask = Flask(__name__)

        # initialize Flask endpoint
        @self.app.route("/api/texture", methods=["POST"])
        def texture():
            """
            Mesh texturing endpoint.

                Parameters:
                    None

                Returns:
                    JSON: The output of the Paint-it CLI.
            """

            # get mesh_filepath and
            # user_prompt from request
            data = request.get_json()
            mesh_filepath: str = data.get("mesh_filepath")
            user_prompt: str = data.get("user_prompt")

            # check if mesh_filepath
            # and user_prompt are provided
            if not mesh_filepath or not user_prompt:
                return jsonify({"error": "Missing required parameters"}), 400

            # prepare command arguments
            # TODO: replace with actual command
            cmd: list[str] = ["paint-it", mesh_filepath, user_prompt]

            # add any extra parameters from request
            extra_params: dict[str, str] = {
                k: v
                for k, v in data.items()
                if k not in ["mesh_filepath", "user_prompt"]
            }
            for param, value in extra_params.items():
                cmd.append(f"--{param} {str(value)}")

            try:
                # execute command
                result: CompletedProcess = run(cmd, capture_output=True, text=True)

                # check if command was successful
                # and return error otherwise
                if result.returncode != 0:
                    return jsonify({"error": result.stderr}), 500
                return jsonify({"output": result.stdout})
            except Exception as e:
                # return error if command failed
                return jsonify({"error": str(e)}), 500

    def run(self, host="0.0.0.0", port=5000, debug=True):
        """
        Start the Flask server.

            Parameters:
                host (str): The interface to listen on. Defaults to 0.0.0.0 (all interfaces).
                port (int): The port of the webserver. Defaults to 5000.
                debug (bool): Enable debug mode. Defaults to True.
        """

        # start Flask server
        self.app.run(host=host, port=port, debug=debug)
