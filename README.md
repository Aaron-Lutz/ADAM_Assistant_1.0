A.D.A.M. - Your Personal Digital Assistant

Overview
A.D.A.M. (Automated Digital Assistant Mainframe) is a prototype, Flask-based web application designed to act as a personal digital assistant. Drawing inspiration from JARVIS in Iron Man, A.D.A.M. offers a unique blend of functionality, including handling emails, managing calendar events, creating tasks, and providing general updates, all with the convenience and efficiency of voice commands. Built with integration for Google Cloud services and leveraging advanced AI through GPT models and Google's Text-to-Speech, A.D.A.M. brings a personal assistant into the digital age, catering to private individuals looking for a smarter way to manage their digital life. This versions main functinality is still based on the API from OpenAI using the chat completions API. I am currently working on adapting this application to use the new Assistants API from OpenAI with integrated function calling to reduce the amount of "GPT instances" required to optimize the speed and usability of the application as well as use threads instead of having to handle the conversation history manually.

Installation and Setup
Clone the repository: Get the code to your local machine.
Dependencies: Install necessary Python packages with pip install -r requirements.txt.
Google Cloud Credentials: Securely configure your Google Cloud credentials as per the provided documentation below.
Configuration
Sensitive data such as Google Cloud credentials must be managed securely. Use environment variables for OAuth 2.0 Client IDs, client secrets, and service account keys, ensuring your personal data remains secure.

Usage
With python app.py, A.D.A.M. comes to life on your local server. A web-based interface allows intuitive interaction, providing services from weather updates to task management, all processed with natural language through GPT and articulated via Google's Text-to-Speech.

Contributing
Contributions to A.D.A.M. are warmly welcomed. Whether it's bug fixes, feature enhancements, or documentation improvements, feel free to fork the project and submit a pull request.

License and Use
This project is intended for private use and educational purposes only. Commercial use is strictly prohibited. Contributions, however, are encouraged under the premise that they adhere to this project's non-commercial ethos.

Setting Up Google Cloud Credentials
Ensure A.D.A.M. is equipped with the necessary access to Google services by following detailed instructions for creating a Google Cloud project, enabling APIs, and configuring service accounts. This setup is crucial for leveraging the full capabilities of A.D.A.M., from email management to speech synthesis.

Step 1: Create a Google Cloud Project
Go to the Google Cloud Console.
Create a new project or select an existing one.
Step 2: Enable APIs
Navigate to the "APIs & Services" dashboard.
Enable the Google Text-to-Speech API, Gmail API, Google Calendar API and Tasks API as well as any other APIs your project adaption requires.
Step 3: Create a Service Account
Go to "IAM & Admin" > "Service Accounts".
Click "Create Service Account", fill in the form, and grant it the necessary roles (e.g., Text-to-Speech User).
Step 4: Generate Credentials
In the service account list, find the newly created account and click on "Actions" > "Manage keys".
Add a new key, select JSON, and download the key file.
Step 5: Configure Your Project
Rename your downloaded key file to tts_creds.json and place it in the project directory, or set the path to this file in your environment variables.
For OAuth2.0 credentials (used for accessing user data), go to the "Credentials" page in the Cloud Console, create OAuth 2.0 Client IDs, download the JSON, and fill in the credentials.json template accordingly.

RapidAPI Google Search API:
For using the Google Search API I used:
Sign up at RapidAPI.
Subscribe to the Google Search API.
Obtain your RapidAPI key and enter it in the main.py file or use your own preferred API for websearch and make the necessary adaption in the code.

OpenAI API Key:
Register at OpenAI and access your API key from the account settings and enter it in the main.py file or use an environment variable.
