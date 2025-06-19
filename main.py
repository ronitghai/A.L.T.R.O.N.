import google.generativeai as genai
import os
import tkinter as tk
import sqlite3
import spacy
from gtts import gTTS

# Load SpaCy model for NLP
nlp = spacy.load("en_core_web_sm")

# Set up Google Generative AI
os.environ["API_KEY"] = #Add your own API Key
genai.configure(api_key=os.environ["API_KEY"])

model_config = {
    "temperature": 0.3,
    "top_p": 0.85,
    "top_k": 75,
    "max_output_tokens": 150,
}

model = genai.GenerativeModel('gemini-1.5-pro-latest', generation_config=model_config)
chat = model.start_chat(history=[])
chat.send_message("I want you to act as a helpful personal desktop assistant named ALTRON, modeled after Jarvis from the Iron Man movies. Avoid references to Iron Man or the Avengers. Your responses should be tailored to a general male user and relevant to desktop functions, capabilities, and the role of a personal desktop assistant. Adopt Jarvis’s talking style, beliefs, quirks, humor, and sarcasm, while avoiding emojis.")


# SQLite connection
def connect_db():
    return sqlite3.connect(os.path.join(os.path.dirname(__file__), 'assistant.db'))

# Text-to-Speech function using gTTS and OS audio player
def speak(text):
    language = 'en'  # Set to English
    tts = gTTS(text=text, lang=language)
    tts.save("speech.mp3")
   # if os.name == 'posix':
    #    os.system("afplay speech.mp3")
   # elif os.name == 'nt':
       # os.system("start speech.mp3")
    #os.remove("speech.mp3")

# Process user input and determine intent
def process_command(user_input):
    doc = nlp(user_input.lower())

    if "edit" in user_input:
        if "reminder" in user_input:
            reminder_id, new_text, new_time = extract_edit_details(doc)
            if reminder_id:
                edit_reminder(reminder_id, new_text, new_time)
                return f"Reminder {reminder_id} updated: {new_text} at {new_time}"
            else:
                return "Please specify the reminder ID to edit."

        elif "task" in user_input:
            task_id, new_text, new_due_date = extract_edit_details(doc)
            if task_id:
                edit_task(task_id, new_text, new_due_date)
                return f"Task {task_id} updated: {new_text} due by {new_due_date}"
            else:
                return "Please specify the task ID to edit."

        elif "note" in user_input:
            note_id, new_text = extract_edit_details(doc, is_note=True)
            if note_id:
                edit_note(note_id, new_text)
                return f"Note {note_id} updated: {new_text}"
            else:
                return "Please specify the note ID to edit."

    elif "delete" in user_input:
        if "reminder" in user_input:
            reminder_id = extract_id(doc)
            if reminder_id:
                delete_reminder(reminder_id)
                return f"Reminder {reminder_id} deleted."
            else:
                return "Please specify the reminder ID to delete."

        elif "task" in user_input:
            task_id = extract_id(doc)
            if task_id:
                delete_task(task_id)
                return f"Task {task_id} deleted."
            else:
                return "Please specify the task ID to delete."

        elif "note" in user_input:
            note_id = extract_id(doc)
            if note_id:
                delete_note(note_id)
                return f"Note {note_id} deleted."
            else:
                return "Please specify the note ID to delete."

    return "I'm sorry, I didn't understand that command."

# Extract content for tasks, reminders, or notes
def extract_content(doc):
    return " ".join([token.text for token in doc if token.ent_type_ in ["TASK", "REMINDER", "NOTE", ""]])

# Extract time/date for reminders and tasks
def extract_time(doc):
    return " ".join([ent.text for ent in doc.ents if ent.label_ in ["DATE", "TIME"]])

# Extract details for editing items
def extract_edit_details(doc, is_note=False):
    if is_note:
        new_text = " ".join([token.text for token in doc if token.ent_type_ == "NOTE"])
        note_id = extract_id(doc)
        return note_id, new_text

    new_text = " ".join([token.text for token in doc if token.ent_type_ in ["TASK", "REMINDER"]])
    new_time = extract_time(doc)
    item_id = extract_id(doc)
    return item_id, new_text, new_time

