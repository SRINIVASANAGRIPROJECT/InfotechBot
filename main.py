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

# Hardcoded syllabuses for reliable, quick responses
SYLLABUSES = {
    'Data Science Pro': """
**Week 1-2: Foundations of Data Science**
- Introduction to Data Science, Python for Data Science, and Jupyter Notebooks.
- Statistics and Probability for Data Science.

**Week 3-4: Data Wrangling and Visualization**
- Data Cleaning, Pre-processing, and Manipulation with Pandas.
- Data Visualization with Matplotlib and Seaborn.

**Week 5-6: Machine Learning Fundamentals**
- Supervised Learning (Regression, Classification).
- Unsupervised Learning (Clustering).

**Week 7-8: Advanced Topics & Capstone Project**
- Introduction to Deep Learning and Neural Networks.
- Natural Language Processing (NLP) or Computer Vision basics.
- Capstone project development.
""",
    'Full Stack Web Dev': """
**Week 1-2: Frontend Development**
- HTML5 and CSS3 fundamentals.
- Introduction to JavaScript, DOM manipulation, and modern ES6 features.

**Week 3-4: Backend Development (Node.js)**
- Node.js and Express.js for building a server.
- RESTful APIs and API design.

**Week 5-6: Databases & Deployment**
- Working with MongoDB (or a similar NoSQL database).
- User authentication and security.
- Deployment strategies on platforms like Railway.

**Week 7-8: Frameworks & Final Project**
- Introduction to a modern framework (e.g., React or Vue.js).
- Building a full-stack application from scratch.
""",
    'Digital Marketing': """
**Week 1-2: Introduction and Core Concepts**
- Digital Marketing Fundamentals and strategy.
- Search Engine Optimization (SEO): On-page and off-page techniques.

**Week 3-4: Paid Advertising and Social Media**
- Search Engine Marketing (SEM) with Google Ads.
- Social Media Marketing (SMM) on platforms like Facebook and Instagram.

**Week 5-6: Content, Email, and Analytics**
- Content Marketing and Copywriting.
- Email Marketing strategies and automation.
- Google Analytics for tracking and reporting.

**Week 7-8: Specialization & Final Campaign**
- In-depth look at a specific area like Video Marketing or Affiliate Marketing.
- Creating and analyzing a comprehensive digital marketing campaign.
""",
    'Cloud Computing with AWS': """
**Week 1-2: AWS Fundamentals**
- Introduction to Cloud Computing and the AWS ecosystem.
- Core services: EC2, S3, IAM.

**Week 3-4: Networking and Databases**
- Virtual Private Cloud (VPC) and network security.
- Databases in AWS (RDS, DynamoDB).

**Week 5-6: Serverless and Management**
- AWS Lambda and serverless architecture.
- Monitoring and logging with CloudWatch.

**Week 7-8: Security and Certification Prep**
- Security best practices and identity management.
- Exam preparation for the AWS Certified Cloud Practitioner.
""",
    'Cyber Security Essentials': """
**Week 1-2: Foundational Concepts**
- Introduction to cybersecurity, threats, and vulnerabilities.
- Principles of network security and firewalls.

**Week 3-4: System & Application Security**
- Securing operating systems (Windows, Linux).
- Common application attacks and countermeasures.

**Week 5-6: Cryptography and Cloud Security**
- Principles of cryptography and public key infrastructure (PKI).
- Securing cloud environments and cloud-based services.

**Week 7-8: Incident Response & Ethics**
- Incident response and disaster recovery planning.
- Legal and ethical issues in cybersecurity.
""",
    'UI/UX Design Fundamentals': """
**Week 1-2: Principles of UI/UX**
- Introduction to UI vs. UX.
- The Design Thinking process.

**Week 3-4: User Research & Prototyping**
- Conducting user interviews and creating personas.
- Wireframing and creating interactive prototypes with Figma.

**Week 5-6: Visual Design & Handoff**
- Typography, color theory, and visual hierarchy.
- Creating a design system and handing off designs to developers.

**Week 7-8: Case Studies & Portfolio**
- Analyzing real-world design case studies.
- Building a professional portfolio project.
""",
    'Advanced Python Programming': """
**Week 1-2: Advanced Data Structures**
- In-depth look at lists, dictionaries, and sets.
- Advanced functions and decorators.

**Week 3-4: Object-Oriented Programming (OOP)**
- Classes, objects, inheritance, and polymorphism.
- Design patterns in Python.

**Week 5-6: Concurrency and Networking**
- Multithreading and multiprocessing.
- Building network applications and working with APIs.

**Week 7-8: Web Scraping & Final Project**
- Web scraping with BeautifulSoup and Scrapy.
- Final project applying advanced Python concepts.
""",
    'Project Management (PMP)': """
**Week 1-2: PMP Fundamentals**
- Introduction to project management and the PMP framework.
- Project life cycles and agile vs. waterfall methodologies.

**Week 3-4: Process Groups**
- Initiation, planning, and execution processes.
- Monitoring, controlling, and closing processes.

**Week 5-6: Knowledge Areas**
- Scope, schedule, cost, and quality management.
- Resource, communication, and risk management.

**Week 7-8: Professional Responsibility**
- Stakeholder management and professional ethics.
- Mock exams and final exam preparation.
""",
    'Blockchain Development': """
**Week 1-2: Blockchain & Crypto Fundamentals**
- How blockchain technology works (hashing, blocks, and chains).
- Cryptography and decentralized ledgers.

**Week 3-4: Ethereum and Smart Contracts**
- Introduction to Ethereum and the Solidity programming language.
- Writing, testing, and deploying smart contracts.

**Week 5-6: DApp Development**
- Building decentralized applications (DApps).
- Interacting with smart contracts from a web interface.

**Week 7-8: Advanced Topics & Project**
- Introduction to other blockchain platforms (e.g., Polygon, Hyperledger).
- Final project: building a simple DApp.
""",
    'Graphic Design Masterclass': """
**Week 1-2: Foundational Principles**
- Principles of design (balance, rhythm, emphasis).
- Color theory and typography.

**Week 3-4: Mastering Adobe Suite**
- Introduction to Adobe Photoshop and Illustrator.
- Creating vector graphics and editing photos.

**Week 5-6: Branding & Marketing Collateral**
- Designing logos and brand identities.
- Creating social media graphics and marketing materials.

**Week 7-8: Portfolio & Professional Practice**
- Developing a professional portfolio.
- Client communication and project management.
""",
    'Business Analytics': """
**Week 1-2: The Role of Analytics**
- Introduction to business analytics and its importance.
- Foundational statistics and data concepts.

**Week 3-4: Data Analysis & Visualization**
- Data manipulation and analysis with Excel and Python (Pandas).
- Data visualization with Tableau or Power BI.

**Week 5-6: Predictive Analytics**
- Introduction to predictive modeling.
- Regression and forecasting.

**Week 7-8: Capstone Project & Strategy**
- Applying analytics to a real-world business case study.
- Communicating data-driven insights to stakeholders.
""",
    'iOS App Development': """
**Week 1-2: Swift Language Basics**
- Introduction to Xcode and Swift programming.
- Variables, data types, control flow, and functions.

**Week 3-4: UI/UX for iOS**
- Building user interfaces with SwiftUI.
- Navigation, lists, and forms.

**Week 5-6: Data & Networking**
- Handling data in iOS apps.
- Making API calls and fetching data from the internet.

**Week 7-8: Advanced Features & Deployment**
- Working with Core Data for local storage.
- App Store submission process and final project.
""",
    'Machine Learning Engineering': """
**Week 1-2: ML Foundations**
- Review of machine learning concepts (supervised, unsupervised).
- Setting up a development environment (Python, TensorFlow, PyTorch).

**Week 3-4: Model Development & Training**
- Building and training neural networks.
- Model evaluation and optimization.

**Week 5-6: MLOps**
- Version control for models and data.
- Deploying models to production.

**Week 7-8: Advanced Topics & Project**
- Introduction to MLOps tools (e.g., Kubeflow).
- Final project on a real-world machine learning problem.
""",
    'Content Writing & SEO': """
**Week 1-2: Content & Strategy**
- Introduction to content marketing and content types.
- Keyword research and content planning.

**Week 3-4: Writing for the Web**
- Copywriting for blogs, websites, and social media.
- On-page SEO techniques.

**Week 5-6: Content Promotion**
- Off-page SEO and link building.
- Content promotion on social media and email newsletters.

**Week 7-8: Analytics & Monetization**
- Using Google Analytics to track content performance.
- Monetization strategies (e.g., affiliate marketing, ad revenue).
""",
    'Financial Modeling': """
**Week 1-2: Excel Fundamentals**
- Advanced Excel skills for financial analysis.
- Introduction to financial statements (income statement, balance sheet, cash flow).

**Week 3-4: Building a 3-Statement Model**
- Forecasting revenue and expenses.
- Integrating the three financial statements.

**Week 5-6: Valuation & Sensitivity Analysis**
- Building a discounted cash flow (DCF) model.
- Performing sensitivity analysis and scenario planning.

**Week 7-8: Advanced Models & Project**
- Mergers & Acquisitions (M&A) or leveraged buyout (LBO) models.
- Building a comprehensive financial model from scratch.
""",
    'Human Resource Management': """
**Week 1-2: HR Fundamentals**
- The role of HR in an organization.
- Talent acquisition and recruitment.

**Week 3-4: Employee Relations & Development**
- Employee onboarding and training.
- Performance management and feedback.

**Week 5-6: Compensation & Benefits**
- Designing compensation and benefits packages.
- Managing payroll and legal compliance.

**Week 7-8: Strategic HR & Analytics**
- HR's role in organizational strategy.
- Introduction to HR analytics.
""",
    'DevOps Engineering': """
**Week 1-2: DevOps Culture & CI/CD**
- Introduction to DevOps principles.
- Continuous Integration/Continuous Deployment (CI/CD) pipelines.

**Week 3-4: Version Control & Automation**
- Git for version control.
- Automation with tools like Jenkins or GitLab CI.

**Week 5-6: Containerization**
- Introduction to Docker.
- Building, managing, and deploying containers.

**Week 7-8: Orchestration & Monitoring**
- Kubernetes for container orchestration.
- Monitoring and logging best practices.
""",
    'Product Management': """
**Week 1-2: The Product Manager Role**
- Introduction to product management.
- Product life cycle and agile development.

**Week 3-4: User Research & Strategy**
- Conducting user research and competitive analysis.
- Defining product vision and strategy.

**Week 5-6: Execution & Development**
- Writing user stories and managing the product backlog.
- Working with engineering and design teams.

**Week 7-8: Launch & Metrics**
- Go-to-market strategy.
- Defining and tracking key metrics (KPIs).
""",
    'Data Structures & Algorithms': """
**Week 1-2: Fundamental Data Structures**
- Arrays, Linked Lists, Stacks, and Queues.
- Time and space complexity analysis.

**Week 3-4: Advanced Data Structures**
- Trees (Binary Trees, BSTs), Heaps, and Graphs.
- Hash Tables and collision resolution.

**Week 5-6: Core Algorithms**
- Searching and sorting algorithms.
- Recursion and backtracking.

**Week 7-8: Problem Solving & Interviews**
- Dynamic Programming and Greedy Algorithms.
- Preparing for coding interviews.
""",
    'Video Editing & VFX': """
**Week 1-2: The Art of Editing**
- Introduction to video editing software (e.g., Adobe Premiere Pro).
- The fundamentals of sequencing, pacing, and storytelling.

**Week 3-4: Visual and Audio Enhancement**
- Color correction and grading.
- Audio mixing and sound design.

**Week 5-6: Visual Effects (VFX)**
- Introduction to VFX software (e.g., After Effects).
- Chroma keying (green screen) and motion tracking.

**Week 7-8: Final Project & Portfolio**
- Creating a short film or motion graphics project.
- Building a professional reel for your portfolio.
"""
}
# Handler for the /start command and welcome messages
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message and asks how to help."""
    await update.message.reply_text(
        "Hello! I am the Infotech company's course bot. How can I help you today?\n\n"
        "You can ask me about our courses, their fees, mentors, or even a general question like 'what is business analytics?'."
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
        # If no course is found, check if it's a general question for the AI
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
