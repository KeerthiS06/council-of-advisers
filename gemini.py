from google import genai
from code import run_pipeline

DEFAULT_GEMINI_API_KEY = ""  # Set via Streamlit Secrets (GEMINI_API_KEY) or the sidebar

# Max characters to send (~750k tokens at ~4 chars/token, well within the 1M token limit)
MAX_CONTENT_CHARS = 3_000_000


def ask_gemini(file_path: str, user_question: str, api_key: str = DEFAULT_GEMINI_API_KEY) -> str:
    """
    Read a transcript file and ask Gemini a question about it.
    Content is passed directly in the prompt to avoid Files API authentication
    issues (ACCESS_TOKEN_TYPE_UNSUPPORTED) in Streamlit Cloud deployments.

    Args:
        file_path:     Path to the local transcript text file.
        user_question: The question to ask Gemini about the transcript.
        api_key:       Gemini API key.

    Returns:
        Gemini's response as a string, or an error message.
    """
    if not api_key:
        raise ValueError("Gemini API key is required.")

    client = genai.Client(api_key=api_key)

    with open(file_path, "r", encoding="utf-8") as f:
        file_content = f.read()

    # Truncate if extremely large to stay within token limits
    if len(file_content) > MAX_CONTENT_CHARS:
        file_content = file_content[:MAX_CONTENT_CHARS] + "\n\n[Content truncated due to size]"

    prompt = f"Here is the transcript content:\n\n{file_content}\n\n---\n\nQuestion: {user_question}"

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=[prompt]
    )
    return response.text


def main():
    file_path = run_pipeline()
    user_question = 'What is my name?'

    try:
        print(f"📄 Reading {file_path} for Gemini API...")
        answer = ask_gemini(file_path, user_question)
        print("\n✨ Gemini's Response:")
        print(answer)
    except FileNotFoundError:
        print(f"❌ Error: The file '{file_path}' was not found.")
    except Exception as e:
        print(f"❌ An error occurred: {e}")


if __name__ == "__main__":
    main()