const firstname = document.getElementById("firstname");
const lastname = document.getElementById("lastname");
const password = document.getElementById("password");
const confirmPassword = document.getElementById("confirm_password");
const login = document.getElementById("login");
const form = document.getElementById('form');

const invalidLogin = document.getElementById("invalid-login");
const validLogin = document.getElementById("valid-login");
const invalidFirstname = document.getElementById("invalid-firstname");
const invalidLastname = document.getElementById("invalid-lastname");
const invalidPassword1 = document.getElementById("invalid-password-1");
const invalidPassword2 = document.getElementById("invalid-password-2");

let isLoginValid = false;

function setValidClass(form, isValid) {
    if (isValid) {
        form.classList.remove("is-invalid")
        form.classList.add("is-valid");
    } else {
        form.classList.remove("is-valid");
        form.classList.add("is-invalid");
    }
}

function isPasswordValid() {
    password1 = password.value;
    password2 = confirmPassword.value;

    errors = 0;
    if (password1.length > 0 && password2.length > 0) {
        if (password1.length >= 8) {
            setValidClass(password, true);
        } else {
            invalidPassword1.innerText = "Hasło musi mieć przynajmniej 8 znaków.";
            setValidClass(password, false);
            errors++;
        }

        if (password1 == password2) {
            setValidClass(confirmPassword, true);
        } else {
            invalidPassword2.innerText = "Hasła nie są takie same.";
            setValidClass(confirmPassword, false);
            errors++;
        }
    } else {
        errors++;
    }
    return errors == 0;
}

function checkCase(ch) {
    if (!isNaN(ch * 1)) {
        return "numeric";
    } else if (ch == ch.toUpperCase()) {
        return "upper";
    } else if (ch == ch.toLowerCase()) {
        return "lower";
    }
}

function isNameValid(name) {
    return (name.length >= 2
        && checkCase(name[0]) == "upper"
        && checkCase(name[1]) == "lower")
}

function submit(event) {
    if (!isPasswordValid
        || !isNameValid(firstname.value)
        || !isNameValid(lastname.value)
        || !isLoginValid) {
            
        event.preventDefault();
        alert("Formularz zawiera błędy.")
    }
}

function checkLoginAvailability() {
    const xhttp = new XMLHttpRequest();

    xhttp.onreadystatechange = function () {
        if (this.readyState == 4) {
            if (this.status == 200) {
                const response = JSON.parse(this.responseText);

                if (response[login.value] == "available") {
                    validLogin.innerText = "Wybrana nazwa użytkownika jest dostępna.";
                    setValidClass(login, true);
                    isLoginValid = true;
                } else {
                    invalidLogin.innerText = "Wybrana nazwa użytkownika jest zajęta.";
                    setValidClass(login, false);
                    isLoginValid = false;
                }
            } else {
                invalidLogin.innerText = "Błąd komunikacji z serwerem obsługującym rejestrację.";
                setValidClass(login, false);
                isLoginValid = false;
            }
        }
    };

    xhttp.open("GET", "https://infinite-hamlet-29399.herokuapp.com/check/" + login.value, true);
    xhttp.send();
}

function attachEvents() {
    form.onsubmit = submit;

    password.addEventListener("keyup", isPasswordValid);
    confirmPassword.addEventListener("keyup", isPasswordValid);

    login.addEventListener("change", function () {
        if (/^[a-z]+$/.test(login.value)) {
            checkLoginAvailability();
        } else {
            invalidLogin.innerText = "Nazwa użytkownika musi zawierać tylko małe litery.";
            setValidClass(login, false);
            isLoginValid = false;
        }
    });

    firstname.addEventListener("keyup", function () {
        invalidFirstname.innerText = "Imię musi zaczynać się wielką literą i mieć co najmniej jedną małą literę.";
        setValidClass(firstname, isNameValid(firstname.value));
    });

    lastname.addEventListener("keyup", function () {
        invalidLastname.innerText = "Imię musi zaczynać się wielką literą i mieć co najmniej jedną małą literę.";
        setValidClass(lastname, isNameValid(lastname.value));
    });
}

attachEvents()