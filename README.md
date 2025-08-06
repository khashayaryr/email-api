# 🚀 AI-Powered Email Outreach Assistant

An intelligent, Streamlit-based web application designed to streamline and automate professional email outreach. This tool allows users to manage contacts, create email templates, and schedule personalized emails with smart reminders and a background sending process.


## ✨ Features

-   **👤 User Profile Management**: Set up your personal profile, including name, title, and a custom email signature.
-   **👥 Contact Management**: Easily add, view, and delete contact profiles for email recipients.
-   **📝 Dynamic Templates**: Create reusable email templates with placeholders like `{name}`, `{title}`, etc., for personalization.
-   **✉️ Advanced Email Composer**:
    -   Compose emails from scratch or load a template with one click.
    -   Select multiple recipients from your contact list.
    -   Live, side-by-side preview that shows the personalized email for each selected recipient.
    -   Attach multiple files to your emails.
-   **🗓️ Flexible Scheduling**:
    -   Schedule emails to be sent at a specific future date and time.
    -   A "Send Now" option that queues the email for immediate dispatch.
-   **⏰ Smart Reminders**:
    -   Set follow-up reminders directly when composing or scheduling an email.
    -   View and manage all upcoming reminders in a dedicated, chronologically sorted list.
-   **⚙️ Asynchronous Sending**: Emails are handled by a separate background worker process, ensuring the user interface remains fast and responsive.


## 🛠️ Tech Stack

-   **Framework**: Streamlit
-   **Database**: TinyDB (a lightweight, document-based database)
-   **Email Sending**: Yagmail
-   **Logging**: Loguru


## ⚙️ Setup and Installation

Follow these steps to get the project running on your local machine. It is recommended to create a virtual environment for this project.

### 1. Clone the Repository
```bash
git clone https://github.com/khashayaryr/email-api.git
```

### 2. Navigate to the project root:
```bash
cd email-api
```

### 3. Install Dependencies
All required packages are listed in `requirements.txt`.
```bash
pip install -r requirements.txt
```

### 4. Create the Environment File
Create a file named `.env` in the root directory of the project.

### 5. Configure Email Credentials
Open the `.env` file and add your Gmail address and an **App Password**.

```ini
EMAIL_SENDER=your-email@gmail.com
EMAIL_PASS=your-16-character-app-password
```

> ### ❗️ **How to Get a Google App Password**
> You **cannot** use your regular Google account password. You must generate a special "App Password" for this application to access your Gmail account securely.
>
> 1.  **Enable 2-Step Verification**: An App Password can only be created if 2-Step Verification is active on your Google Account. If it's not, enable it first.
> 2.  Go to your Google Account settings: [myaccount.google.com](https://myaccount.google.com/).
> 3.  In the search bar at the top, type **"App Passwords"** and select the corresponding result, or visit [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
> 4.  Give it a name (e.g., "Streamlit Email App") and click **"Create"**.
> 5.  Google will provide a **16-character password**. Copy this password and paste it into your `.env` file as the value for `EMAIL_PASS`.


## ▶️ Running the Application

This project uses a wrapper script to run both the Streamlit UI and the background sending worker simultaneously from a single terminal.

Simply run the following command from the project's root directory:
```bash
python run_app.py
```
This will:
1.  Start the Streamlit web server (usually at `http://localhost:8501`).
2.  Start the `send_worker.py` script in the background to process the email queue.

Your browser should open with the application running. To stop both processes, press `Ctrl` + `C` in the terminal.


## 📂 Project Structure

```
email-assistance/
├── .env                  # For storing secret credentials
├── .gitignore            # Specifies intentionally untracked files to ignore
├── requirements.txt      # Project dependencies
├── LICENSE               # Project license file
├── README.md             # This file
├── run_app.py            # A wrapper script to run the entire application
└── src/
    ├── pages/            # Contains all Streamlit pages for the multipage app
    │   ├── 1_👥_Profiles.py
    │   ├── 2_📝_Templates.py
    │   ├── 3_✉️_Compose_&_Send.py
    │   ├── 4_🗓️_Schedule.py
    │   ├── 5_⏰_Reminders.py
    │   ├── 6_🤖_Chat_with_Emails.py
    │   └── 7_👤_My_Profile.py
    ├── utils/
    │   ├── db.py         # The TinyDB database handler class
    │   └── helpers.py    # The email sending function using yagmail
    ├── Home.py           # The main entrypoint/dashboard of the Streamlit app
    └── send_worker.py    # The background worker for sending scheduled emails
```


## Future Work

-   Implement the **Dashboard** on the Home page with real statistics.
-   Build out the **Chat with Emails (RAG)** page for conversational search.
-   Add more advanced, condition-based reminders.


## 📄 License

This project is licensed under the MIT License. See the [LICENSE](https://github.com/khashayaryr/email-api/blob/main/LICENSE) file for details.