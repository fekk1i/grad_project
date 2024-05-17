document.addEventListener('DOMContentLoaded', function() {
    fetchDmpFiles(); // Fetch list of .dmp files when the document is ready
    updateStatus('Ready...'); // Set the initial status to "Ready..."
});

function appendToConsole(text) {
    const outputElement = document.getElementById('console');
    outputElement.textContent += text; // Append new text
    outputElement.scrollTop = outputElement.scrollHeight; // Scroll to the bottom
}

function runMFoc() {
    const outputFilename = document.getElementById('outputFilename').value;
    const outputElement = document.getElementById('console');
    outputElement.textContent = 'Starting MFOC...\n'; // Initial message for starting MFOC
    updateStatus('Running MFOC...'); // Update the status to "Running MFOC..."

    const eventSource = new EventSource(`/run-mfoc?output_filename=${encodeURIComponent(outputFilename)}`);
    eventSource.onmessage = function(event) {
        appendToConsole(event.data); // Append each new piece of data to the console
        if (event.data.includes("Command executed successfully.")) {
            updateStatus('MFOC Completed Successfully');
            eventSource.close();
        } else if (event.data.includes("Command failed")) {
            updateStatus('MFOC Failed');
            eventSource.close();
        }
    };
    eventSource.onerror = function(error) {
        console.error('EventSource failed:', error);
        appendToConsole('Error: Command execution failed.\n');
        updateStatus('MFOC Failed'); // Update status on error
        eventSource.close();
    };
}

function writeCard() {
    const sourceFile = document.getElementById('sourceDmpFileList').value;
    const targetFile = document.getElementById('targetDmpFileList').value;
    const outputElement = document.getElementById('console');
    outputElement.textContent = 'Executing NFC Write...\n'; // Initial message for starting NFC Write
    updateStatus('Writing...'); // Update the status to "Writing..."

    fetch('/write-card', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `source_file=${encodeURIComponent(sourceFile)}&target_file=${encodeURIComponent(targetFile)}`
    }).then(response => response.text())
    .then(result => {
        appendToConsole(result); // Append result to the console
        if (result.includes("Command executed successfully.")) {
            updateStatus('Write Completed Successfully');
        } else if (result.includes("Command failed")) {
            updateStatus('Write Failed');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        appendToConsole('Error: Command execution failed.\n');
        updateStatus('Write Failed'); // Update status on error
    });
}

function scanNFC() {
    const outputElement = document.getElementById('console');
    outputElement.textContent = 'Scanning for NFC tags...\n'; // Initial message for starting NFC Scan
    updateStatus('Scanning...'); // Update the status to "Scanning..."

    const eventSource = new EventSource('/scan-nfc');
    eventSource.onmessage = function(event) {
        appendToConsole(event.data); // Append each new piece of data to the console
        if (event.data.includes("Command executed successfully.")) {
            updateStatus('Scan Completed Successfully');
            eventSource.close();
        } else if (event.data.includes("Command failed")) {
            updateStatus('Scan Failed');
            eventSource.close();
        }
    };
    eventSource.onerror = function(error) {
        console.error('EventSource failed:', error);
        appendToConsole('Error: Command execution failed.\n');
        updateStatus('Scan Failed'); // Update status on error
        eventSource.close();
    };
}

function fetchDmpFiles() {
    const sourceSelect = document.getElementById('sourceDmpFileList');
    const targetSelect = document.getElementById('targetDmpFileList');
    fetch('/list-dmp-files')
        .then(response => response.json())
        .then(files => {
            sourceSelect.innerHTML = ''; // Clear existing options
            targetSelect.innerHTML = '';
            files.forEach(file => {
                let option = document.createElement('option');
                option.value = file;
                option.textContent = file;
                sourceSelect.appendChild(option);
                targetSelect.appendChild(option.cloneNode(true));
            });
        })
        .catch(error => {
            console.error('Error fetching files:', error);
            sourceSelect.innerHTML = '<option>Error loading files</option>';
            targetSelect.innerHTML = '<option>Error loading files</option>';
        });
}

function updateStatus(message) {
    const statusText = document.getElementById('statusText');
    statusText.textContent = message;
}

function logout() {
    fetch('/logout', {
        method: 'GET',
    }).then(() => {
        window.location.href = '/login';
    }).catch(error => {
        console.error('Error during logout:', error);
    });
}
