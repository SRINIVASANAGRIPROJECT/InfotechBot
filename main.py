import os
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Get your Telegram bot token and Google Project ID from environment variables
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
# GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID") # Uncomment if you're using Google APIs

# Load the courses data from the CSV file
try:
    df_courses = pd.read_csv('courses.csv')
except FileNotFoundError:
    print("Error: 'courses.csv' file not found. Please make sure it's in the same directory as main.py.")
    df_courses = pd.DataFrame() # Create an empty DataFrame to avoid errors

# Handler for the /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message with instructions."""
    await update.message.reply_text(
        "Hello! I'm BrightLearn's Course Bot. "
        "I can help you find information about our courses.\n\n"
        "Here are some things you can ask:\n"
        "- 'What courses are available?'\n"
        "- 'Tell me about the Data Science Pro course.'\n"
        "- 'What's the fee for the Digital Marketing course?'\n"
        "- 'Who is the mentor for the Cloud Computing course?'"
    )

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

# Handler for general text messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Analyzes the user's message and provides a relevant answer from the CSV."""
    user_message = update.message.text.lower()
    response = "I'm sorry, I couldn't find information for that. Please try asking about a specific course or ask 'what courses are available'."

    if not df_courses.empty:
        # Look for a specific course name in the user's message
        for index, row in df_courses.iterrows():
            course_name_lower = row['course_name'].lower()
            if course_name_lower in user_message:
                # Check for specific queries about the course
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
                break
    
    await update.message.reply_text(response, parse_mode='Markdown')

def main() -> None:
    """Starts the bot."""
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN environment variable not found.")
        return

    # Create the Application and pass your bot's token.
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Add command and message handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND) & filters.Regex(r'(?i)course|courses|what courses|list of courses'), get_courses))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    # Run the bot
    print("Bot is polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
