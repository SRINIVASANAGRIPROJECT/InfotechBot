import os
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from a .env file
load_dotenv()

# Get your Telegram bot token and Google API key from environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize the generative model
model = genai.GenerativeModel('gemini-1.5-flash')

# Load the courses data from the CSV file
try:
    df_courses = pd.read_csv('courses.csv')
except FileNotFoundError:
    print("Error: 'courses.csv' file not found. Please make sure it's in the same directory as main.py.")
    df_courses = pd.DataFrame() # Create an empty DataFrame to avoid errors

# Handler for the /start command and welcome messages
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message and asks how to help."""
    await update.message.reply_text(
        "Hello! I am the Infotech company's course bot. How can I help you today?\n\n"
        "You can ask me about our courses, or ask a general question like 'what is business analytics?'."
    )

# Handler for "thank you" messages
async def thank_you(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Responds to 'thank you' messages."""
    await update.message.reply_text("You're welcome! Let me know if you need anything else.")

# Handler for getting a list of courses
async def get_courses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a list of all available courses."""
    if not df_courses.empty:
        course_list = "Available Courses:\n\n"
        course_names = df_courses['course_name'].tolist()
        for name in course_names:
            course_list += f"• {name}\n"
        await update.message.reply_text(course_list)
    else:
        await update.message.reply_text("I'm sorry, I don't have a list of courses right now.")

# Function to generate a response for a specific course query using Google API
async def generate_course_response_with_gemini(course_name: str, user_message: str) -> str:
    """Generates a response for a specific course query using the Gemini API."""
    prompt = f"Using the following course details as a guide, please answer the user's question. If you are asked about the syllabus, make up a concise one in a professional format. Be concise. \n\nCourse: {course_name}\nQuestion: {user_message}\n\nCourse details:\n{df_courses[df_courses['course_name'] == course_name].to_string(index=False)}"
    
    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating content: {e}")
        return "I'm sorry, I'm unable to answer that question at the moment. Please try again later."

# Function to generate a response for a general query using Google API
async def generate_general_response_with_gemini(user_message: str) -> str:
    """Generates a response for a general query using the Gemini API."""
    prompt = f"Answer the following question in a concise and professional manner: {user_message}"
    
    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating content: {e}")
        return "I'm sorry, I'm unable to answer that question at the moment. Please try again later."

# Handler for all text messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Analyzes the user's message and provides a relevant answer."""
    user_message = update.message.text.lower()
    
    # Check for "thank you" keywords
    if "thank" in user_message or "thanks" in user_message:
        await thank_you(update, context)
        return

    # Check for a specific course name in the user's message
    found_course = None
    if not df_courses.empty:
        for course_name in df_courses['course_name'].tolist():
            if course_name.lower() in user_message:
                found_course = course_name
                break

    if found_course:
        await update.message.reply_text("Thinking... Please wait a moment while I generate a response for you.")
        ai_response = await generate_course_response_with_gemini(found_course, user_message)
        await update.message.reply_text(ai_response, parse_mode='Markdown')
        return
    else:
        # If no course is found, treat it as a general question
        await update.message.reply_text("Thinking... Please wait a moment while I get more information for you.")
        ai_response = await generate_general_response_with_gemini(user_message)
        await update.message.reply_text(ai_response, parse_mode='Markdown')
        return

def main() -> None:
    """Starts the bot."""
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN environment variable not found.")
        return

    # Create the Application and pass your bot's token.
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Add command and message handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND) & (filters.Regex(r'(?i)hi|hello|hey|welcome')), start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND) & filters.Regex(r'(?i)course|courses|what courses|list of courses'), get_courses))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # Run the bot
    print("Bot is polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
