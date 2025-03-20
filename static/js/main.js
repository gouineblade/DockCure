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

async function scanImageGET(imageName) {
    try {
        const response = await fetch(`/scan?image_name=${encodeURIComponent(imageName)}`);
        if (response.ok) {
            const data = await response.json(); // assuming the response is JSON
            console.log("GET Response:", data);
        } else {
            console.error("GET request failed", response.status);
        }
    } catch (error) {
        console.error("Error during GET request:", error);
    }
}

async function scanImagePOST(imageName) {
    try {
        const response = await fetch("/scan", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ image_name: imageName })
        });
        if (response.ok) {
            const data = await response.json(); // assuming the response is JSON
            console.log("POST Response:", data);
        } else {
            console.error("POST request failed", response.status);
        }
    } catch (error) {
        console.error("Error during POST request:", error);
    }
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

