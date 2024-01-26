import json

from langchain.chains import create_extraction_chain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate


def flatten_keys(data, parent_key='', sep='$$'):
    items = {}
    for k, v in data.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_keys(v, new_key, sep=sep))
        else:
            items[new_key] = v
    return items

def ai_form_filling(context_str: str, target_json: dict, auto: bool = True) -> dict:
    if auto:
        flattened_json = flatten_keys(target_json)
        properties = {key: {"type": "string"} for key in flattened_json.keys()}
        # required = list(properties.keys())
        required = []
        schema = {
            "properties": properties,
            "required": required
        }
        print("schema", json.dumps(schema, indent=4))
    else:
        schema = target_json

    llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
    chain = create_extraction_chain(schema, llm)
    result = chain.run(context_str)
    # print("result", json.dumps(result, indent=4))
    if type(result) == list:
        result = result[0]
    return result

def genearl_form_filling(form_a_str:str, form_b_str:str) -> dict:
    prompt = '''
You are a form filling expert. You will help user fill the content from forma to formb. You should respond in json format.
Rules:
- Leave items from form b as blank if you're not sure 
- forma contains ground truth information, and formb is the information you will finish

Here are the content from the forma:
{form_a_content}

Here is the schema from formb:
{form_b_schema}
    '''
    model = ChatOpenAI()
    prompt = ChatPromptTemplate.from_template(prompt)
    chain = prompt | model
    res = chain.invoke({"form_a_content": form_a_str, "form_b_schema": form_b_str})
    res = json.loads(res.content)
    return res

# Test
def test_ai_form_filling():
    # Define the input text and target schema
    inp = """Alex is 5 feet tall. Claudia is 1 feet taller Alex and jumps higher than him. Claudia is a brunette and Alex is blonde."""
    target_json = {
        "name": {},
        "height": {},
        "hair_color": {}
    }

    # Call the ai_form_filling function with auto set to True
    output = ai_form_filling(inp, target_json, auto=True)

    # Print the output
    print(output)

def test_ai_form_filling_nested():
    # Define the input text and target schema
    inp = """Alex is 5 feet tall. Claudia is 1 feet taller Alex and jumps higher than him. Claudia is a brunette and Alex is blonde.
    Alex lives at sunnyvale. zipcode 94089. Alex's emergency contact is John Smith. John's phone number is 1234567890. John's relationship to Alex is father.
    """
    target_json = {
        "First Name": "",
        "Last Name": "",
        "Date of Birth": "",
        "Sex": "",
        "Marital Status": "",
        "Email Address": "",
        "Address": "",
        "City": "",
        "State": "",
        "Zip Code": "",
        "Phone": "",
        "Emergency Contact 1": {
            "First Name": "",
            "Last Name": "",
            "Phone": "",
            "Relationship to Patient": ""
        },
        "Emergency Contact 2": {
            "First Name": "",
            "Last Name": "",
            "Phone": "",
            "Relationship to Patient": ""
        },
        "Did you feel fever or feverish lately?": "",
        "Are you having shortness of breath?": "",
        "Do you have a cough?": "",
        "Did you experience loss of taste or smell?": "",
        "Where you in contact with any confirmed COVID-19 positive patients?": "",
        "Did you travel in the past 14 days to any regions affected by COVID-19?": ""
    }

    # Call the ai_form_filling function with auto set to True
    # import ipdb; ipdb.set_trace()
    output = ai_form_filling(inp, target_json, auto=True)

    # Print the output
    print(output)

def test_genearl_form_filling():
    # Define the input text and target schema
    inp = """Alex is 5 feet tall and was born on 1996/6/3. Claudia is 1 feet taller Alex and jumps higher than him. Claudia is a brunette and Alex is blonde."""
    form_b_str = """
    {
        "First Name": {
            "type": "string"
        },
        "Last Name": {
            "type": "string"
        },
        "Date of Birth": {
            "type": "string"
        },
        "Sex": {
            "type": "string"
        },
        "Marital Status": {
            "type": "string"
        },
        "Email Address": {
            "type": "string"
        },
        "Address": {
            "type": "string"
        },
        "City": {
            "type": "string"
        },
        "State": {
            "type": "string"
        },
        "Zip Code": {
            "type": "string"
        },
    }
    """
    # Call the ai_form_filling function with auto set to True
    output = genearl_form_filling(inp, form_b_str)
    # Print the output
    print(output)


if __name__ == "__main__":
    test_ai_form_filling()
    test_ai_form_filling_nested()
    test_genearl_form_filling()
