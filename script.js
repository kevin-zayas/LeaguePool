function handleRoleSelection() {
    var roleSelect = document.getElementById("role-select");
    var saveButton = document.getElementById("save-button");

    if (roleSelect.value === "") {
        saveButton.disabled = true;
    } else {
        saveButton.disabled = false;
    }
}

function handleRoleSave() {
    var roleSelect = document.getElementById("role-select");
    var selectedRole = roleSelect.value;

    // Make an HTTP GET request to the API endpoint
    var apiUrl = 'http://3.144.102.47:5000/champion-list?role=' + selectedRole;
    fetch(apiUrl)
        .then(response => response.json())
        .then(responseData => {
            var championList = responseData.champion_list;
            // Use the championList variable as needed
            console.log("Champion List:", championList);
        })
        .catch(error => {
            console.error("Error:", error);
        });
}
