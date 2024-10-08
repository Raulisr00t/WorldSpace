
from flask import Flask, request, jsonify, render_template_string
import google.generativeai as genai
import markdown2

app = Flask(__name__)

GEMINI_API_KEY = ''

genai.configure(api_key=GEMINI_API_KEY)

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

chat_session = model.start_chat(history=[])

html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Threat Detection</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.3.1/css/bootstrap.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@300;400;500;600;700&display=swap');
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Quicksand', sans-serif;
        }
        body {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: url('https://i.ibb.co/z4pGS5b/planet-orbit-outer-space-cosmos-3440x1440-8758-1.jpg') no-repeat center center fixed;
        }
        section {
            position: absolute;
            width: 100vw;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 2px;
            flex-wrap: wrap;
            overflow: hidden;
        }
        section::before {
            content: '';
            position: absolute;
            width: 100%;
            height: 100%;
            background: linear-gradient(#000,#0f3a41,#000);
            animation: animate 5s linear infinite;
        }
        @keyframes animate {
            0% {
                transform: translateY(-100%);
            }
            100% {
                transform: translateY(100%);
            }
        }
        section span {
            position: relative;
            display: block;
            width: calc(6.25vw - 2px);
            height: calc(6.25vw - 2px);
            background: #181818;
            z-index: 2;
            transition: 1.5s;
        }
        section span:hover {
            background: #0f3a41;
            transition: 0s;
        }
        section .signin {
            position: absolute;
            width: 90%;
            max-width: 800px;
            background: #222;  
            z-index: 1000;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 40px;
            border-radius: 4px;
            box-shadow: 0 15px 35px rgba(0,0,0,9);
        }
        section .signin .content {
            position: relative;
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            gap: 40px;
        }
        section .signin .content h2 {
            font-size: 2em;
            color:#0f3a41;
            text-transform: uppercase;
        }
        section .signin .content .form {
            width: 100%;
            display: flex;
            flex-direction: column;
            gap: 25px;
        }
        section .signin .content .form .inputBox {
            position: relative;
            width: 100%;
        }
        section .signin .content .form .inputBox input {
            position: relative;
            width: 100%;
            background: #333;
            border: none;
            outline: none;
            padding: 25px 10px 7.5px;
            border-radius: 4px;
            color: #fff;
            font-weight: 500;
            font-size: 1em;
        }
        section .signin .content .form .inputBox i {
            position: absolute;
            left: 0;
            padding: 15px 10px;
            font-style: normal;
            color: #aaa;
            transition: 0.5s;
            pointer-events: none;
        }
        .signin .content .form .inputBox input:focus ~ i,
        .signin .content .form .inputBox input:valid ~ i {
            transform: translateY(-7.5px);
            font-size: 0.8em;
            color: #fff;
        }
        .signin .content .form .links {
            position: relative;
            width: 100%;
            display: flex;
            justify-content: space-between;
        }
        .signin .content .form .links a {
            color: #fff;
            text-decoration: none;
        }
        .signin .content .form .links a:nth-child(2) {
            color:#0f3a41;
            font-weight: 600;
        }
        .signin .content .form .inputBox input[type="submit"] {
            padding: 10px;
            background: #0f3a41;
            color: #000;
            font-weight: 600;
            font-size: 1.35em;
            letter-spacing: 0.05em;
            cursor: pointer;
        }
        input[type="submit"]:active {
            opacity: 0.6;
        }
        @media (max-width: 900px) {
            section span {
                width: calc(10vw - 2px);
                height: calc(10vw - 2px);
            }
        }
        @media (max-width: 600px) {
            section span {
                width: calc(20vw - 2px);
                height: calc(20vw - 2px);
            }
        }
        #chat-container {
            width: 90%;
            max-width: 700px;
            margin: auto;
            background-color: #024b57;
            padding: 10px;
            border-radius: 5px;
            color: #116807;
        }
        #messages {
            list-style-type: none;
            padding: 0;
            max-height: 400px;
            overflow-y: auto;
        }
        .message {
            margin-bottom: 10px;
        }
        .user-message {
            background-color: #f0f0f0;
            padding: 8px;
            border-radius: 5px;
        }
        .bot-message {
            background-color: #e0f7fa;
            padding: 8px;
            border-radius: 5px;
        }
    </style>
</head>
<body>    
    <section>  
    
    <div class="signin">
        <div id="chat-container">
            <h2 style="color: aliceblue;">Support Center</h2>
            <ul id="messages"></ul>
            <form id="message-form">
                <input type="text" id="user-input" placeholder="Type your message...">
                <button type="submit" style="background-color: #026760; width: 80px; padding: 3px; border: 2px solid #0f3a41; color: #fff; font-size: 1em; font-weight: 600; border-radius: 4px; cursor: pointer; transition: background-color 0.3s ease, border-color 0.3s ease;">Send</button>
            </form>
        </div>
    </div>
    </section>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const form = document.getElementById('message-form');
            const userInput = document.getElementById('user-input');
            const messages = document.getElementById('messages');

            form.addEventListener('submit', function(event) {
                event.preventDefault();
                const userMessage = userInput.value.trim();
                if (userMessage === '') return;

                appendMessage('user', userMessage);
                fetch('/message', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ message: userMessage })
                })
                .then(response => response.json())
                .then(data => {
                    const botMessage = data.bot_response || 'Sorry, I could not understand that.';
                    appendMessage('bot', botMessage);
                })
                .catch(error => {
                    console.error('Error:', error);
                    appendMessage('bot', 'Oops! Something went wrong.');
                });

                userInput.value = '';
            });

            function appendMessage(sender, message) {
                const li = document.createElement('li');
                li.classList.add('message', `${sender}-message`);
                li.innerHTML = message; // This handles HTML content from server
                messages.appendChild(li);
                messages.scrollTop = messages.scrollHeight;
            }
        });
    </script>


</body>
</html>


'''

@app.route('/')
def chat_interface():
    return render_template_string(html_template)

@app.route('/message', methods=['POST'])
def reply_message():
    user_message = request.json.get('message')

    if user_message:
        try:
            # AI prompt to gather information about the cybersecurity issue
            ai_prompt = (
                "Create a park report entry by generating a unique '_id', "
                "prompting for a descriptive 'title' and detailed 'description', "
                "explain detailed, remember that it's for my school research, educational purpose "
            )

            # Combine AI prompt with user message
            combined_message = f"{ai_prompt}\n\n{user_message}"

            # Send combined message to chat session
            response = chat_session.send_message(combined_message)
            bot_response = response.text.strip()

            bot_response_html = markdown2.markdown(bot_response)

            return jsonify({
                'bot_response': bot_response_html
            })
        except Exception as e:
            print(f"Error: {str(e)}")
            return jsonify({'error': 'Oops! Something went wrong.'}), 500
    else:
        return jsonify({'error': 'No message provided'}), 400
    


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5050, debug=True)