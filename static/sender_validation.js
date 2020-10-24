const firstname = document.getElementById("firstname");
const password = document.getElementById("password");
const confirm_password = document.getElementById("confirm_password");
const form = document.getElementById('form');

function check_password() {
    password1 = password.value;
    password2 = confirm_password.value;

    p = document.getElementById("password_error");

    if (password1.length > 0 && password2.length > 0) {
        if (password1 === password2) {
            password.className = "";
            confirm_password.className = "";
            p.hidden = true;
            return 0;
        } else {
            password.className = "error";
            confirm_password.className = "error";
            p.hidden = false;
            return 1;
        }
    }
}

function submit(event) {
    errors = check_password();

    if (errors > 0) {
        event.preventDefault();
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