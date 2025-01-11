import asyncio
import csv
from dotenv import load_dotenv
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

# Load environment variables from .env file (credentials)
load_dotenv()

# Credentials
api_id = '26483958'
api_hash = 'b0cf68ff6a7c406e41b3833aabc2dc3e'
bot_username = '@isquestionsbot'

# Initialize Telegram client
client = TelegramClient('session_name', api_id, api_hash)

current_question = None
questions = []
number_of_questions = 10

csv_file = 'questions.csv'
with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow(["Question", "Answer"])

@client.on(events.NewMessage(from_users=bot_username))
async def handle_message(event):

    global current_question
    global questions

    try:
        message = event.raw_text
        answer = None

        if event.message.buttons:
            for row in event.message.buttons:
                for button in row:
                    if "1" in button.text:
                        await asyncio.sleep(5)
                        await button.click()
                        return button.text
            print("No button containing '1' was found.")

        if message.endswith("."):
            print(f"Received Message: {message}")
            current_question = message

        else:
            if "טעות" in message:
                try:
                    answer = message.split("התשובה הנכונה היא")[1].split()[1]
                    print(f"Correct Answer: {answer}")
                except IndexError:
                    print("Error parsing the correct answer.")
            if "טעות" not in message and "תודה" not in message and "?" not in message:
                answer = "1"
                print("Correct Answer: 1")

        if current_question and answer:
            if current_question not in questions:
                print("Adding to csv file")
                with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    writer.writerow([current_question, answer])
                questions.append(current_question)
            if len(questions) >= number_of_questions:
                print(f"Reached {number_of_questions} unique questions. Stopping...")
                await client.disconnect()
                return

    except Exception as e:
        print(f"Error handling message: {e}")

async def interact_with_bot():

    async with client:

        while True:
            try:
                await client.send_message(bot_username, "/start")
                await asyncio.sleep(20)

            # Handling in case of too many API calls
            except FloodWaitError as e:
                print(f"FloodWaitError: Need to wait for {e.seconds} seconds.")
                await asyncio.sleep(e.seconds)

# Start the interaction
try:
    client.loop.run_until_complete(interact_with_bot())
except KeyboardInterrupt:
    print("Script interrupted by user.")
