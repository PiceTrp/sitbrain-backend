import gradio as gr
import requests

# * api endpoint configuration
API_BASE_URL = "http://localhost:8080"
CHAT_ENDPOINT = f"{API_BASE_URL}/api/v1/chat"


def chat_with_api(question):
    """
    * send question to chat api and return response
    """
    try:
        # * prepare request payload
        payload = {"question": question}

        # * send post request to chat endpoint
        response = requests.post(
            CHAT_ENDPOINT, json=payload, headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "No answer received")
            sources = None
            processing_time = data.get("processing_time", 0)

            # * format response with sources and timing
            result = f"{answer}\n\n"
            if sources:
                result += f"**Sources:** {', '.join(sources)}\n"
            result += f"**Processing time:** {processing_time:.2f}s"

            return result
        else:
            return f"Error: {response.status_code} - {response.text}"

    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to API. Make sure the server is running on http://localhost:8080"
    except Exception as e:
        return f"Error: {str(e)}"


# * create gradio interface
with gr.Blocks(title="RAG Chat Interface") as app:
    gr.Markdown("# 🤖 RAG Chat Interface")
    gr.Markdown("Ask questions and get answers from your document knowledge base")

    with gr.Row():
        with gr.Column():
            question_input = gr.Textbox(
                label="Your Question",
                placeholder="Enter your question here...",
                lines=3,
            )
            submit_btn = gr.Button("Ask Question", variant="primary")

        with gr.Column():
            answer_output = gr.Textbox(label="Answer", lines=10, max_lines=20)

    # * examples for quick testing
    gr.Examples(
        examples=[
            ["What is the main topic of the documents?"],
            ["Can you summarize the key findings?"],
            ["What are the recommendations mentioned?"],
        ],
        inputs=[question_input],
    )

    # * connect button to function
    submit_btn.click(fn=chat_with_api, inputs=[question_input], outputs=[answer_output])

    # * also allow enter key to submit
    question_input.submit(
        fn=chat_with_api, inputs=[question_input], outputs=[answer_output]
    )

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860, share=False)
