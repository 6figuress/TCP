import base64
import os
from time import sleep

import requests

# List of prompts to process
prompts = [
    "pink rubber ducky",
    "rubber ducky wearing a football jersey",
    "spiderman rubber ducky",
    "rubber ducky with sunglasses",
    "rubber ducky as a pirate",
    "rubber ducky in space suit",
    "rainbow colored rubber ducky",
    "rubber ducky as a king",
    "ninja rubber ducky",
    "robot rubber ducky",
    "rubber ducky as a chef",
    "rubber ducky as a wizard",
    "superhero rubber ducky",
    "rubber ducky with headphones",
    "steampunk rubber ducky",
    "rubber ducky with mohawk",
    "mermaid rubber ducky",
    "rubber ducky in tuxedo suit",
    "zombie rubber ducky",
    "rubber ducky as a cowboy",
    "vampire rubber ducky",
    "rubber ducky with fairy wings",
    "knight rubber ducky",
    "rubber ducky as firefighter",
    "rock star rubber ducky",
    "doctor rubber ducky",
    "samurai rubber ducky",
    "rubber ducky as artist",
    "rubber ducky as santa",
    "rubber ducky wearing traditional chinese outfit",
]

# Create output directory
output_dir = "benchmark_output"
os.makedirs(output_dir, exist_ok=True)

# API endpoint
api_url = "http://localhost:5000/api/texture"


def process_prompt(prompt):
    # Create a safe filename from the prompt
    safe_filename = "".join(
        x for x in prompt if x.isalnum() or x in (" ", "-", "_")
    ).rstrip()
    safe_filename = safe_filename.replace(" ", "_")

    # Prepare the request
    payload = {"user_prompt": prompt}
    headers = {"Content-Type": "application/json"}

    print(f"Processing prompt: {prompt}")

    try:
        # Make the request
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()

        # Parse the response
        result = response.json()

        if result.get("status") == "success":
            # Decode the base64 GLB data
            glb_data = base64.b64decode(result["glb_data"])

            # Save the GLB file
            output_path = os.path.join(output_dir, f"{safe_filename}.glb")
            with open(output_path, "wb") as f:
                f.write(glb_data)

            print(f"Successfully saved: {output_path}")
            return True
        else:
            print(f"Error in response: {result.get('error', 'Unknown error')}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"Request failed for prompt '{prompt}': {str(e)}")
        return False
    except Exception as e:
        print(f"Error processing prompt '{prompt}': {str(e)}")
        return False


def main():
    successful = 0
    failed = 0

    for prompt in prompts:
        print("\n" + "=" * 50)
        if process_prompt(prompt):
            successful += 1
        else:
            failed += 1

        # Add a small delay between requests to prevent overwhelming the server
        sleep(5)

    print("\n" + "=" * 50)
    print("Processing complete!")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Output directory: {os.path.abspath(output_dir)}")


if __name__ == "__main__":
    main()
