// Check if this is an hu.nl e-mail address
// Add "unlimited lease time" for usage by specific e-mail addresses
function processMailAddress() {

    // edit line below, but don't forget to add server side validation
    var trustedEmailAddresses = [
        "aaa@hu.nl",
        "bbb@hu.nl",
        "ccc@hu.nl",
    ]

    var eMail = document.getElementById('huMail').value
    if (! eMail.match(/(\@student\.|\@)hu\.nl$/i)) {
        alert("Dit geen geldig HU e-mail adres.")
    }

    if (trustedEmailAddresses.indexOf(eMail) > -1) {
        var select = document.getElementById("expiration");
        select.options[select.options.length] = new Option('Onbeperkt', 'Onbeperkt');
    }
}

// Validate MAC-address provided
function processMacAddress() {

    var mac = document.getElementById('macAddress').value
    if (! mac.match(/^([0-9A-Fa-f]{2}[-]){5}([0-9A-Fa-f]{2})$/i)) {
        alert("Dit geen geldig MAC-adres van 6 hexadecimale getallen gescheiden door een '-'")
    }
}

// User must accept the conditions before submitting the form
function validateForm() {
    var x = document.forms["request_code"]["accept_conditions"].checked;
    if (x == false) {
        alert("Je moet de voorwaarden accepteren om een code te kunnen aanvragen.");
        return false;
    }
}
