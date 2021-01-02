async function longPolling() {
    let response = await fetch("http://0.0.0.0:8000/notifications", {credentials: 'include'});

    if (response.status == 204) {
        await longPolling();
    } else if (response.status == 401) {
        console.log("Unauthorized for notifications");
    }
    else if (response.status != 200) {
        console.log(response);
        await new Promise(resolve => setTimeout(resolve, 1000));
        await longPolling();
    } else {
        let message = await response.text();
        alert(message);
        await longPolling();
    }
}

longPolling();