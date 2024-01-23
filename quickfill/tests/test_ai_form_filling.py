# TODO Make this script work
from quickfill.ocr.aws_text_extract import quick_analyze_document


def test_ocr_and_form_filling():
    
    res = quick_analyze_document("./data/driver_license/US/Alabama's.jpg")
    print(res)

    # Define the target schema
    target_schema = {
        "properties": {
            "license_type": {"type": "string"},
            "state": {"type": "string"},
            "license_number": {"type": "string"},
            "class": {"type": "string"},
            "dob": {"type": "string"},
            "exp_date": {"type": "string"},
            "first_name": {"type": "string"},
            "last_name": {"type": "string"},
            "address": {"type": "string"},
            "city": {"type": "string"},
            "state_address": {"type": "string"},
            "zip": {"type": "string"},
            "endorsements": {"type": "string"},
            "restrictions": {"type": "string"},
            "issue_date": {"type": "string"},
            "sex": {"type": "string"},
            "height": {"type": "string"},
            "eye_color": {"type": "string"},
            "weight": {"type": "string"},
            "hair_color": {"type": "string"}
        },
        "required": ["license_type", "state", "license_number", "first_name", "last_name"]
    }

    # Call the ai_form_filling function with auto set to False (since we have a defined schema)
    output = ai_form_filling(ocr_result_text, target_schema)

    # Print the output
    print(json.dumps(output, indent=4))


# Run the test
if __name__ == "__main__":
    # test_ai_form_filling()
    test_ocr_and_form_filling()
