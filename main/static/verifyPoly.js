async function verifyPoly() {
    let polynomial = document.getElementById('polynomial').value; 

    // We must convert any plus signs 
    polynomial = convertPlusSigns(polynomial);

    const response = await fetch('/verifyPoly/?polynomial=' + polynomial); 
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

function convertPlusSigns(polynomial) {
    for(let i = 0; i < polynomial.length; i++) {
        if(polynomial.charAt(i) == '+') {
            let temp = polynomial.substring(0, i) + '%2B'; 
            if(i < polynomial.length - 1) {
                temp += polynomial.substring(i+1, polynomial.length);
            }
            polynomial = temp; 
        }
    }   

    return polynomial;
}