# GPT Harris Matrix Draft

## Description
This project, written in Python, focuses on providing a Graphical User Interface (GUI) that allows users to interact with the GPT-4 AI model (not released as of the time of writing) by inputting a prompt and receiving a text output from the model.
The main construct used here is the PyQt5 library to create the GUI, providing buttons for various operations like saving, clearing, analyzing images, and changing pen color.
This project incorporates several wide-ranging features such as:
A simple drawing app: Using PyQt5, the app enables users to draw simple images with the ability to save, clear and analyze the drawings. The pen color used for drawing can be changed.
A chat interface with GPT-4: There's a function get_gpt4_response that can seemingly interact with GPT-4 API to get responses based on user input.
Token and cost tracking: As the GPT-4 model operates, it tracks the number of tokens used and the total cost of those tokens.
Image Analysis: It appears to have a mechanism to convert drawn images into a form that can be processed by GPT-4 (analyze_image function).
Important to note, some parts of this project may not work since GPT-4 is not released yet and there are placeholders like self.get_api_key which seem to be getting the API key for interacting with GPT-4.
Overall, this project seems like an impressive attempt to use PyQt5 to provide an interface for GPT-4 model to analyze hand-drawn images and generate intelligent content based on them.

## Features

- Interactive Drawing Interface: The interface allows users to draw simple images with the ability to save, clear and analyze the drawings. The pen color used for drawing can be changed.

- GPT-4 AI Integrations: The application has features seemingly set up to interact with the GPT-4 artificial intelligence model to generate intelligent responses based on the user input and potentially also hand-drawn images.

- Token and Cost Estimation: The application keeps track of the number of tokens used and the cost of those tokens when interacting with GPT-4.

- Image Analysis: The application is potentially equipped to convert hand-drawn images into a form that can be processed by GPT-4, thereby providing insightful content based on the images.

## Requirements

- Python 3.x
- Required packages listed in `requirements.txt`

## Setup Instructions

### Clone the Repository
Clone the repository to your local machine using:
```sh
git clone https://github.com/enzococca/gpt-harris-matrix-draft.git
cd gpt-harris-matrix-draft
```
### Install Dependencies
Using a Batch File (Windows)
Run the following batch file to install all required packages:

 ```
 install_requirements.bat
 
 ```

### Manual Installation
Alternatively, you can manually install the required packages using pip

 ```pip install -r requirements.txt ```

### Usage
Provide instructions on how to use your project. For example:
 ```python draw_main.py ```

### Contributing
If you would like to contribute, please fork the repository and use a feature branch. Pull requests are warmly welcome.
License
This project is licensed under the MIT License - see the LICENSE file for details.
Contact
- Enzo Cocca - enzo.ccc@gmail.com
- Project Link: https://github.com/enzococca/gpt-harris-matrix-draft


