from flask import Flask, request, jsonify
import subprocess
import tempfile
import os
import threading
import time
import random

app = Flask(__name__)

# Sample tutorials data
TUTORIALS = [
    {
        "id": 1,
        "title": "Python Basics",
        "difficulty": "Beginner",
        "description": "Learn the fundamentals of Python programming language from scratch."
    },
    {
        "id": 2,
        "title": "Data Structures",
        "difficulty": "Intermediate",
        "description": "Master essential data structures and algorithms for efficient programming."
    },
    {
        "id": 3,
        "title": "Web Development",
        "difficulty": "Advanced",
        "description": "Build responsive web applications with modern frameworks and tools."
    }
]

# Sample exercises data
EXERCISES = [
    {
        "id": 1,
        "title": "Array Manipulation Challenge",
        "difficulty": "Intermediate",
        "description": (
            "Write a function called filter_and_sort that takes a list of numbers and returns a new list with the following conditions:\n"
            "- Filter out all numbers that are less than 10\n"
            "- Sort the remaining numbers in descending order\n"
            "- Return the new list\n"
            "Example: Input [5, 15, 3, 22, 9, 14] should return [22, 15, 14]"
        ),
        "starter_code": (
            "def filter_and_sort(numbers):\n"
            "    # Your code here\n"
            "    pass\n"
        ),
        "solution_code": (
            "def filter_and_sort(numbers):\n"
            "    filtered = [n for n in numbers if n >= 10]\n"
            "    return sorted(filtered, reverse=True)\n"
        )
    },
    {
        "id": 2,
        "title": "Sum of Even Numbers",
        "difficulty": "Beginner",
        "description": (
            "Write a function called sum_even that takes a list of integers and returns the sum of all even numbers."
        ),
        "starter_code": (
            "def sum_even(numbers):\n"
            "    # Your code here\n"
            "    pass\n"
        ),
        "solution_code": (
            "def sum_even(numbers):\n"
            "    return sum(n for n in numbers if n % 2 == 0)\n"
        )
    }
]

# Helper function to run code with timeout and capture output/errors
def run_python_code(code, timeout=5):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
        tmp_file.write(code)
        tmp_file_path = tmp_file.name

    def target(result):
        try:
            # Run python code with subprocess, capture stdout and stderr
            proc = subprocess.run(
                ['python3', tmp_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )
            result['stdout'] = proc.stdout
            result['stderr'] = proc.stderr
            result['returncode'] = proc.returncode
        except subprocess.TimeoutExpired:
            result['stdout'] = ''
            result['stderr'] = 'Error: Execution timed out.'
            result['returncode'] = -1

    result = {}
    thread = threading.Thread(target=target, args=(result,))
    thread.start()
    thread.join(timeout + 1)

    # Clean up temp file
    try:
        os.remove(tmp_file_path)
    except Exception:
        pass

    return result

# Basic code analysis using pylint (must be installed in environment)
def analyze_python_code(code):
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp_file:
        tmp_file.write(code)
        tmp_file_path = tmp_file.name

    try:
        # Run pylint with JSON output
        proc = subprocess.run(
            ['pylint', '--disable=all', '--enable=E,W,C,R', '--output-format=json', tmp_file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )
        pylint_output = proc.stdout
        # pylint outputs JSON array of messages
        import json
        messages = json.loads(pylint_output) if pylint_output else []
    except Exception as e:
        messages = [{"type": "error", "message": f"Analysis failed: {str(e)}"}]
    finally:
        try:
            os.remove(tmp_file_path)
        except Exception:
            pass

    # Format messages for frontend
    formatted = []
    for msg in messages:
        formatted.append({
            "type": msg.get("type"),
            "line": msg.get("line"),
            "message": msg.get("message"),
            "symbol": msg.get("symbol")
        })
    return formatted

@app.route('/api/tutorials', methods=['GET'])
def get_tutorials():
    return jsonify({"tutorials": TUTORIALS})

@app.route('/api/exercises', methods=['GET'])
def get_exercises():
    # Optionally support ?id= to get specific exercise
    exercise_id = request.args.get('id', type=int)
    if exercise_id:
        exercise = next((ex for ex in EXERCISES if ex['id'] == exercise_id), None)
        if exercise:
            return jsonify({"exercise": exercise})
        else:
            return jsonify({"error": "Exercise not found"}), 404
    else:
        # Return all exercises
        return jsonify({"exercises": EXERCISES})

@app.route('/api/exercises/random', methods=['GET'])
def get_random_exercise():
    exercise = random.choice(EXERCISES)
    return jsonify({"exercise": exercise})

@app.route('/api/analyze', methods=['POST'])
def analyze_code():
    data = request.get_json()
    code = data.get('code', '')
    if not code:
        return jsonify({"error": "No code provided"}), 400

    # For demo, only analyze Python code
    analysis = analyze_python_code(code)
    return jsonify({"analysis": analysis})

@app.route('/api/run', methods=['POST'])
def run_code():
    data = request.get_json()
    code = data.get('code', '')
    if not code:
        return jsonify({"error": "No code provided"}), 400

    result = run_python_code(code)
    return jsonify({
        "stdout": result.get('stdout', ''),
        "stderr": result.get('stderr', ''),
        "returncode": result.get('returncode', 0)
    })

if __name__ == '__main__':
    # Run Flask app
    app.run(debug=True, port=5000)
