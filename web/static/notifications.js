function displayNotification(text, type) {
    let notification = document.createElement("div");
    notification.className = "alert alert-" + type + " alert-dismissible fade show";
    notification.innerText = text;
    notification.setAttribute("role", "alert")

    let button = document.createElement("button");
    button.type = "button";
    button.className = "close"
    button.innerHTML = "&times;"
    button.setAttribute("data-dismiss", "alert")
    notification.appendChild(button)

    document.getElementById("messages").appendChild(notification)
}

async function longPolling() {
    let response = await fetch("http://0.0.0.0:8000/notifications", { credentials: "include" });

    if (response.status == 204) {
        await longPolling();
    }
    else if (response.status == 401) {
        displayNotification("Sesja wygasła, zaloguj się ponownie.", "warning")
        //window.location.reload();
    }
    else if (response.status != 200) {
        console.log(response);
        await new Promise(resolve => setTimeout(resolve, 1000));
        await longPolling();
    }
    else {
        let message = await response.text();
        displayNotification(message, "success")
        await longPolling();
    }
}

longPolling();