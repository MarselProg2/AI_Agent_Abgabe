from google.adk.apps import App
import inspect

with open("inspect_output.txt", "w") as f:
    f.write("--- App Fields ---\n")
    try:
        fields = list(App.model_fields.keys())
        f.write(str(fields) + "\n")
    except Exception as e:
        f.write(f"Error getting fields: {e}\n")

    f.write("\n--- App Signature ---\n")
    try:
        sig = inspect.signature(App.__init__)
        f.write(str(sig) + "\n")
    except Exception as e:
        f.write(f"Error getting signature: {e}\n")
