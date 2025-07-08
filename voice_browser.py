import speech_recognition as sr
import webbrowser
import time

class VoiceBrowserController:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        print("Initializing voice controller...")
        # Calibrate for ambient noise once at the start
        with self.microphone as source:
            print("Calibrating microphone for ambient noise... Please be silent.")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Calibration complete. Ready for commands!")

    def listen_for_command(self):
        """
        Listens for a voice command, converts it to text, and returns the text.
        Handles various speech recognition errors.
        """
        with self.microphone as source:
            print("Say a command (e.g., 'open Google', 'open YouTube'):")
            try:
                # Listen for audio with a timeout and phrase time limit
                audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=5)
                print("Recognizing speech...")
                # Use Google Web Speech API to recognize the audio
                text = self.recognizer.recognize_google(audio)
                print(f"You said: '{text}'")
                return text.lower() # Return lowercased text for easier comparison

            except sr.WaitTimeoutError:
                print("No speech detected. Try again.")
                return None
            except sr.UnknownValueError:
                print("Google Speech Recognition could not understand audio. Please speak more clearly.")
                return None
            except sr.RequestError as e:
                print(f"Could not request results from Google Speech Recognition service; {e}. Check your internet connection.")
                return None
            except Exception as e:
                print(f"An unexpected error occurred: {e}")
                return None

    def execute_command(self, command_text):
        """
        Executes actions based on the recognized command text.
        """
        if command_text is None:
            return

        if "open google" in command_text:
            print("Opening Google...")
            webbrowser.open("https://www.google.com")
        elif "open youtube" in command_text:
            print("Opening YouTube...")
            webbrowser.open("https://www.youtube.com")
        elif "open wikipedia" in command_text:
            print("Opening Wikipedia...")
            webbrowser.open("https://www.wikipedia.org")
        elif "open website" in command_text:
            # You can make this more advanced by asking for the URL
            print("Please specify a website, e.g., 'open website example.com'")
        elif "exit" in command_text or "quit" in command_text:
            print("Exiting voice browser controller. Goodbye!")
            return "exit"
        else:
            print("Command not recognized. Please try a different command.")
            # You can optionally "reply" with the text if it wasn't understood clearly
            # or suggest valid commands.

    def run(self):
        """
        Main loop to continuously listen and execute commands.
        """
        while True:
            command = self.listen_for_command()
            if command == "exit":
                break
            elif command: # Only try to execute if a command was actually recognized
                self.execute_command(command)
            time.sleep(1) # Small delay to prevent too rapid listening

if __name__ == "__main__":
    controller = VoiceBrowserController()
    controller.run()