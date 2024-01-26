import hashlib
import json
import os
from enum import Enum

import boto3
from quickfill.const import CACHE_PATH


def analyze_document(image_bytes, use_cache=True):
    # Initialize cache_path to None
    cache_path = None
    
    if use_cache:
        # Only calculate the hash and define cache_path if use_cache is True
        image_hash = hashlib.md5(image_bytes).hexdigest()
        cache_path = CACHE_PATH / f"{image_hash}.json"

        # Check if the OCR result is already in the cache on disk
        if os.path.exists(cache_path):
            print("Cache hit")
            with open(cache_path, 'r') as cache_file:
                return json.load(cache_file)

    # Otherwise, send a request to AWS Textract
    textract = boto3.client("textract")
    response = textract.analyze_document(
        Document={'Bytes': image_bytes},
        FeatureTypes=["TABLES", "FORMS"]
    )

    # If caching is enabled, store the OCR result in the cache on disk
    if use_cache:
        # Ensure the cache directory exists
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        # Store the OCR result in the cache on disk
        with open(cache_path, 'w') as cache_file:
            json.dump(response, cache_file)

    return response

# Plain text
def get_text_from_response(response):
    blocks = response["Blocks"]
    text = ""
    for block in blocks:
        if block["BlockType"] == "LINE":
            text += block["Text"] + "\n"
    return text


def extract_key_value_pairs(blocks):
    key_map = {}
    value_map = {}
    block_map = {}
    key_value_pairs = {}
    key_value_pairs_obj = {}  # New object for storing coordinates

    for block in blocks:
        block_id = block['Id']
        block_map[block_id] = block
        if block['BlockType'] == "KEY_VALUE_SET":
            if 'KEY' in block['EntityTypes']:
                key_map[block_id] = block
            else:
                value_map[block_id] = block

    for block_id, key_block in key_map.items():
        value_block = find_value_block(key_block, value_map, block_map)
        key = get_text(key_block, block_map)
        val = get_text(value_block, block_map)
        key_value_pairs[key] = val

        # Extract and store coordinates of the value block
        if value_block:
            coordinates = value_block.get('Geometry', {}).get('BoundingBox', {})
            key_value_pairs_obj[key] = {}
            key_value_pairs_obj[key]['BoundingBox'] = coordinates
            key_value_pairs_obj[key]['Value'] = "" # TODO: add default value?


    return key_value_pairs, key_value_pairs_obj

def find_value_block(key_block, value_map, block_map):
    for relationship in key_block['Relationships']:
        if relationship['Type'] == 'VALUE':
            for value_id in relationship['Ids']:
                value_block = value_map.get(value_id)
                if value_block:
                    return value_block
    return None

def get_text(block, block_map):
    text = ''
    if 'Relationships' in block:
        for relationship in block['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    word = block_map[child_id]
                    if word['BlockType'] == 'WORD':
                        text += word['Text'] + ' '
                    if word['BlockType'] == 'SELECTION_ELEMENT':
                        if word['SelectionStatus'] == 'SELECTED':
                            text += 'X '
    return text.strip()

# TODO: Table content and key-value pair logic is written by ChatGPT, sometimes it doesn't work, which will throw error, 
# We should process the error properly
# Table content
def extract_table_content(blocks):
    tables = []
    for block in blocks:
        if block['BlockType'] == 'TABLE':
            table = []
            for relationship in block['Relationships']:
                if relationship['Type'] == 'CHILD':
                    row = []
                    for cell_id in relationship['Ids']:
                        cell_block = find_block_by_id(cell_id, blocks)
                        cell_text = get_text_from_block(cell_block)
                        row.append(cell_text)
                    table.append(row)
            tables.append(table)
    return tables

def find_block_by_id(block_id, blocks):
    for block in blocks:
        if block['Id'] == block_id:
            return block
    return None

def get_text_from_block(block):
    text = ''
    if 'Text' in block:
        return block['Text']
    if 'Relationships' in block:
        for relationship in block['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    child_block = find_block_by_id(child_id, blocks)
                    text += get_text_from_block(child_block) + ' '
    return text.strip()

# Helper functions
def quick_analyze_document(file_path):
    with open(file_path, 'rb') as image_file:
        image_bytes = image_file.read()
    res = analyze_document(image_bytes)
    res = get_text_from_response(res)
    return res

class OCRReturnType(Enum):
    RAW = "raw"
    TEXT = "text"
    KEY_VALUE_PAIRS = "key_value_pairs"
    TABLE_CONTENT = "table_content"
    

def api_analyze_document(image_bytes, return_type: OCRReturnType = OCRReturnType.TEXT):
    '''
    Calls analyze_document and optionally uses get_text_from_response,
    extract_key_value_pairs, extract_table_content to return results in different formats.
    Users can decide which return_type they want to get, they can get either text, key_value_pairs or table_content.
    '''
    # Get the OCR result
    ocr_result_response = analyze_document(image_bytes)

    # Process the OCR result based on the return_type
    if return_type == OCRReturnType.TEXT:
        result = get_text_from_response(ocr_result_response)
    # TODO, 'Block' might be redundant
    elif return_type == OCRReturnType.KEY_VALUE_PAIRS:
        result = extract_key_value_pairs(ocr_result_response['Blocks'])
    elif return_type == OCRReturnType.TABLE_CONTENT:
        result = extract_table_content(ocr_result_response['Blocks'])
    elif return_type == OCRReturnType.RAW:
        result = ocr_result_response
    else:
        raise ValueError(f"Unsupported return_type: {return_type}")

    return result



if __name__ == "__main__":
    file_path = "./data/driver_license/US/Alabama's.jpg"
    with open(file_path, 'rb') as file:
        image_bytes = file.read()

    # Call the function with the image bytes
    text_result = api_analyze_document(image_bytes, OCRReturnType.TEXT)
    print(text_result)
    key_value_pairs, key_value_pairs_obj = api_analyze_document(image_bytes, OCRReturnType.KEY_VALUE_PAIRS)
    print(key_value_pairs_obj)
    table_content_result = api_analyze_document(image_bytes, OCRReturnType.TABLE_CONTENT)
    print(table_content_result)
