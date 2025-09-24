# bot.py

from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
import pandas as pd
import openai
from fpdf import FPDF
import os

# --- Environment Variables ---
TOKEN = os.environ.get("BOT_TOKEN")        # Telegram Bot token
openai.api_key = os.environ.get("OPENAI_API_KEY")  # OpenAI API key

# --- Load CSV ---
courses_df = pd.read_csv('infotech_courses_realistic.csv')

# --- Common Responses ---
common_responses = {
    "good morning": "Good morning! ☀️ Welcome to Infotech. How can I assist you today?",
    "hello": "Hello! 👋 I’m your Infotech assistant. How may I help you?",
    "hi": "Hi there! I’m Infotech’s course assistant. What would you like to know?",
    "bye": "Goodbye! Have a great day! Feel free to ask anytime about our courses.",
    "refund": "We ensure a smooth refund process. Kindly share your registration details, and we will assist you promptly."
}

# --- CSV Lookup ---
def lookup_course(user_text):
    for _, row in courses_df.iterrows():
        if row['course_name'].lower() in user_text.lower():
            return (
                f"Course: {row['course_name']}\n"
                f"Duration: {row['duration']}\n"
                f"Fee: ₹{row['fee']}\n"
                f"Mentor: {row['mentor_name']} ({row['mentor_designation']}, {row['mentor_company']})\n"
                f"Online: {row['no_of_online_sessions']}, Offline: {row['no_of_offline_sessions']}\n"
                f"Project: {row['realtime_project']}\n"
                f"Students Enrolled: {row['students_enrolled']}, Finished: {row['students_finished']}\n"
                f"Placed: {row['students_placed_offer']} in {row['placement_company']} with Avg Package: {row['average_package']}\n"
                f"Language: {row['course_language']}, Rating: {row['course_rating']}"
            )
    return None

# --- Generate Syllabus PDF ---
def generate_syllabus(course_name):
    topics = ["Introduction & Basics", "Core Concepts", "Hands-on Practice", "Advanced Techniques", "Real-time Project", "Summary & Next Steps"]
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"{course_name} - Syllabus", ln=True, align="C")
    pdf.ln(10)
    pdf.set_font("Arial", '', 12)
    for idx, topic in enumerate(topics, start=1):
        pdf.cell(0, 8, f"{idx}. {topic}", ln=True)
    file_name = f"{course_name.replace(' ','_')}_syllabus.pdf"
    pdf.output(file_name)
    return file_name

# --- Message Handler ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.lower()

    # 1️⃣ Common responses
    for keyword, response in common_responses.items():
        if keyword in user_text:
            await update.message.reply_text(response)
            return

    # 2️⃣ Syllabus request
    if "syllabus" in user_text:
        course_name = None
        for _, row in courses_df.iterrows():
            if row['course_name'].lower() in user_text:
                course_name = row['course_name']
                break
        if not course_name:
            course_name = "Requested Course"
        pdf_file = generate_syllabus(course_name)
        await update.message.reply_document(open(pdf_file,'rb'))
        return

    # 3️⃣ Course lookup
    local_answer = lookup_course(user_text)
    if local_answer:
        await update.message.reply_text(local_answer)
        return

    # 4️⃣ AI fallback
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a professional Infotech chatbot answering course-related queries."},
            {"role": "user", "content": user_text}
        ]
    )
    response = completion.choices[0].message['content'].strip()
    await update.message.reply_text(response)

# --- Start Command ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! I’m your Infotech bot. Ask me about courses or any queries.")

# --- Run Bot ---
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Bot running...")
app.run_polling()
