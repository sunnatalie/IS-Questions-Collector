import asyncio
import csv
import os
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

# Load environment variables from .env file (credentials) 
load_dotenv()

# Credentials
api_id = os.getenv('TELEGRAM_API_ID')
api_hash = os.getenv('TELEGRAM_API_HASH')
bot_username = '@isquestionsbot'

# Initialize Telegram client
client = TelegramClient('session_name', api_id, api_hash)

# Global variables
current_question = None
current_question_without_answer_choices = None
questions = []
rawquestions = []
number_of_questions = 501

# Initialize CSV files to store questions and answers
csv_file = 'questions.csv'
with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["Question", "Answer"])

csv_file_raw = 'rawquestions.csv'
with open(csv_file_raw, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["rawQuestion", "rawAnswer"])

# Event handler for messages received from the bot
@client.on(events.NewMessage(from_users=bot_username))
async def handle_message(event):
    """
    Handles incoming messages from the bot, extracts questions and answers,
    and saves them to a CSV file.
    """
    global current_question
    global current_question_without_answer_choices
    global questions

    try: 
        message = event.raw_text
        answer = None

        print(message)
        
        # If the message has buttons, attempt to click the one containing "1"
        if event.message.buttons:
            for row in event.message.buttons:
                for button in row:
                    if "1" in button.text:
                        await asyncio.sleep(6)
                        await button.click()
                        return button.text
            print("No button containing '1' was found.")

        # Check if the message is a question (ends with a period)
        if message.endswith("."):

            print(f"Received Message: {message}")
            split_message = message.splitlines()

            def contains_number(s):
                return '.1' in s or '1.' in s # All of the answer choices has either .1 or 1. in the beginning (sometimes reverse formatting due to the questions being in Hebrew)

            # Only get the strings before the answer choices
            def get_strings_before_number(strings):
            # Find the index of the first string containing a number
                index_with_number = next((i for i, s in enumerate(strings) if contains_number(s)), len(strings))
                # Get strings before the first number-containing string
                return strings[:index_with_number]
            
            current_question = message
            current_question_without_answer_choices = get_strings_before_number(split_message)

            print(f'Question: {get_strings_before_number(split_message)}')
            
        # Extract the correct answer
        else:
            # If we're wrong, the message will contain the word טעות
            if "טעות" in message:
                try:
                    answer = message.split("התשובה הנכונה היא")[1].split()[1]
                    print(f"Correct Answer: {answer}")
                except IndexError:
                    print("Error parsing the correct answer.")
            # If we're right (meaning that the button we pressed, 1, is correct), record 1 as the answer
            if "טעות" not in message and "תודה" not in message and "?" not in message:
                answer = "1"
                print("Correct Answer: 1")

        # Save relevant answer choices to CSV file
        if current_question and answer:
            # Save raw questions without filtering
            with open(csv_file_raw, mode='a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([current_question, answer])
                rawquestions.append(current_question_without_answer_choices)
            print(f"Number of raw: {len(rawquestions)}")
            # Skip survey questions
            if any('שאלה זו היא לצרכי מחקר' in x for x in current_question_without_answer_choices):
                print("This question is a survey question! No processing")
            # Skip duplicate questions
            elif any(" ".join(current_question_without_answer_choices) == " ".join(q) for q in questions):
                print("This question has already been processed! No processing")
            # Save the file
            else:
                print("New question found. Adding to csv file")
                with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow([current_question, answer])
                questions.append(current_question_without_answer_choices)
                current_question = None
                answer = None
            print(f"Number of questions processed: {len(questions)}")

            # Stop the script if the desired number of unique questions is reached
            if len(questions) >= number_of_questions:
                print(f"Reached {number_of_questions} unique questions. Stopping...")
                await client.disconnect()
                return

    except Exception as e:
        print(f"Error handling message: {e}")

async def interact_with_bot():
    """
    Sends a "/start" command to the bot in a loop, ensuring interaction.
    Handles rate limits using FloodWaitError.
    """
    async with client:

        while True:
            try:
                await client.send_message(bot_username, "/start")
                await asyncio.sleep(1000)

            # Handling in case of too many API calls
            except FloodWaitError as e:
                print(f"FloodWaitError: Need to wait for {e.seconds} seconds.")
                await asyncio.sleep(e.seconds)

# Main execution with timeout
async def main():
    try:
        # Run the bot interaction for a maximum of 6 hours
        await asyncio.wait_for(interact_with_bot(), timeout=6 * 60 * 60)
    except asyncio.TimeoutError:
        print("Script stopped after reaching the 6-hour limit.")
    finally:
        await client.disconnect()

# Run the interaction loop
try:
    client.loop.run_until_complete(main())
except KeyboardInterrupt:
    print("Script interrupted by user.")
