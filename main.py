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
questions = []
number_of_questions = 10

# Initialize CSV file to store questions and answers
csv_file = 'questions.csv'
with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["Question", "Answer"])

# Event handler for messages received from the bot
@client.on(events.NewMessage(from_users=bot_username))
async def handle_message(event):
    """
    Handles incoming messages from the bot, extracts questions and answers,
    and saves them to a CSV file.
    """
    global current_question
    global questions

    try:
        message = event.raw_text
        answer = None
        
        # If the message has buttons, attempt to click the one containing "1"
        if event.message.buttons:
            for row in event.message.buttons:
                for button in row:
                    if "1" in button.text:
                        await asyncio.sleep(4)
                        await button.click()
                        return button.text
            print("No button containing '1' was found.")

        # Check if the message is a question (ends with a period)
        if message.endswith("."):
            print(f"Received Message: {message}")
            current_question = message

        # Extract the correct answer
        else:
            # If we're wrong, the message with contain the word טעות
            if "טעות" in message:
                try:
                    answer = message.split("התשובה הנכונה היא")[1].split()[1]
                    print(f"Correct Answer: {answer}")
                except IndexError:
                    print("Error parsing the correct answer.")
            # If we're right (meaing that the button we pressed, 1, is correct), record 1 as the answer
            if "טעות" not in message and "תודה" not in message and "?" not in message:
                answer = "1"
                print("Correct Answer: 1")

        # Save the question and answer to the CSV if not already processed
        if current_question and answer:
            if current_question not in questions:
                print("Adding to csv file")
                with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow([current_question, answer])
                questions.append(current_question)
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
                await asyncio.sleep(20)

            # Handling in case of too many API calls
            except FloodWaitError as e:
                print(f"FloodWaitError: Need to wait for {e.seconds} seconds.")
                await asyncio.sleep(e.seconds)

# Run the interaction loop
try:
    client.loop.run_until_complete(interact_with_bot())
except KeyboardInterrupt:
    print("Script interrupted by user.")
