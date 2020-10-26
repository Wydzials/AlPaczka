const firstname = document.getElementById("firstname");
const lastname = document.getElementById("lastname");
const password = document.getElementById("password");
const confirm_password = document.getElementById("confirm_password");
const login = document.getElementById("login");
const form = document.getElementById('form');
const invalid_login = document.getElementById("invalid-login");

let isLoginValid = false;

function setValid(form) {
    form.classList.remove("is-invalid")
    form.classList.add("is-valid");
}

function setInvalid(form) {
    form.classList.remove("is-valid");
    form.classList.add("is-invalid");
}


function checkPassword() {
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
    errors = checkPassword() + checkName(firstname.value) + checkName(lastname.value);

    if (errors > 0 || isLoginValid == false) {
        event.preventDefault();
        alert("Formularz zawiera błędy.")
    }
}

function ajaxLoginCheck() {
    const xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function () {
        if (this.readyState == 4) {
            if (this.status == 200) {
                const response = JSON.parse(this.responseText);

                if (response[login.value] == "available") {
                    setValid(login);
                    console.log(response[login.value]);
                    isLoginValid = true;
                } else {
                    invalid_login.innerText = "Wybrana nazwa użytkownika jest zajęta.";
                    setInvalid(login);
                    isLoginValid = false;
                }
            } else {
                invalid_login.innerText = "Błąd komunikacji z serwerem obsługującym rejestrację.";
                setInvalid(login);
                isLoginValid = false;
            }
        }
    };

    xhttp.open("GET", "https://infinite-hamlet-29399.herokuapp.com/check/" + login.value, true);
    xhttp.send();
}

function attachEvents() {
    form.onsubmit = submit;

    login.addEventListener("change", function () {
        if (/^[a-z]+$/.test(login.value)) {
            ajaxLoginCheck();
        } else {
            invalid_login.innerText = "Nazwa użytkownika musi zawierać tylko małe litery.";
            setInvalid(login);
            isLoginValid = false;
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

    password.addEventListener("keyup", checkPassword);
    confirm_password.addEventListener("keyup", checkPassword);
}

attachEvents()