from flask import Flask, jsonify
from threading import Thread
from sahara import listen, speak, check_medication_reminders  # Import functions

app = Flask(__name__)

@app.route("/set-voice-reminder", methods=["POST"])
def set_voice_reminder():
    def voice_thread():
        speak("What medicine would you like to set a reminder for and at what time?")
        command = listen()
        if not command:
            speak("I didn't catch that. Please try again.")
            return
        response = check_medication_reminders(command)
        speak(response)

    Thread(target=voice_thread).start()
    return jsonify({"status": "Listening for reminder..."})

if __name__ == "__main__":
    app.run(debug=True, port=5001)