import base64
import io
import json
import re
import time

import openai
import vertexai
from langchain.chat_models import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from vertexai.preview.generative_models import GenerativeModel, Image, Part

gpt4v_text_prompt = \
'''Please read the text in this image and return the information in JSON format, if there is no valid result, leave it as blank.
'''


def time_it(func):
    # This function shows the execution time of
    # the function object passed
    def wrap_func(*args, **kwargs):
        t1 = time.time()
        result = func(*args, **kwargs)
        t2 = time.time()
        print(f"### Function {func.__name__!r} executed in {(t2 - t1):.4f}s ###")
        return result

    return wrap_func


# TODO: Add Google Gemini code
@time_it
def run_gemini(image_path: str, prompt_text: str, project_id: str="aitist-390505", location: str="us-central1") -> str:
    # Initialize Vertex AI
    vertexai.init(project=project_id, location=location)
    
    # Load the image file into an Image object
    # Assuming there's a method in the Image class to load from a file path
    image = Image.load_from_file(image_path)  # This line might need to be adjusted
    
    # Load the model
    multimodal_model = GenerativeModel("gemini-pro-vision")

    # Query the model with the image
    response = multimodal_model.generate_content(
        [
            Part.from_image(image),
            prompt_text,
        ]
    )
    
    print(response)
    # Extract and return the text content from the response
    for candidate in response.candidates:
        return candidate.content.parts[0].text

# GPT4V
def get_base64_image(image_source, from_bytes=False):
    if from_bytes:
        return base64.b64encode(image_source).decode('utf-8')
    else:
        # Read the image from the file path and convert to base64
        with open(image_source, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')


# Function to process text with multiple images for form filling
@time_it
def process_text_with_images_gpt4v(image_paths, text_input=gpt4v_text_prompt, expected_keys=None, from_bytes=False):
    # Convert each image to base64 and store in a list
    base64_images = [get_base64_image(path, from_bytes=from_bytes) for path in image_paths]

    # Create a chain with the ChatOpenAI model for GPT-4 Vision
    chat = ChatOpenAI(model="gpt-4-vision-preview", max_tokens=2048)
    if expected_keys:
        text_input = f"{text_input}\nHere are the keys that are expected: {expected_keys}."

    print("text_input promopt:", text_input)
    contents = []
    contents.append({"type": "text", "text": text_input})
    for img in base64_images:
        contents.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{img}",
                "detail": "auto",
            },
        })

    message = HumanMessage(content=contents)

    # Invoke the chain with the message
    response = chat.invoke([message])
    
    # Extract and process the response
    res = response.content
    # print("Res from GPT4V:", res)

    pattern = r'```json\s*({.*?}|\[.*?])\s*```'
    # Search for the pattern in the input string
    match = re.search(pattern, res, re.DOTALL)

    # If a match is found, return the JSON string
    if match:
        res = match.group(1)
    res = json.loads(res)
    return res


if __name__ == "__main__":
    from quickfill.const import DATA_PATH
    img1_path = DATA_PATH / "driver_license/US/Alabama's.jpg"
    # Example usage
    print("Run openai demo")
    image_paths = [img1_path, img1_path]  # Replace with your image paths
    filled_form = process_text_with_images_gpt4v(image_paths)
    print(filled_form)

#     print("Run google demo")
#     google_prompt = \
# '''Please read the text in this image and return the information in JSON format, if 
# there is no valid result, leave it as blank
# '''

#     # Example usage
#     image_path = "/Users/ouyangzhihao/Desktop/WechatIMG419.jpg"  # Replace with your image file path
#     res = run_gemini(image_paths[0], google_prompt)
#     print(res)


