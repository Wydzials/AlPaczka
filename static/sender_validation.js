const firstname = document.getElementById("firstname");
const lastname = document.getElementById("lastname");
const password = document.getElementById("password");
const confirmPassword = document.getElementById("confirm_password");
const login = document.getElementById("login");
const form = document.getElementById('form');

const invalidFirstname = document.getElementById("invalid-firstname");
const invalidLastname = document.getElementById("invalid-lastname");
const invalidPassword1 = document.getElementById("invalid-password-1");
const invalidPassword2 = document.getElementById("invalid-password-2");
const invalidLogin = document.getElementById("invalid-login");
const validLogin = document.getElementById("valid-login");

let isLoginFieldValid = false;

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
    return (errors == 0);
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
    return (/^[A-ZĄĆĘŁŃÓŚŹŻ][a-ząćęłńóśźż]+$/.test(name));
}

function submit(event) {
    if (!isPasswordValid()
        || !isNameValid(firstname.value)
        || !isNameValid(lastname.value)
        || !isLoginFieldValid) {

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
                    isLoginFieldValid = true;
                } else {
                    invalidLogin.innerText = "Wybrana nazwa użytkownika jest zajęta.";
                    setValidClass(login, false);
                    isLoginFieldValid = false;
                }
            } else {
                invalidLogin.innerText = "Błąd komunikacji z serwerem obsługującym rejestrację.";
                setValidClass(login, false);
                isLoginFieldValid = false;
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
        value = login.value;
        if (/^[a-z]+$/.test(value) && value.length >= 3 && value.length <= 12) {
            checkLoginAvailability();
        } else {
            invalidLogin.innerText = "Nazwa użytkownika powinna składać się z małych liter i zawierać od 3 do 12 znaków.";
            setValidClass(login, false);
            isLoginFieldValid = false;
        }
    });

    firstname.addEventListener("keyup", function () {
        invalidFirstname.innerText = "Imię musi zaczynać się od wielkiej litery i składać tylko z liter.";
        setValidClass(firstname, isNameValid(firstname.value));
    });

    lastname.addEventListener("keyup", function () {
        invalidLastname.innerText = "Nazwisko musi zaczynać się od wielkiej litery i składać tylko z liter.";
        setValidClass(lastname, isNameValid(lastname.value));
    });
}

attachEvents()