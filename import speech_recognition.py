import speech_recognition as sr
import time

class SpeechGame:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        # You might want to adjust ambient noise calibration here or elsewhere
        # with self.microphone as source:
        #     self.recognizer.adjust_for_ambient_noise(source)

    def listen_continuously(self):
        print("Calibrating microphone for ambient noise...")
        # Calibrate once when starting continuous listening
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            print("Microphone calibrated. Listening for speech...")

            while True: # Loop indefinitely to listen
                try:
                    # Attempt to listen
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                    text = self.recognizer.recognize_google(audio)
                    print(f"You said: {text}")

                except sr.WaitTimeoutError:
                    # This is normal if no speech is detected within the timeout
                    print("No speech detected.")
                    continue # Continue listening

                except sr.UnknownValueError:
                    print("Google Speech Recognition could not understand audio")
                except sr.RequestError as e:
                    print(f"Could not request results from Google Speech Recognition service; {e}")
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")
                    # If the stream stops, you might want to break or try to reinitialize
                    break # Break out of the loop on critical error like stream stop

# --- Outside the class, how you might run it ---
if __name__ == "__main__":
    game = SpeechGame()
    try:
        game.listen_continuously()
    except KeyboardInterrupt:
        print("Listening stopped by user.")
    except Exception as e:
        print(f"Program terminated due to: {e}")