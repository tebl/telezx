/**
 * Set image details field on webpage. If an empty string has been specified
 * then the string 'No information.' is shown instead.
 */
function web_set_tasl(content) {
    var element = document.getElementById('tasl');
    if (element == null) {
        return false;
    }

    content = content.trim()
    if (content.length == 0) {
        element.innerHTML = 'No information.';
        return false;
    }

    element.innerHTML = content;
    return true;
}


/**
 * Web page has separate sections for additional information, call the function
 * to toggle visibility of their content.
 */
function web_toggle_section(source, element_id) {
    var content = document.getElementById(element_id);
    source.classList.toggle('active_section');
    if (content.style.display == "block"){
        content.style.display = "none";
    } else {
        content.style.display = "block";
    }
}
