import os
import requests
from flask import Flask, request, jsonify
import re

app = Flask(__name__)

# API setup
API_URL = "https://router.huggingface.co/novita/v3/openai/chat/completions"
HEADERS = {"Authorization": "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"}
# MODEL = "deepseek/deepseek-v3-0324"
# MODEL = "meta-llama/Llama-2-7b-chat-hf"
MODEL = "google/gemma-3-1b-it"

def fetchQuizFromLlama(student_topic):
    print("Fetching quiz from Hugging Face router API")
    payload = {
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Generate a quiz with 3 questions to test students on the provided topic. "
                    f"For each question, generate 4 options where only one of the options is correct. "
                    f"Format your response as follows:\n"
                    f"**QUESTION 1:** You can use any question here and setup a couple of answers\n"
                    f"**OPTION A:** Answer 1\n"
                    f"**OPTION B:** Answer 2\n"
                    f"**OPTION C:** Answer 3\n"
                    f"**ANS:** Answer 2\n\n"
                    f"**QUESTION 2:** 2. True or False?\n"
                    f"**OPTION A:** True\n"
                    f"**OPTION B:** False\n"
                    f"**ANS:** True\n\n"
                    f"**QUESTION 3:** 3. What is the answer to life?\n"
                    f"**OPTION A:** 24\n"
                    f"**OPTION B:** 42\n"
                    f"**OPTION C:** 0\n"
                    f"**ANS:** 42\n\n"
                    f"Ensure text is properly formatted. It needs to start with a question, then the options, and finally the correct answer. "
                    f"Follow this pattern for all questions. "
                    f"Here is the student topic:\n{student_topic}"
                )
            }
        ],
        "model": MODEL,
        "max_tokens": 500,
        "temperature": 0.7,
        "top_p": 0.9
    }

    response = requests.post(API_URL, headers=HEADERS, json=payload)
    if response.status_code == 200:
        result = response.json()["choices"][0]["message"]["content"]
        # print(result)
        return result
    else:
        raise Exception(f"API request failed: {response.status_code} - {response.text}")

def process_quiz(quiz_text):
    questions = []
    # Updated regex to match bolded format with numbered questions
    pattern = re.compile(
        r'\*\*QUESTION \d+:\*\* (.+?)\n'
        r'\*\*OPTION A:\*\* (.+?)\n'
        r'\*\*OPTION B:\*\* (.+?)\n'
        r'\*\*OPTION C:\*\* (.+?)\n'
        r'\*\*OPTION D:\*\* (.+?)\n'
        r'\*\*ANS:\*\* (.+?)(?=\n|$)',
        re.DOTALL
    )
    matches = pattern.findall(quiz_text)

    for match in matches:
        question = match[0].strip()
        options = [match[1].strip(), match[2].strip(), match[3].strip(), match[4].strip()]
        correct_ans = match[5].strip()

        question_data = {
            "question": question,
            "options": options,
            "correct_answer": correct_ans
        }
        questions.append(question_data)

    return questions

@app.route('/getQuiz', methods=['GET'])
def get_quiz():
    print("Request received")
    student_topic = request.args.get('topic')
    if not student_topic:
        return jsonify({'error': 'Missing topic parameter'}), 400
    try:
        quiz = fetchQuizFromLlama(student_topic)
        print(quiz)
        processed_quiz = process_quiz(quiz)
        if not processed_quiz:
            return jsonify({'error': 'Failed to parse quiz data', 'raw_response': quiz}), 500
        return jsonify({'quiz': processed_quiz}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test', methods=['GET'])
def run_test():
    return jsonify({'quiz': "test"}), 200

if __name__ == '__main__':
    port_num = 5000
    print(f"App running on port {port_num}")
    app.run(port=port_num, host="0.0.0.0")
