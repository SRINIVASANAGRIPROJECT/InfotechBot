import os
import pandas as pd
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load environment variables (locally)
load_dotenv()

TOKEN = os.environ.get("BOT_TOKEN")
GROK_KEY = os.environ.get("GROK_API_KEY")

# Load CSV
df = pd.read_csv("infotech_courses_realistic.csv")

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hi! I’m your Infotech Assistant 🤖. Ask me anything about our courses."
    )

# Function to search CSV
def search_course(query):
    query = query.lower()
    for _, row in df.iterrows():
        if row['course_name'].lower() in query:
            return (f"Course: {row['course_name']}\n"
                    f"Duration: {row['duration']}\n"
                    f"Fee: {row['fee']}\n"
                    f"Mentor: {row['mentor_name']} ({row['mentor_designation']} at {row['mentor_company']})\n"
                    f"Online Sessions: {row['no_of_online_sessions']}, Offline Sessions: {row['no_of_offline_sessions']}\n"
                    f"Realtime Project: {row['realtime_project']}\n"
                    f"Students Enrolled: {row['students_enrolled']}, Finished: {row['students_finished']}, Placed: {row['students_placed_offer']}\n"
                    f"Average Package: {row['average_package']} at {row['placement_company']}\n"
                    f"Course Language: {row['course_language']}, Rating: {row['course_rating']}/5")
    return None

# Function to call Grok API
def grok_response(prompt):
    url = "https://api.x.ai/v1/grok"
    headers = {"Authorization": f"Bearer {GROK_KEY}"}
    data = {"prompt": prompt}
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        return response.json().get("response", "Sorry, I couldn't understand that.")
    except:
        return "Sorry, Grok is not available at the moment."

# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.lower()

    # Greetings
    if any(greet in user_text for greet in ["hi", "hello", "good morning", "good evening"]):
        await update.message.reply_text("Hello! How can I assist you with our courses today?")
        return

    # Check CSV first
    course_info = search_course(user_text)
    if course_info:
        await update.message.reply_text(course_info)
        return

    # Fallback to Grok AI
    response = grok_response(user_text)
    await update.message.reply_text(response)

# Bot setup
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot running...")
app.run_polling()
