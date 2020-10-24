const firstname = document.getElementById("firstname");
const password = document.getElementById("password");
const confirm_password = document.getElementById("confirm_password");
const form = document.getElementById('form');

function check_password() {
    password1 = password.value;
    password2 = confirm_password.value;

    passwords_not_match = document.getElementById("passwords_dont_match");
    password_too_weak = document.getElementById("password_too_weak");

    if (password1.length > 0 && password2.length > 0) {
        if (password1 === password2) {
            passwords_not_match.hidden = true;

            if (password1.length < 8) {
                password.className = "error";
                confirm_password.className = "error";

                password_too_weak.hidden = false;
                return 1;
            } else {
                password.className = "ok";
                confirm_password.className = "ok";

                password_too_weak.hidden = true;
                return 0;
            }
        } else {
            password.className = "error";
            confirm_password.className = "error";
            passwords_not_match.hidden = false;
            password_too_weak.hidden = true;
            return 1;
        }
    }
}

function submit(event) {
    errors = check_password();

    if (errors > 0) {
        event.preventDefault();
        alert("Formularz zawiera błędy.")
    }
}

function attach_events() {
    form.onsubmit = submit;

    firstname.addEventListener("change", function () {
        console.log(firstname.value)
    });

    password.addEventListener("keyup", check_password);
    confirm_password.addEventListener("keyup", check_password);
}

attach_events()