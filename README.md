# QuickFill

QuickFill is an AI-powered form-filling application that simplifies the process of filling out forms by using image uploads. It leverages GPT-4 Vision and AWS OCR technology to extract information from provided images and fill the forms accurately.

## Installation

To get started with QuickFill, you need to set up the application on your local environment. Follow these steps:

```bash
pip install -e .
pip install -r requirements.txt
```

## Setup

Before using QuickFill, you need to configure your OpenAI and AWS credentials. These keys are essential for the application to function properly.

1. OpenAI API Key: Set up your OpenAI API key to enable GPT-4 Vision capabilities.
2. AWS Access Key: Configure your AWS access key to use AWS OCR services.

## How to Start

To launch QuickFill, navigate to the application's directory and run the provided script. Then, access the application through your web browser:

```bash
cd quickfill
sh run.sh
```

Visit `localhost:8080` in your browser to access QuickFill frontend.
Visit `localhost:8080/docs` to see the API doc.

## Frontend

The frontend code for QuickFill is located in the following directory:

```
quickfill/frontend/index.html
```

You can modify the frontend as per your needs.

## Functionality

QuickFill mainly functions through two image uploads:

- **Image A**: Upload an image containing the information from the user.
- **Image B**: Upload an image of the target form that needs to be filled.

## Technology Stack

- **GPT-4 Vision**: Utilized for advanced image processing and understanding.
- **AWS OCR**: Employed for Optical Character Recognition to accurately extract text from images.

## Limitations

Currently, QuickFill only supports English, due to the reliance on AWS OCR services. This limitation is necessary to ensure accurate location and filling of the forms.

## Citation

If you use QuickFill in your research or project, please cite the following paper:

```bibtex
@article{qin2023openvoice,
  title={OpenVoice: Versatile Instant Voice Cloning},
  author={Qin, Zengyi and Zhao, Wenliang and Yu, Xumin and Sun, Xin},
  journal={arXiv preprint arXiv:2312.01479},
  year={2023}
}
```

Thank you for choosing QuickFill!
```
