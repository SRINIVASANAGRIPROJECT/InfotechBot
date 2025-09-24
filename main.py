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
        "You can ask me about our courses, their fees, mentors, or even a general question like 'which course is best?'."
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
    found_course_data = None
    if not df_courses.empty:
        for _, row in df_courses.iterrows():
            if row['course_name'].lower() in user_message:
                found_course_data = row
                break

    if found_course_data is not None:
        # User is asking about a specific course, handle with CSV data first
        if "mentor" in user_message or "trainer" in user_message:
            response = f"The mentor for **{found_course_data['course_name']}** is {found_course_data['mentor_name']} from {found_course_data['mentor_company']}."
        elif "fee" in user_message or "cost" in user_message:
            response = f"The fee for **{found_course_data['course_name']}** is ₹{found_course_data['fee']}."
        elif "duration" in user_message or "long" in user_message:
            response = f"The **{found_course_data['course_name']}** course has a duration of {found_course_data['duration']}."
        elif "placement" in user_message or "placed" in user_message or "package" in user_message:
            response = (
                f"For the **{found_course_data['course_name']}** course, {found_course_data['students_placed_offer']} students "
                f"received offers out of {found_course_data['students_finished']} who finished. "
                f"The average package is {found_course_data['average_package']}."
            )
        elif "sessions" in user_message:
            response = (
                f"The **{found_course_data['course_name']}** course includes {found_course_data['no_of_online_sessions']} online sessions "
                f"and {found_course_data['no_of_offline_sessions']} offline sessions."
            )
        elif "syllabus" in user_message:
            # Use AI for syllabus, but provide a custom prompt
            await update.message.reply_text("Thinking... Please wait a moment while I generate a syllabus for you.")
            prompt = f"Create a detailed 6-8 week syllabus for a professional course titled '{found_course_data['course_name']}'. Include weekly topics, key concepts, and a final project idea. The language should be concise and professional."
            ai_response = await generate_general_response_with_gemini(prompt)
            await update.message.reply_text(ai_response, parse_mode='Markdown')
            return
        else:
            # If no specific keyword is found, provide a full summary
            response = (
                f"**{found_course_data['course_name']}**\n\n"
                f"**Duration:** {found_course_data['duration']}\n"
                f"**Fee:** ₹{found_course_data['fee']}\n"
                f"**Mentor:** {found_course_data['mentor_name']} ({found_course_data['mentor_designation']} at {found_course_data['mentor_company']})\n"
                f"**Sessions:** {found_course_data['no_of_online_sessions']} online, {found_course_data['no_of_offline_sessions']} offline\n"
                f"**Real-time Project:** {found_course_data['realtime_project']}\n"
                f"**Average Package:** {found_course_data['average_package']}\n"
                f"**Placement Companies:** {found_course_data['placement_company'].replace(';', ', ')}\n"
                f"**Course Rating:** {found_course_data['course_rating']} ⭐"
            )
        
        await update.message.reply_text(response, parse_mode='Markdown')
        return

    else:
        # If no course is found, check for general questions and use the AI
        if "which course is best" in user_message:
            prompt = "In a professional and helpful tone, explain that the 'best' course depends on a person's individual interests, career goals, and prior experience. Suggest that they review the syllabus of various courses to find the best fit."
            await update.message.reply_text("Thinking... Please wait a moment.")
            ai_response = await generate_general_response_with_gemini(prompt)
            await update.message.reply_text(ai_response, parse_mode='Markdown')
            return
            
        elif "companies" in user_message and ("hire" in user_message or "job" in user_message):
            # Extract the job role from the user's message
            job_roles = ['ml engineer', 'data scientist', 'software engineer', 'cloud architect']
            found_role = None
            for role in job_roles:
                if role in user_message:
                    found_role = role
                    break
            
            if found_role:
                prompt = f"Name some of the top companies that hire for the role of a {found_role}."
                await update.message.reply_text("Thinking... Please wait a moment.")
                ai_response = await generate_general_response_with_gemini(prompt)
                await update.message.reply_text(ai_response, parse_mode='Markdown')
                return
        
        # Default fallback for questions not handled above
        await update.message.reply_text("I'm sorry, I couldn't find information for that. Please try asking about a specific course or ask 'what courses are available'.")

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
