const firstname = document.getElementById("firstname");
const lastname = document.getElementById("lastname");
const password = document.getElementById("password");
const confirm_password = document.getElementById("confirm_password");
const login = document.getElementById("login");
const form = document.getElementById('form');

function setValid(form) {
    form.classList.remove("is-invalid")
    form.classList.add("is-valid");
}

function setInvalid(form) {
    form.classList.remove("is-valid");
    form.classList.add("is-invalid");
}


function check_password() {
    password1 = password.value;
    password2 = confirm_password.value;

    errors = 0;
    if (password1.length > 0 && password2.length > 0) {
        if (password1.length >= 8) {
            setValid(password);
        } else {
            setInvalid(password);
            errors++;
        }

        if (password1 == password2) {
            setValid(confirm_password);
        } else {
            setInvalid(confirm_password);
            errors++;
        }
    } else {
        errors++;
    }
    return errors;
}

function checkCase(ch) {
    if (!isNaN(ch * 1)) {
        return "numeric";
    }
    else if (ch == ch.toUpperCase()) {
        return "upper";
    }
    else if (ch == ch.toLowerCase()) {
        return "lower";
    }
}

function checkName(name) {
    if (name.length >= 2 && checkCase(name[0]) == "upper" && checkCase(name[1]) == "lower") {
        return 0;
    } else {
        return 1;
    }
}

function submit(event) {
    errors = check_password() + checkName(firstname.value) + checkName(lastname.value);

    if (errors > 0) {
        event.preventDefault();
        alert("Formularz zawiera błędy.")
    }
}

function attachEvents() {
    form.onsubmit = submit;

    login.addEventListener("change", function () {
        if (/^[a-z]+$/.test(login.value)) {
            setValid(login);
        } else {
            setInvalid(login);
        }
    });

    firstname.addEventListener("keyup", function () {
        if (checkName(firstname.value) == 0) {
            setValid(firstname);
        } else {
            setInvalid(firstname);
        }
    });

    lastname.addEventListener("keyup", function () {
        if (checkName(lastname.value) == 0) {
            setValid(lastname);
        } else {
            setInvalid(lastname);
        }
    });

    password.addEventListener("keyup", check_password);
    confirm_password.addEventListener("keyup", check_password);
}

attachEvents()