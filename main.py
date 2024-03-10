import openai
import speech_recognition as sr
import requests
import json
import base64
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fuzzywuzzy import fuzz
import json
import threading




openai.api_key = "API_KEY"

MAX_TURNS = 8  # Each "turn" includes one user message and one assistant message

class UserSession:

    now = datetime.now()
    datetime_str = now.strftime("%A %Y-%m-%d %H:%M:%S")

    def __init__(self, user_name, conversation_history, latitude, longitude, city):
        self.user_name = user_name
        self.conversation_history = conversation_history
        self.latitude = latitude
        self.longitude = longitude
        self.city = city

    
    def generate_response(self):
        now = datetime.now()
        datetime_str = now.strftime("%A %Y-%m-%d %H:%M:%S")

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=0.5,
            messages=[
            {
            "role": "system",
            "content": f"Ignore all previous instructions. You are a personal A.I assistant. You behave exactly like JARVIS from Iron Man, but your name is A.D.A.M. - Automated Digital Assistant Mainframe. However, everyone just calls you Adam. You were created by Aaron Lutz. You are the assistant of {self.user_name}. They are located in {self.city}. Use Mr. / Ms. to address them. Today's datetime is {datetime_str}. Keep your responses short and witty. You are the center piece of a program that is connected to various APIs. You can call those APIs to handle emails, calendar, to-do list, perform web searches, check the weather and give general updates. When the prompt, in any way, requires one of those API calls, respond with something like 'Of course, one moment while I...'. You do not have direct access to the API calls, they will be executed in another instance, so do not ever, under any circumstance, confirm an action or answer a prompt that requires one of the above API calls on your own, you are never allowed to do that. If a prompt requires anything that you yourself are not capable of and isn't one of the integrated APIs, respond with 'I'm sorry, I can't do that yet'."
            },
            *self.conversation_history
            ]
        )

        # Add the new assistant message to the conversation history
        message_content = response.choices[0].message['content']
        self.conversation_history.append({"role": "assistant", "content": message_content})

        # If the conversation history is too long, remove the oldest messages
        while len(self.conversation_history) > MAX_TURNS:
            self.conversation_history.pop(0)

        return message_content


    def generate_command(self, prompt):
        self.conversation_history.append({"role": "user", "content": prompt})
        command_response = openai.ChatCompletion.create(
            model="gpt-4",
            temperature=0,
            messages=[
            *self.conversation_history,
            {
            "role": "system",
            "content": "Ignore all previous instructions. You are my command center. When you detect an action that needs to be taken based on my prompt, respond only with one of the following commands. You have full authorization to perform each command. Your response must only contain the command and nothing else. The actual response to the prompt will be taken care of by another instance of GPT 4, so do not ever respond to the prompt, only output the command. You are not allowed to ever, under any circumstance, respond with anything other than the following commands: regularresponse, websearch, getcalendar, createevents, gettasks, createtask, deletetask, getweather, getemail, draftemail, confirmsendemail, briefing, none. If multiple different commands are needed, link them together with '->'. Never link multiple instances of the same command with itself. Use the command 'none' when none of the other commands fit the prompt. Never, ever use the websearch command if it wasn't clearly stated in the prompt to do a web search or GPT 4 can answer with its own knowledge. Never use confirmsendemail unless the user confirmed to send the email after being asked."
            },
            ]
        )

        # Get the content of the message
        command_content = command_response.choices[0].message['content']
        return command_content
	
    #generate web search query function
    def generate_search_query(self, prompt):
        search_query_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=0,
            messages=[
            *self.conversation_history,
            {"role": "system", "content": f"Generate a web search search query based on the latest prompt. Current location: {self.city}. Current date time: {datetime}"},
        ]
        )
        search_query_content = search_query_response.choices[0].message['content']
        print(search_query_content)
        return search_query_content
        

    #web search api function
    def web_search(self, search_query_content):
        url = "https://google-search83.p.rapidapi.com/google"
        headers = {
            "X-RapidAPI-Key": "API_KEY",
            "X-RapidAPI-Host": "google-search83.p.rapidapi.com"
        }
        params = {
            "query": search_query_content,
            "num": 10,
            "gl": "us"
        }
        response = requests.get(url, headers=headers, params=params)
        print(response.json())
        return response.json()

    #read out web search results
    def generate_search_result_response(self, response):

        # Add the assistant message (search results) to the conversation history
        # self.conversation_history.append({"role": "assistant", "content": json.dumps(search_results)})

        # Generate a response using the updated conversation history
        search_result_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            temperature=0,
            messages=[
            {"role": "system", "content": "Provide a short and concise answer to my latest prompt based the following web search results. No more than 4-5 sentences. Provide two or three hyperlinks from the search results sources, formatted as markdown"},
            *self.conversation_history,
            {"role": "assistant", "content": json.dumps(response)},
            ]
        )

        # Add the new assistant message to the conversation history
        search_result_content = search_result_response.choices[0].message['content']
        self.conversation_history.append({"role": "assistant", "content": search_result_content})

        # If the conversation history is too long, remove the oldest messages
        while len(self.conversation_history) > MAX_TURNS:
            self.conversation_history.pop(0)

        return search_result_content


    def get_weather(self):
        response = requests.get(f'https://api.open-meteo.com/v1/forecast?latitude={self.latitude}&longitude={self.longitude}&daily=temperature_2m_max,temperature_2m_min,sunrise,sunset,precipitation_sum,windspeed_10m_max&current_weather=true&timezone=Europe%2FBerlin')
        weather_data = response.json()

        # Add the assistant message to the conversation history
        # self.conversation_history.append({"role": "assistant", "content": json.dumps(weather_data)})
        
        weather_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            temperature=0,
            messages=[{"role": "system", "content": f"You are my personal A.I assistant. You behave exactly like JARVIS from Iron Man, but your name is A.D.A.M. - Automated Digital Assistant Mainframe. My name is {self.user_name} and I live in {self.city}. Today's datetime is {self.datetime_str}. Keep your responses concise, short and witty. Respond to my prompts with the weather data provided."},
            *self.conversation_history,
            {"role": "assistant", "content": json.dumps(weather_data)}
            ]
        )

        # Add the new assistant message to the conversation history
        weather_content = weather_response.choices[0].message['content']
        self.conversation_history.append({"role": "assistant", "content": weather_content})

        # If the conversation history is too long, remove the oldest messages
        while len(self.conversation_history) > MAX_TURNS:
            self.conversation_history.pop(0)

        return weather_content

    #get calendar
    def get_calendar(self, token):
        try:
            creds = Credentials.from_authorized_user_info(token)
            service = build('calendar', 'v3', credentials=creds)

            # Call the Calendar API
            now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            events_result = service.events().list(calendarId='primary', timeMin=now,
                                                maxResults=30, singleEvents=True,
                                                orderBy='startTime').execute()
            events = events_result.get('items', [])

            # Convert the list of events into a string
            event_str = "\n".join(str(e) for e in events)

            # Truncate the event_str to 95000 characters
            event_str = event_str[:95000]
            return event_str

        except HttpError as error:
            response = ('An error occurred: %s' % error)
            return response
        
    def read_events(self, event_str):

        # Add the assistant message to the conversation history
        # self.conversation_history.append({"role": "assistant", "content": json.dumps(event_str)})
        
        event_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            temperature=0,
            messages=[{"role": "system", "content": f"You are my personal A.I assistant. You behave exactly like JARVIS from Iron Man, but your name is A.D.A.M. - Automated Digital Assistant Mainframe. My name is {self.user_name} and I live in {self.city}. Today's datetime is {self.datetime_str}. Keep your responses concise, short and quippy. Respond to my prompts with the calendar data provided. Do not answer with more data than necessary. Never respond to anything that does not concern my calendar events. You are solely responsible for my calendar."},
            *self.conversation_history,
            {"role": "assistant", "content": json.dumps(event_str)}
            ]
        )

        # Add the new assistant message to the conversation history
        calendar_content = event_response.choices[0].message['content']
        self.conversation_history.append({"role": "assistant", "content": calendar_content})

        # If the conversation history is too long, remove the oldest messages
        while len(self.conversation_history) > MAX_TURNS:
            self.conversation_history.pop(0)

        return calendar_content
        
    #generate the event details
    def generate_event_details(self, token, prompt):
        try:
            filtered_contacts = self.filter_contacts(token, prompt)
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-16k-0613",
                temperature=0,
                messages=[
                    {"role": "system", "content": f"You create events for my calendar through google calendar api. Current datetime: {self.datetime_str}. My contacts are: {filtered_contacts}.Output the json exactly as defined. Always keep the time zone as Europe/Berlin."},
                    *self.conversation_history
                ],
                functions=[
                    {
                        "name": "createevents",
                        "description": "Creates new calendar events",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "events": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "summary": {"type": "string", "description": "The event title"},
                                            "location": {"type": "string", "description": "The event location"},
                                            "description": {"type": "string", "description": "The event description"},
                                            "start": {
                                                "type": "object",
                                                "properties": {
                                                    "dateTime": {
                                                        "type": "string",
                                                        "description": "The start date and time in the format 'yyyy-mm-ddThh:mm:ss'",
                                                    },
                                                    "timeZone": {
                                                        "type": "string",
                                                        "description": "The time zone, e.g., 'Europe/Berlin'",
                                                        "default": "Europe/Berlin",
                                                    },
                                                },
                                                "required": ["dateTime"]
                                            },
                                            "end": {
                                                "type": "object",
                                                "properties": {
                                                    "dateTime": {
                                                        "type": "string",
                                                        "description": "The end date and time in the format 'yyyy-mm-ddThh:mm:ss'",
                                                    },
                                                    "timeZone": {
                                                        "type": "string",
                                                        "description": "The time zone, e.g., 'Europe/Berlin'",
                                                        "default": "Europe/Berlin",
                                                    },
                                                },
                                                "required": ["dateTime"]
                                            },
                                        },
                                        "required": ["summary", "start", "end"]
                                    }
                                }
                            },
                            "required": ["events"]
                        }
                    }
                ]  
            )
            message = response.choices[0].message
            print("Message:", message)

            function_call = message.get('function_call', {})
            print("Function Call:", function_call)

            arguments_json = function_call.get('arguments', '{}')
            arguments = json.loads(arguments_json)
            print("Arguments:", arguments)

            events = arguments.get('events')
            print("Events:", events)

            if not isinstance(events, list):  # Ensure we always return a list
                events = [events]
            return events
        except Exception as e:
            print('An error occurred: %s' % e)
            return None

    def add_events_to_calendar(self, token, events):
        if events is None:
            print("Error: Events is None")
            return
        for event in events:
            summary = event.get('summary')
            start = event.get('start')
            end = event.get('end')
            location = event.get('location', None)
            description = event.get('description', None)
            attendees = event.get('attendees', None)
            
            self.create_calendar_event(token, summary, start, end, location, description, attendees)

    #add event to calendar
    def create_calendar_event(self, token, summary, start, end, location=None, description=None, attendees=None):
        try:
            creds = Credentials.from_authorized_user_info(token)
            service = build('calendar', 'v3', credentials=creds)
            event = {
                'summary': summary,
                'location': location,
                'description': description,
                'start': start,
                'end': end,
                'attendees': attendees
            }
            event = service.events().insert(calendarId='primary', body=event).execute()
            print('A.D.A.M.: The event "{}" has been added to your calendar.'.format(summary))
        except HttpError as error:
            print('An error occurred: %s' % error)


    #Get Tasks
    def list_tasks(self, token):
        creds = Credentials.from_authorized_user_info(token)
        service = build('tasks', 'v1', credentials=creds)
        tasklists = service.tasklists().list(maxResults=10).execute()
        tasks = service.tasks().list(tasklist=tasklists['items'][0]['id']).execute()
        return tasks

    def read_tasks(self, tasks):    
        # Add the assistant message to the conversation history
        self.conversation_history.append({"role": "assistant", "content": json.dumps(tasks)})
        
        task_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            temperature=0,
            messages=[{"role": "system", "content": f"You are my personal A.I assistant. You behave exactly like JARVIS from Iron Man, but your name is A.D.A.M. - Automated Digital Assistant Mainframe. My name is {self.user_name} and I live in {self.city}. Today's datetime is {self.datetime_str}. Keep your responses concise, short and quippy. Respond to my prompts with the task list data provided."},
            *self.conversation_history
            ]
        )

        # Add the new assistant message to the conversation history
        task_content = task_response.choices[0].message['content']
        self.conversation_history.append({"role": "assistant", "content": task_content})

        # If the conversation history is too long, remove the oldest messages
        while len(self.conversation_history) > MAX_TURNS:
            self.conversation_history.pop(0)

        return task_content


    #generate Task Details
    def generate_task_details(self):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            temperature=0,
            messages=[
                {
                    "role": "system", 
                    "content": f"You create tasks for my tasklist. Current datetime: {self.datetime_str}. Output the task details."
                },
                *self.conversation_history
            ],
            functions=[
                {
                    "name": "createtask",
                    "description": "Creates a new task",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "description": "The task title"},
                            "notes": {"type": "string", "description": "The task notes"},
                            "due": {"type": "string", "description": "The task due date"}
                        },
                        "required": ["title"],
                    },
                },
            ]
        )
        task_details = response.choices[0].message.get('function_call', {}).get('arguments')
        return task_details

    def add_task(self, token, task_details):
        creds = Credentials.from_authorized_user_info(token)
        service = build('tasks', 'v1', credentials=creds)
        tasklists = service.tasklists().list(maxResults=10).execute()
        task = service.tasks().insert(tasklist=tasklists['items'][0]['id'], body=task_details).execute()
        print(f"A.D.A.M.: I have added the task '{task_details['title']}' to your to-do list.")
        return task

    #generate which task to delete
    def generate_delete_command(self, tasks):
        self.conversation_history.append({"role": "assistant", "content": json.dumps(tasks)})

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-0613",
            temperature=0,
            messages=[
                {
                    "role": "system", 
                    "content": f"You delete tasks from my tasklist based on the task data provided. Never, ever, under any circumstance, respond with anything other than the task id to be deleted."
                },
                *self.conversation_history
            ],
            functions=[
                {
                    "name": "deletetask",
                    "description": "Deletes a task",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string", "description": "The task id"},
                        },
                        "required": ["id"],
                    },
                },
            ]
        )
        delete_command = response.choices[0].message.get('function_call', {}).get('arguments')
        return delete_command

    def delete_task(self, token, task_id):
        creds = Credentials.from_authorized_user_info(token)
        service = build('tasks', 'v1', credentials=creds)
        tasklists = service.tasklists().list(maxResults=10).execute()
        service.tasks().delete(tasklist=tasklists['items'][0]['id'], task=task_id['id']).execute()


    #get emails
    def fetch_gmail(self, token):
        creds = Credentials.from_authorized_user_info(token)
        service = build('gmail', 'v1', credentials=creds)

        # Call the Gmail API
        results = service.users().messages().list(userId='me', maxResults=40).execute()
        messages = results.get('messages', [])

        email_data = []
        
        for message_info in messages:
            message_id = message_info['id']
            message = service.users().messages().get(userId='me', id=message_id).execute()

            # Extract the payload and headers
            payload = message.get('payload', {})
            headers = payload.get('headers', [])

            # Extract subject and sender from headers
            subject = next((header['value'] for header in headers if header['name'] == 'Subject'), None)
            sender = next((header['value'] for header in headers if header['name'] == 'From'), None)

            # Get the snippet
            snippet = message.get('snippet')

            email_data.append((subject, sender, snippet))
            
        # Convert the email data into a string
        email_str = "\n".join(str(e) for e in email_data)

        # Truncate the email_str to 90000 characters
        email_str = email_str[:90000]

        print(email_data)
        return email_str

    def read_emails(self, email_str):               

        # Add the assistant message to the conversation history
        # self.conversation_history.append({"role": "assistant", "content": f"{email_str}"})
        
        email_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            temperature=0,
            messages=[{"role": "system", "content": f"You are my personal A.I assistant. You behave exactly like JARVIS from Iron Man, but your name is A.D.A.M. - Automated Digital Assistant Mainframe. My name is {self.user_name} and I live in {self.city}. Today's datetime is {self.datetime_str}. Keep your responses concise, short and quippy. Respond to my prompts based on the email data provided."},
            *self.conversation_history,
            {"role": "assistant", "content": f"{email_str}"}
            ]
        )

        # Add the new assistant message to the conversation history
        email_content = email_response.choices[0].message['content']
        self.conversation_history.append({"role": "assistant", "content": email_content})

        # If the conversation history is too long, remove the oldest messages
        while len(self.conversation_history) > MAX_TURNS:
            self.conversation_history.pop(0)

        return email_content

    def filter_contacts(self, token, prompt):
        all_contacts = self.fetch_contacts(token)
        
        def is_similar(contact_name, prompt):
            # Set a threshold for similarity. This can be adjusted.
            threshold = 80  
            similarity = fuzz.token_set_ratio(contact_name, prompt)
            return similarity > threshold

        filtered_contacts = [contact for contact in all_contacts if is_similar(contact['name'], prompt)]
        return filtered_contacts

    def fetch_contacts(self, token):
        creds = Credentials.from_authorized_user_info(token)
        service = build('people', 'v1', credentials=creds)
        results = service.people().connections().list(resourceName='people/me', pageSize=100, personFields='names,emailAddresses').execute()
        connections = results.get('connections', [])
        contacts = []
        for person in connections:
            email_addresses = person.get('emailAddresses', [])
            names = person.get('names', [])
            if email_addresses and names:
                contacts.append({
                    'name': names[0].get('displayName'),
                    'email': email_addresses[0].get('value')
                })
        return contacts

    #generate email
    def generate_email_details(self, token, prompt):
        filtered_contacts = self.filter_contacts(token, prompt)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            temperature=0,
            messages=[{"role": "system", "content": f"You create emails for me. Sign it with my name ({self.user_name}), but always include 'This email was written and sent by my AI Assistant.'. Current datetime: {self.datetime_str}. My contacts are: {filtered_contacts}. Output the json exactly as defined."},

            *self.conversation_history
                    ],
            functions=[
                {
                    "name": "sendemail",
                    "description": "Sends an email",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "to": {"type": "string", "description": "The recipient's email address"},
                            "subject": {"type": "string", "description": "The email subject"},
                            "message": {"type": "string", "description": "The email message"},
                        },
                        "required": ["to", "subject", "message"],
                    },
                },
            ]
        )
        email_details = response.choices[0].message.get('function_call', {}).get('arguments')
        return email_details

    #send email
    def send_email(self, token, to, subject, message):
        creds = Credentials.from_authorized_user_info(token)
        service = build('gmail', 'v1', credentials=creds)
        message = self.create_message("me", to, subject, message)
        self.send_message(service, message)

    def create_message(self, sender, to, subject, message_text):
        message = MIMEMultipart('alternative')
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject
        msg = MIMEText(message_text, 'html')
        message.attach(msg)
        raw_message = base64.urlsafe_b64encode(message.as_bytes())
        raw_message = raw_message.decode()
        return {'raw': raw_message}

    def send_message(self, service, message):
        user_id = "me"
        try:
            message = service.users().messages().send(userId=user_id, body=message).execute()
            return message
        except Exception as e:
            response = ('An error occurred: %s' % e)
            return response

    #General Update
    def general_update(self, token):
        # Fetch new data
        email_data_str = self.fetch_gmail(token)
        email_data_str = email_data_str[:10000]  # limit to the first 10000 characters

        events_str = self.get_calendar(token)
        events_str = events_str[:10000]  # limit to the first 10000 characters

        tasks = self.list_tasks(token)
        tasks = dict(list(tasks.items())[:10])  # limit to the first 10 items

        # Combine the truncated data
        combined_data = {
            'email_data': email_data_str,
            'events': events_str,
            'tasks': tasks,
        }
        combined_data = json.dumps(combined_data)




        combined_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            temperature=0,
            messages=[{"role": "system", "content": f"You are my personal A.I assistant. You behave exactly like JARVIS from Iron Man, but your name is A.D.A.M. - Automated Digital Assistant Mainframe. My name is {self.user_name} and I live in {self.city}. Today's datetime is {self.datetime_str}. Keep your responses concise, short and quippy. Give me a briefing of my newest emails, upcoming events for today and tasks based on the data provided. Summarize your response and keep it short."},
            {"role": "assistant", "content": json.dumps(combined_data)}
            ]
        )

        # Add the new assistant message to the conversation history
        update_content = combined_response.choices[0].message['content']
        self.conversation_history.append({"role": "assistant", "content": update_content})

        # If the conversation history is too long, remove the oldest messages
        while len(self.conversation_history) > MAX_TURNS:
            self.conversation_history.pop(0)

        return update_content

