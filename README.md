# SingleStore Hands-On-Lab Launcher
## Overview
The SingleStore Hands-On-Lab Launcher is a Jupyter Notebook based tool designed to streamline the creation and management of AWS and SingleStore resources for hands-on lab environments. It provides an interactive form to configure and deploy resources efficiently.

## Repository Structure
This project consists of four primary Python files:

1. form_funcs.py: Contains utility functions for form handling and data fetching.
1. aws_funcs.py: Comprises functions related to AWS operations, including AWS credential validation and CloudFormation stack management.
1. sdb_funcs.py (SingleStore Functions): Encompasses all functionalities related to managing SingleStore workspaces, including creation, update, and querying of workspace details.
1. form.py: The main file that uses ipywidgets to create an interactive form in the Jupyter Notebook, integrating functionalities from the other modules.

## Installation and Usage
To use this project, follow these steps:

1. Clone the Repository: Clone this repository to your local machine or Jupyter environment.
```bash
git clone <repository-url>
```
1. Install Dependencies: Ensure you have Jupyter Notebook and necessary Python libraries installed. You can install the required libraries using:
```bash
pip install -r requirements.txt
```
1. Launch Jupyter Notebook:

```bash
jupyter notebook
```
1. Open form.py: This file is the entry point. Run the cells in this notebook to interact with the form.
1. Fill in the Form: Provide necessary details like AWS credentials, SingleStore API key, and other configurations as per the form fields.
1. Execute Operations: Use the form buttons to perform operations like creating AWS resources, managing SingleStore workspaces, etc.

## Contributing
Contributions to improve the tool or extend its functionality are welcome. Please adhere to the following guidelines:

1. Fork the Repository: Make a fork of this project.
1. Create a Feature Branch: Make your changes in a new git branch.
1. Commit Changes: Commit your changes with clear and concise commit messages.
1. Push to the Branch: Push your changes to your fork.
1. Submit a Pull Request: Open a pull request to merge your changes into the main branch.

## Support and Feedback
If you encounter any issues or have suggestions, feel free to open an issue in the repository, and we'll address it as promptly as possible.
