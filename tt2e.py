try:
    import pyttsx3
except ImportError:
    print("pyttsx3 is not installed. Please install it with 'pip install pyttsx3'.")
    raise

engine = pyttsx3.init()
voices = engine.getProperty("voices") or []

for index, voice in enumerate(voices):
    print(f"ID de voz [{index}]: {voice.name}")
    print(f"  -> {voice.id}\n")



# 1. Configurar la voz (reemplaza '0' por el ID de tu voz masculina más grave)
engine.setProperty('voice', voices[0].id)

# 2. Bajar el ritmo de habla para simular la cadencia de JARVIS
rate = engine.getProperty('rate')
engine.setProperty('rate', rate - 30)  # Generalmente un valor entre 150-175

# 3. Hacer hablar al asistente
engine.say("System ready. How may I assist you today, sir?")
engine.runAndWait()