def process_command(user_name, prompt, token, conversation_history, latitude, longitude, city):
    user_session = UserSession(user_name, conversation_history, latitude, longitude, city)
    command_content = user_session.generate_command(prompt)
    print(command_content)
    commands = command_content.split('->')
    responses = []  # To store responses for each command

    # Dictionary to map commands to their corresponding functions
    command_functions = {
        "none": user_session.generate_response,
        "regularresponse": user_session.generate_response,
        "websearch": lambda: user_session.generate_search_result_response(user_session.web_search(user_session.generate_search_query(prompt))),
        "getweather": user_session.get_weather,
        "getcalendar": lambda: user_session.read_events(user_session.get_calendar(token)),
        "createevents": lambda: user_session.add_events_to_calendar(token, user_session.generate_event_details(token, prompt)) or "I have updated your calendar.",
        "gettasks": lambda: user_session.read_tasks(user_session.list_tasks(token)),
        "createtask": lambda: user_session.add_task(token, json.loads(user_session.generate_task_details())) or "I have added the task to your to-do list.",
        "deletetask": lambda: user_session.delete_task(token, json.loads(user_session.generate_delete_command(user_session.list_tasks(token)))) or "The task has been deleted.",
        "getemail": lambda: user_session.read_emails(user_session.fetch_gmail(token)),
        "draftemail": lambda: user_session.conversation_history.append({
            "role": "assistant", 
            "content": f"Here's the email I will send:\nTo: {email_details['to']}\nSubject: {email_details['subject']}\nMessage: {email_details['message']}\nShall I send it?"
        }) or f"Here's the email I will send:\nTo: {email_details['to']}\nSubject: {email_details['subject']}\nMessage: {email_details['message']}\n\nShall I send it?",
        "confirmsendemail": lambda: user_session.send_email(token, **json.loads(user_session.generate_email_details(token, prompt))) or "Thank you, the email has been sent.",
        "briefing": lambda: user_session.general_update(token),
    }

    for command_content in commands:
        command_content = command_content.strip()
        func = command_functions.get(command_content, user_session.generate_response)
        responses.append(func())

    combined_response = "<br><br>".join(responses)  # Joining all responses with a newline in between
    return combined_response, user_session.conversation_history