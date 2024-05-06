import os
import subprocess
from flask import Flask, request, render_template, Response

app = Flask(__name__)

def run_command(command):
    """Run a shell command and stream the output."""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    # Stream both stdout and stderr
    for line in iter(process.stdout.readline, ''):
        yield line
    process.stdout.close()
    return_code = process.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, command)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        output_filename = request.form['output_filename']

        # Create a folder named "saved_cards" if it doesn't exist
        folder_name = "saved_cards"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)

        # Execute command to save dumps in the "saved_cards" folder with specified filename
        command_user_specified = f"mfoc -O {folder_name}/{output_filename}.dmp"
        process_user_specified = subprocess.Popen(command_user_specified, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        # Execute command to save dumps in saved_cards.dmp
        command_saved_cards = f"mfoc -O {folder_name}/saved_cards.dmp"
        process_saved_cards = subprocess.Popen(command_saved_cards, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        # Wait for both processes to complete
        output_user_specified, _ = process_user_specified.communicate()
        output_saved_cards, _ = process_saved_cards.communicate()

        # Concatenate outputs
        combined_output = output_user_specified + "\n" + output_saved_cards
        return Response(combined_output, status=200, mimetype='text/plain')

    return render_template('index.html')

def generate_output(process):
    for line in iter(process.stdout.readline, ''):
        yield line
    process.stdout.close()
    return_code = process.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, "")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