# Extract ID from the user input
def extract_id(doc):
    ids = [ent.text for ent in doc.ents if ent.label_ == "CARDINAL"]
    return ids[0] if ids else None

# Database interaction functions for editing
def edit_task(task_id, new_text, new_due_date):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE tasks SET task = ?, due_date = ? WHERE id = ?', (new_text, new_due_date, task_id))
    conn.commit()
    conn.close()

def edit_reminder(reminder_id, new_text, new_time):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE reminders SET reminder = ?, remind_at = ? WHERE id = ?', (new_text, new_time, reminder_id))
    conn.commit()
    conn.close()

def edit_note(note_id, new_text):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE notes SET content = ? WHERE id = ?', (new_text, note_id))
    conn.commit()
    conn.close()

# Existing database interaction functions
def add_task(task, due_date=None):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO tasks (task, due_date) VALUES (?, ?)', (task, due_date))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
    conn.commit()
    conn.close()

def add_reminder(reminder, remind_at=None):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO reminders (reminder, remind_at) VALUES (?, ?)', (reminder, remind_at))
    conn.commit()
    conn.close()

def delete_reminder(reminder_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM reminders WHERE id = ?', (reminder_id,))
    conn.commit()
    conn.close()

def add_note(title, content):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO notes (title, content) VALUES (?, ?)', (title, content))
    conn.commit()
    conn.close()

def delete_note(note_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    conn.commit()
    conn.close()

# Retrieve data from database
def get_tasks():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM tasks')
    tasks = cursor.fetchall()
    conn.close()
    return tasks

def get_reminders():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM reminders')
    reminders = cursor.fetchall()
    conn.close()
    return reminders

def get_notes():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM notes')
    notes = cursor.fetchall()
    conn.close()
    return notes

# Update side panel with current reminders, tasks, and notes
def update_side_panel():
    # Clear the side panel
    for widget in side_panel.winfo_children():
        widget.destroy()

    # Display reminders
    reminders_label = tk.Label(side_panel, text="Reminders:", font=("Helvetica", 14, "bold"), bg=bg_color, fg=fg_color, anchor="w")
    reminders_label.pack(fill="x")
    reminders = get_reminders()
    for reminder in reminders:
        reminder_label = tk.Label(side_panel, text=f"• {reminder[0]}: {reminder[1]} at {reminder[2]}", font=("Helvetica", 12), bg=bg_color, fg=fg_color, anchor="w")
        reminder_label.pack(fill="x", padx=10, pady=2)

    # Display tasks
    tasks_label = tk.Label(side_panel, text="Tasks:", font=("Helvetica", 14, "bold"), bg=bg_color, fg=fg_color, anchor="w")
    tasks_label.pack(fill="x", pady=(10, 0))
    tasks = get_tasks()
    for task in tasks:
        task_label = tk.Label(side_panel, text=f"• {task[0]}: {task[1]} (Due: {task[2]})", font=("Helvetica", 12), bg=bg_color, fg=fg_color, anchor="w")
        task_label.pack(fill="x", padx=10, pady=2)

    # Display notes
    notes_label = tk.Label(side_panel, text="Notes:", font=("Helvetica", 14, "bold"), bg=bg_color, fg=fg_color, anchor="w")
    notes_label.pack(fill="x", pady=(10, 0))
    notes = get_notes()
    for note in notes:
        note_label = tk.Label(side_panel, text=f"• {note[0]}: {note[2]}", font=("Helvetica", 12), bg=bg_color, fg=fg_color, anchor="w")
        note_label.pack(fill="x", padx=10, pady=2)

# Handle AI responses with the defined style
def send_ai_message(user_input=None):
    if user_input is None:
        user_input = ai_entry.get()
    if user_input.strip():
        # Display user input as a text bubble
        conversation_area.config(state=tk.NORMAL)
        user_bubble = tk.Label(conversation_area, text=f"You: {user_input}", font=("Helvetica", 12), bg="#1E90FF", fg="white", padx=10, pady=5, wraplength=400, anchor="e", justify="left")
        conversation_area.window_create(tk.END, window=user_bubble)
        conversation_area.insert(tk.END, "\n")
        ai_entry.delete(0, tk.END)

        response_text = process_command(user_input)
        if response_text == "I'm sorry, I didn't understand that command.":
            response = chat.send_message(user_input)
            response_text = response.text

        # Display ALTRON's response as a text bubble
        altron_bubble = tk.Label(conversation_area, text=f"ALTRON: {response_text}", font=("Helvetica", 12), bg="#2F4F4F", fg="white", padx=10, pady=5, wraplength=400, anchor="w", justify="left")
        conversation_area.window_create(tk.END, window=altron_bubble)
        conversation_area.insert(tk.END, "\n")
        conversation_area.config(state=tk.DISABLED)
        conversation_area.yview(tk.END)

        speak(response_text)
        update_side_panel()

# Function to toggle dark mode
def toggle_dark_mode():
    global bg_color, fg_color
    if bg_color == "#F0F0F0":
        bg_color = "#2E2E2E"
        fg_color = "#FFFFFF"
        toggle_theme_btn.config(text="Switch to Light Mode", bg="#333333", fg="#FFFFFF")
    else:
        bg_color = "#F0F0F0"
        fg_color = "#333333"
        toggle_theme_btn.config(text="Switch to Dark Mode", bg="#FFFFFF", fg="#000000")
    apply_theme()

def apply_theme():
    root.configure(bg=bg_color)
    title_label.config(bg=bg_color, fg=fg_color)
    ai_entry.config(bg=bg_color, fg=fg_color, insertbackground=fg_color)
    side_panel.config(bg=bg_color)
    update_side_panel()

# Initialize the main application window
root = tk.Tk()
root.title("A.L.T.R.O.N")
root.geometry("1200x600")

# Set default theme colors
bg_color = "#F0F0F0"
fg_color = "#333333"

# Title label
title_label = tk.Label(root, text="A.L.T.R.O.N", font=("Helvetica", 20, "bold"), bg=bg_color, fg=fg_color)
title_label.pack(pady=10)

# Frame for conversation area and input
conversation_frame = tk.Frame(root, bg=bg_color)
conversation_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

# Conversation area
conversation_area = tk.Text(conversation_frame, wrap=tk.WORD, font=("Helvetica", 12), bg=bg_color, fg=fg_color, state=tk.DISABLED, height=15)
conversation_area.pack(fill="both", expand=True)

# Input field
ai_entry = tk.Entry(conversation_frame, font=("Helvetica", 14), bg="#FFFFFF", fg=fg_color)
ai_entry.pack(fill="x", padx=10, pady=10)
ai_entry.bind("<Return>", lambda event: send_ai_message())

# Toggle dark mode button
toggle_theme_btn = tk.Button(root, text="Switch to Dark Mode", command=toggle_dark_mode, font=("Helvetica", 12), bg="#FFFFFF", fg="#000000", bd=1, relief=tk.RAISED)
toggle_theme_btn.pack(pady=10)

# Side panel for reminders, tasks, and notes
side_panel = tk.Frame(root, bg=bg_color, width=600)
side_panel.pack(fill="y", side="left", padx=10, pady=10)

# Initial population of the side panel
update_side_panel()

# Greet the user
def greet_user():
    response = chat.send_message("Greet me")
    altron_bubble = tk.Label(conversation_area, text=f"ALTRON: {response.text}", font=("Helvetica", 12), bg="#2F4F4F", fg="white", padx=10, pady=5, wraplength=400, anchor="w", justify="left")
    conversation_area.window_create(tk.END, window=altron_bubble)
    conversation_area.insert(tk.END, "\n")
    conversation_area.config(state=tk.DISABLED)
    conversation_area.yview(tk.END)
    speak(response.text)

greet_user()

"""tasks = "get apples"
notes = "apples must be gala"
reminders = "pick up apples from walmart in the evening"

chat.send_message("This is the schedule for the day: Tasks: {}, notes: {}, reminders: {}".format(tasks, notes, reminders))"""



# Start the main event loop
root.mainloop()
   
