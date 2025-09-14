document.addEventListener('DOMContentLoaded', () => {
    const saveButton = document.getElementById('save-button');
    const defaultsButton = document.getElementById('defaults-button');
    const messageOverlay = document.getElementById('message-overlay');
    const userNameInput = document.getElementById('user_name');
    const sidekickNameInput = document.getElementById('sidekick_name');

    saveButton.addEventListener('click', () => {
        const userName = userNameInput.value;
        const sidekickName = sidekickNameInput.value;

        const data = {
            user_name: userName,
            sidekick_name: sidekickName
        };

        fetch('/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams(data).toString()
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                messageOverlay.innerHTML = '<p>Settings saved! Your Sidekick will now continue to the main menu.</p>';
                messageOverlay.classList.remove('hidden');
            } else {
                messageOverlay.innerHTML = '<p>An error occurred. Please try again.</p><button id="error-ok-button">OK</button>';
                messageOverlay.classList.remove('hidden');
                document.getElementById('error-ok-button').addEventListener('click', () => {
                    messageOverlay.classList.add('hidden');
                });
            }
        })
        .catch(error => {
            console.error('Error:', error);
            messageOverlay.innerHTML = '<p>An error occurred. Please try again.</p><button id="error-ok-button">OK</button>';
            messageOverlay.classList.remove('hidden');
            document.getElementById('error-ok-button').addEventListener('click', () => {
                messageOverlay.classList.add('hidden');
            });
        });
    });

    defaultsButton.addEventListener('click', () => {
        userNameInput.value = 'User';
        sidekickNameInput.value = 'Sidekick';
    });
});