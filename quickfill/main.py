from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse  # Corrected import
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from quickfill.ai.ai_form_filling import (filea_to_fileb_fill,
                                          gpt4v_filea_to_fileb_fill,
                                          process_image_and_text)
from quickfill.ai.form_filling import ai_form_filling, genearl_form_filling
from quickfill.ocr.aws_text_extract import OCRReturnType, api_analyze_document

app = FastAPI()

# TODO: Change this to the actual frontend URL
allow_origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/ai_process_form/")
async def ai_process_form(file: UploadFile = File(...), text_description: str = Form(...)):
    # Save the uploaded image
    image_bytes = await file.read()

    # Call the function to process the image and text
    pdf_file = process_image_and_text(image_bytes, text_description)
   # Set the content to be downloadable as a PDF file
    headers = {
        "Content-Disposition": "attachment; filename=form_output.pdf"
    }

    return StreamingResponse(pdf_file, media_type="application/pdf", headers=headers)


@app.post("/analyze_identity_documents")
async def analyze_document_route(file: UploadFile, return_type: OCRReturnType = OCRReturnType.TEXT):
    file_bytes = await file.read()
    ocr_result = api_analyze_document(file_bytes, return_type)
    return ocr_result

@app.post("/general_fill_form")
async def general_fill_form_route(form_a_text:str, form_b_text:str) -> dict:
    fill_result = genearl_form_filling(form_a_text, form_b_text)
    return fill_result


@app.post("/gpt4v_general_fill_form_files")
async def general_fill_form_files_route(form_a_file:UploadFile, form_b_file:UploadFile) -> dict:

    # Save the uploaded image
    image_bytes_filea = await form_a_file.read()
    image_bytes_fileb = await form_b_file.read()

    # Call the function to process the image and text
    pdf_file = gpt4v_filea_to_fileb_fill(image_bytes_filea, image_bytes_fileb)
   # Set the content to be downloadable as a PDF file
    headers = {
        "Content-Disposition": "attachment; filename=form_output.pdf"
    }

    return StreamingResponse(pdf_file, media_type="application/pdf", headers=headers)


@app.post("/general_fill_form_files")
async def general_fill_form_files_route(form_a_file:UploadFile, form_b_file:UploadFile) -> dict:

    # Save the uploaded image
    image_bytes_filea = await form_a_file.read()
    image_bytes_fileb = await form_b_file.read()

    # Call the function to process the image and text
    pdf_file = filea_to_fileb_fill(image_bytes_filea, image_bytes_fileb)
    # Set the content to be downloadable as a PDF file
    headers = {
        "Content-Disposition": "attachment; filename=form_output.pdf"
    }
    return StreamingResponse(pdf_file, media_type="application/pdf", headers=headers)

@app.post("/ai_fill_form_template")
async def ai_fill_form_template(file:UploadFile, form_b_schema:str) -> dict:
    ocr_result = await analyze_document_route(file)
    fill_result = ai_form_filling(ocr_result, form_b_schema)
    return fill_result


@app.get("/ping")
async def root():
    return {"message": "Hello QuickFill!"}

# Frontend
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")
