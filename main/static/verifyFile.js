async function verifyFile() {
    // get the uploaded file
    let fileInput = document.getElementsByName("csv")[0];
    let file = fileInput.files[0];
    console.log("Verifying...");
    const response = await fetch('/verifyFile/?filename=' + file); 
    let responseJSON = await response.json(); 

    let usernametext = document.getElementById('usernametext');

    // The .error class sets colour with !important, so an inline style cannot
    // override it. Toggle the class instead, otherwise a successful check
    // still renders red and reads as a failure.
    if(responseJSON['message'] == 'Valid') {
        usernametext.classList.remove('error');
        usernametext.style.color = 'green';
    } else {
        usernametext.classList.add('error');
        usernametext.style.color = '';
    }

    // Set the text's content to the message
    usernametext.innerHTML = responseJSON["message"]; 
}
