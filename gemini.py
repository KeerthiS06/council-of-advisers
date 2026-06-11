from google import genai
from google.genai import types
from code import run_pipeline

DEFAULT_GEMINI_API_KEY = 'AQ.Ab8RN6KSD06Tsd7ox3EXSlREyEb4GFwhZ7gulVpoBsL50dBjwg'


def ask_gemini(file_path: str, user_question: str, api_key: str = DEFAULT_GEMINI_API_KEY) -> str:
    """
    Upload a transcript file to Gemini and ask a question about it.

    Args:
        file_path:     Path to the local transcript text file.
        user_question: The question to ask Gemini about the transcript.
        api_key:       Gemini API key.

    Returns:
        Gemini's response as a string, or an error message.
    """
    client = genai.Client(api_key=api_key)

    uploaded_file = client.files.upload(
        file=file_path,
        config=types.UploadFileConfig(mime_type="text/plain")
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[user_question, uploaded_file]
        )
        return response.text
    finally:
        # Always clean up the uploaded file from Google's servers
        client.files.delete(name=uploaded_file.name)


def main():
    file_path = run_pipeline()
    user_question = 'What is my name?'

    try:
        print(f"📤 Uploading {file_path} to Gemini API...")
        answer = ask_gemini(file_path, user_question)
        print("\n✨ Gemini's Response:")
        print(answer)
    except FileNotFoundError:
        print(f"❌ Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")


if __name__ == "__main__":
    main()
