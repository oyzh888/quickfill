import io
import json
import re

from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from PIL import Image
from PyPDF2 import PdfFileReader, PdfFileWriter
from quickfill.ai.multimodal_form_filling import process_text_with_images_gpt4v
from quickfill.ocr.aws_text_extract import OCRReturnType, api_analyze_document
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def get_input_file_size(file_path):
    if file_path.lower().endswith('.pdf'):
        with open(file_path, 'rb') as f:
            reader = PdfFileReader(f)
            page = reader.getPage(0)
            return page.mediaBox.getWidth(), page.mediaBox.getHeight()
    else:
        with Image.open(file_path) as img:
            return img.size  # Returns (width, height)


def convert_image_to_pdf(image_path):
    # Convert the image to a PDF and return a PdfFileReader object
    image = Image.open(image_path)
    pdf_bytes = io.BytesIO()
    image.convert('RGB').save(pdf_bytes, format='PDF')
    pdf_bytes.seek(0)
    return PdfFileReader(pdf_bytes)


def create_form_field_pdf():
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # TODO
    # Make fillColor=colors.white more adaptive or transparent
    form = can.acroForm
    form.textfield(name='hello', tooltip='Field',
                   x=200, y=400, width=200, height=20,
                   borderColor=colors.white, fillColor=colors.white,
                   textColor=colors.red, borderWidth=0,  # Border width set to 0
                   borderStyle='underlined', forceBorder=True,
                   value='Hello World')

    can.save()
    packet.seek(0)
    return PdfFileReader(packet)

def merge_pdfs(form_pdf, existing_file_path, output_pdf_path):
    # Check if the existing file is a PDF or an image
    if existing_file_path.lower().endswith('.pdf'):
        existing_pdf = PdfFileReader(existing_file_path)
    else:
        # Convert image to PDF if it's not a PDF
        existing_pdf = convert_image_to_pdf(existing_file_path)

    output = PdfFileWriter()

    for i in range(len(existing_pdf.pages)):
        page = existing_pdf.getPage(i)
        if i == 0:  # Add form only to the first page
            page.mergePage(form_pdf.getPage(0))
        output.addPage(page)

    with open(output_pdf_path, 'wb') as outputStream:
        output.write(outputStream)

def calculate_font_size(field_height, text_length, max_font_size=24):
    # Start with a font size that's 70% of the field's height
    font_size = field_height * 0.7

    # Adjust the font size if the text is too long
    # This is a simple heuristic and might need fine-tuning
    max_char_in_line = field_height * 1.5
    if text_length > max_char_in_line:
        font_size *= max_char_in_line / text_length

    return min(font_size, max_font_size)

def fill_in_forms(key_value_pairs_obj, page_size):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=page_size)

    form = can.acroForm

    page_width, page_height = page_size

    for key, dict_value in key_value_pairs_obj.items():
        bounding_box = dict_value['BoundingBox']
        x = bounding_box['Left'] * page_size[0]
        y = (1 - bounding_box['Top'] - bounding_box['Height']) * page_size[1]
        width = bounding_box['Width'] * page_size[0]
        height = bounding_box['Height'] * page_size[1]
        text = dict_value.get('Value', 'Hello World')

        font_size = calculate_font_size(height, len(text))
        form.textfield(name=key, tooltip=key, x=x, y=y, width=width, height=height,
                       borderColor=colors.black, fillColor=colors.white,
                       textColor=colors.black, borderWidth=1, fontSize=font_size,
                       borderStyle='underlined', forceBorder=True,
                       value=text)
    can.save()
    packet.seek(0)
    return PdfFileReader(packet)


# Function to update nested values
def update_nested_dict(main_dict, updates):
    for key, value in updates.items():
        if key in main_dict and 'Value' in main_dict[key]:
            main_dict[key]['Value'] = value
            # print(main_dict)
            print(f"Assign value [{value}] to key [{key}]")


