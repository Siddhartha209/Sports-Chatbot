# Sports Hub Chatbot

A modern web application for sports fans, featuring a chatbot, user authentication, and theme switching. Made using React, Python, JavaScript, CSS and MongoDB

---

## Features

- **Chatbot**: Ask sports-related questions and get instant answers.
- **User Authentication**: Secure signup and login with email and password.
- **Web Scraping Tool**: Scrapes player statistics off websites.
- **Dark/Light Mode**: Toggle between dark and light themes for all forms and UI elements.

---

## Tech Stack

- **Frontend**: React (functional components, hooks)
- **Styling**: CSS with CSS variables for theme support
- **Backend**: Python for NLP and processing
- **Version Control**: Git & GitHub

---

## Project Structure

```
chatbot-sports/
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   └── Home/
│   │   │       ├── Home.js
│   │   │       └── Home.css
│   │   └── theme.css
│   ├── public/
│   │   └── img/
│   │       └── web_logo.png
│   └── package.json
│
├── backend/
│   └── pl_player_stats.py
    └── player_stats.json.py
│
├── .gitignore
└── README.md
```

---

## How to Run

1. **Install dependencies**
   ```sh
   cd frontend
   npm install
   ```

2. **Start the development server**
   ```sh
   npm start
   ```

3. **Open in browser**
   Visit [http://localhost:3000](http://localhost:3000)

---

## Usage Examples

- **Sign up** with your email and password (optional)
- **Log in** to access the chatbot.
- **Ask questions** like:
  - "How many goals has Mohamed Salah scored?"
  - "Who has made the most fouls?"
  - "Show full stats of Florian Wirtz"
- **Switch themes** using the toggle button in the bottom-left corner.

---
## Python Version
3.12
