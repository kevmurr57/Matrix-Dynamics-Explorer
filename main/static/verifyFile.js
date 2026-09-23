async function verifyFile() {
    const fileInput = document.getElementsByName("csv")[0];
    const usernametext = document.getElementById('usernametext');

    function report(message, ok) {
        // .error sets colour with !important, so toggle the class rather
        // than trying to override it with an inline style.
        if (ok) {
            usernametext.classList.remove('error');
            usernametext.style.color = 'green';
        } else {
            usernametext.classList.add('error');
            usernametext.style.color = '';
        }
        usernametext.innerHTML = message;
    }

    const file = fileInput && fileInput.files ? fileInput.files[0] : null;

    if (!file) {
        report('No file selected', false);
        return;
    }

    // The file's contents have to reach the server, so post it as form data.
    // This previously interpolated the File object into a query string, which
    // stringifies to "[object File]" and hit a route that did not exist.
    const body = new FormData();
    body.append('csv', file);

    const csrf_token = document.querySelector('[name=csrfmiddlewaretoken]').value;

    try {
        const response = await fetch('/verifyFile/', {
            method: 'POST',
            headers: { 'X-CSRFToken': csrf_token },
            mode: 'same-origin',
            body: body
        });

        const responseJSON = await response.json();
        const message = responseJSON['message'];
        report(message, message === 'Valid');
    } catch (err) {
        report('Could not reach the server', false);
    }
}