def genearl_form_filling(form_a_str:str, form_b_str:str) -> dict:
    prompt = '''
You are a form filling expert. You will help user fill the content from forma to formb. You should respond in json format.

# Rules:
- Drop keys from form b if you cannot find the answer
- Only fill in the value when you are super confident
- forma contains ground truth information, and formb is the information you will finish

# Here are the content from the forma:
{form_a_content}

# Here is the schema from formb:
{form_b_schema}

You reply:
```json
?
```
    '''
    model = ChatOpenAI(model='gpt-4-1106-preview', temperature=0.1)
    prompt = ChatPromptTemplate.from_template(prompt)
    print(prompt.invoke({"form_a_content": form_a_str, "form_b_schema": form_b_str}))
    chain = prompt | model
    res = chain.invoke({"form_a_content": form_a_str, "form_b_schema": form_b_str}).content
    print(res)
    pattern = r'```json\s*({.*?}|\[.*?])\s*```'
    # Search for the pattern in the input string
    match = re.search(pattern, res, re.DOTALL)

    # If a match is found, return the JSON string
    if match:
        res = match.group(1)
    res = json.loads(res)
    return res

def export_pdf_through_json(image_bytes, key_value_pairs_obj):
    # Get page size from image bytes
    with Image.open(io.BytesIO(image_bytes)) as img:
        page_size = img.size  # Returns (width, height)

    # Create a form PDF with fields based on OCR results
    form_pdf = fill_in_forms(key_value_pairs_obj, page_size)

    # Convert the image to a PDF if it's not already a PDF
    input_pdf = convert_image_to_pdf(io.BytesIO(image_bytes))

    # Merge the form fields PDF with the input PDF
    output_pdf_bytes = io.BytesIO()
    output_pdf = PdfFileWriter()
    
    for i in range(len(input_pdf.pages)):
        page = input_pdf.getPage(i)
        if i == 0:  # Add form only to the first page
            page.mergePage(form_pdf.getPage(0))
        output_pdf.addPage(page)

    output_pdf.write(output_pdf_bytes)
    output_pdf_bytes.seek(0)  # Reset buffer pointer to the beginning
    return output_pdf_bytes

def process_image_and_text(image_bytes, text_input):
    # Run OCR on the image bytes
    kv_pairs_result, key_value_pairs_obj = api_analyze_document(image_bytes, OCRReturnType.KEY_VALUE_PAIRS)

    # Generate the JSON result from text input using the genearl_form_filling function
    json_res = genearl_form_filling(text_input, json.dumps(kv_pairs_result))

    # Update the key_value_pairs_obj with values from json_res
    update_nested_dict(key_value_pairs_obj, json_res)

    output_pdf_bytes = export_pdf_through_json(image_bytes, key_value_pairs_obj)
    return output_pdf_bytes


def gpt4v_filea_to_fileb_fill(filea_img_bytes, fileb_img_bytes):
    # Run OCR on the image bytes
    kv_pairs_result, key_value_pairs_obj = api_analyze_document(fileb_img_bytes, OCRReturnType.KEY_VALUE_PAIRS)

    json_res = process_text_with_images_gpt4v(image_paths=[filea_img_bytes], expected_keys=kv_pairs_result, from_bytes=True)
    # print("json_res:")
    # print(json_res)
    # Update the key_value_pairs_obj with values from json_res
    update_nested_dict(key_value_pairs_obj, json_res)

    output_pdf_bytes = export_pdf_through_json(fileb_img_bytes, key_value_pairs_obj)
    return output_pdf_bytes


def filea_to_fileb_fill(filea_img_bytes, fileb_img_bytes):
    # Run OCR on the image bytes
    text_res = api_analyze_document(filea_img_bytes, OCRReturnType.TEXT)
    output_pdf_bytes = process_image_and_text(fileb_img_bytes, text_res)
    return output_pdf_bytes


if __name__ == "__main__":
    text_input = '''
    My name is Steve Jobs, and I was born on June 1, 1955. I work in Apple Inc. My SSN is 123123123. I live at "Apple Park, CA, USA".
    '''
    file_path = "your_image_path.jpg"
    save_file_path = "output_pdf_path.pdf"

    with open(file_path, 'rb') as file:
        image_bytes = file.read()

    pdf_file = process_image_and_text(image_bytes, text_input)
    # Save the PDF file for testing purposes
    with open(save_file_path, 'wb') as f:
        f.write(pdf_file.read())
