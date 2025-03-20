function addScanResult(package, version, fixableVersion, cve, security) {
    const tableBody = document.getElementById("scanResults");
    const row = document.createElement("tr");
    
    row.innerHTML = `
        <td>${package}</td>
        <td>${version}</td>
        <td>${fixableVersion || "N/A"}</td>
        <td>${cve}</td>
        <td>${security}</td>
        <td><button class="btn btn-danger btn-sm">N/A</button></td>
    `;
    
    tableBody.appendChild(row);
}

function scanImageGET(imageName) {
    const xhr = new XMLHttpRequest();
    xhr.open("GET", `/scan?image_name=${encodeURIComponent(imageName)}`, true);
    xhr.setRequestHeader("Content-Type", "application/json");

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            console.log("GET Response:", xhr.responseText);
        }
    };

    xhr.send();
}

function scanImagePOST(imageName) {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/scan", true);
    xhr.setRequestHeader("Content-Type", "application/json");

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            console.log("POST Response:", xhr.responseText);
        }
    };

    const data = JSON.stringify({ image_name: imageName });
    xhr.send(data);
}

function editElementContent(elementId, content) {
    $(elementId).html(content);
}


// Functions assignations on HTML elements

document.getElementById("scanButton").addEventListener("click", function () {
    const imageName = document.getElementById("dockerImage").value.trim();
    if (!imageName) {
        editElementContent("#scanModalContent", "Please enter a valid Docker Image.");
        $('#scanModal').modal('show');
        return;
    }

    scanImageGET(imageName);

    scanImagePOST(imageName);
});

