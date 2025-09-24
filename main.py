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
        "You can ask me about our courses, their fees, mentors, or even the syllabus for any course."
    )

# New handler for "thank you" messages
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

# New function to generate a syllabus
async def generate_syllabus(course_name: str) -> str:
    """Generates a detailed syllabus for a given course using the Gemini API."""
    prompt = f"Create a detailed 6-8 week syllabus for a professional course titled '{course_name}'. Include weekly topics, key concepts, and a final project idea. The language should be concise and professional."
    
    try:
        response = await model.generate_content_async(prompt)
        return response.text
    except Exception as e:
        print(f"Error generating content: {e}")
        return "I'm sorry, I couldn't generate a syllabus for that course. Please try again later."

# Handler for general text messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Analyzes the user's message and provides a relevant answer from the CSV."""
    user_message = update.message.text.lower()
    
    # Check for "thank you" keywords
    if "thank" in user_message or "thanks" in user_message:
        await thank_you(update, context)
        return

    response = "I'm sorry, I couldn't find information for that. Please try asking about a specific course or ask 'what courses are available'."

    if not df_courses.empty:
        # Look for a specific course name in the user's message
        for index, row in df_courses.iterrows():
            course_name_lower = row['course_name'].lower()
            if course_name_lower in user_message:
                
                # Check for "syllabus" query
                if "syllabus" in user_message:
                    await update.message.reply_text("Generating a syllabus for you. This might take a moment...")
                    syllabus = await generate_syllabus(row['course_name'])
                    await update.message.reply_text(syllabus, parse_mode='Markdown')
                    return
                
                # Check for other specific queries about the course
                if "mentor" in user_message or "trainer" in user_message:
                    response = (
                        f"The mentor for **{row['course_name']}** is {row['mentor_name']} "
                        f"from {row['mentor_company']}."
                    )
                elif "fee" in user_message or "cost" in user_message:
                    response = f"The fee for **{row['course_name']}** is ₹{row['fee']}."
                elif "duration" in user_message or "long" in user_message:
                    response = f"The **{row['course_name']}** course has a duration of {row['duration']}."
                elif "placement" in user_message or "placed" in user_message or "package" in user_message:
                    try:
                        students_finished = int(row['students_finished'])
                        students_placed_offer = int(row['students_placed_offer'])
                        if students_finished > 0:
                            placement_rate = round((students_placed_offer / students_finished) * 100)
                            response = (
                                f"For the **{row['course_name']}** course, {students_placed_offer} students "
                                f"received offers out of {students_finished} who finished. "
                                f"The average package is {row['average_package']}."
                            )
                        else:
                            response = f"Placement data for the **{row['course_name']}** course is not available yet."
                    except (ValueError, TypeError):
                        response = f"Placement data for the **{row['course_name']}** course is not in a valid format."

                elif "sessions" in user_message:
                    response = (
                        f"The **{row['course_name']}** course includes {row['no_of_online_sessions']} online sessions "
                        f"and {row['no_of_offline_sessions']} offline sessions."
                    )
                elif "language" in user_message:
                    response = f"The **{row['course_name']}** course is taught in {row['course_language']}."
                elif "rating" in user_message:
                    response = f"The **{row['course_name']}** course has a rating of {row['course_rating']} ⭐."
                else:
                    # If no specific keyword is found, provide a full summary
                    response = (
                        f"**{row['course_name']}**\n\n"
                        f"**Duration:** {row['duration']}\n"
                        f"**Fee:** ₹{row['fee']}\n"
                        f"**Mentor:** {row['mentor_name']} ({row['mentor_designation']} at {row['mentor_company']})\n"
                        f"**Sessions:** {row['no_of_online_sessions']} online, {row['no_of_offline_sessions']} offline\n"
                        f"**Real-time Project:** {row['realtime_project']}\n"
                        f"**Average Package:** {row['average_package']}\n"
                        f"**Placement Companies:** {row['placement_company'].replace(';', ', ')}\n"
                        f"**Course Rating:** {row['course_rating']} ⭐"
                    )
                
                await update.message.reply_text(response, parse_mode='Markdown')
                return
    
    await update.message.reply_text(response)

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
