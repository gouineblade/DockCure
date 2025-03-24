const API_URL = 'http://ajy3a0q7.fbxos.fr:44880'

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

// async function scanImageGET(imageName) {
//     try {
//         const response = await fetch(`${API_URL}/scan?image_name=${encodeURIComponent(imageName)}`);
//         if (response.ok) {
//             const data = await response.json(); // assuming the response is JSON
//             console.log("GET Response:", data);
//         } else {
//             console.error("GET request failed", response.status);
//         }
//     } catch (error) {
//         console.error("Error during GET request:", error);
//     }
// }

async function scanImage(imageName) {
    try {
        const response = await fetch(`${API_URL}/scan`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ image_name: imageName })
        });
        if (response.ok) {
            const data = await response.json(); // assuming the response is JSON
            await fetchScanResults(imageName)
        } else {
            console.error("POST request failed", response.status);
        }
    } catch (error) {
        console.error("Error during POST request:", error);
    }
}

async function fetchScanResults(imageName, interval = 1000) {
    try {
        const response = await fetch(`${API_URL}/analyze`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ image_name: imageName })
        });

        if (response.status === 400) {
            // L'image est en cours de scan
            showLoading(`Currently scanning ${imageName}, please wait...`);

            // Attendre avant de relancer la requête
            setTimeout(() => fetchScanResults(imageName, interval), interval);
            // return;
        }

        else if (response.status === 401) {
            return 'error';
        }

        else if (response.status === 200) {
            hideLoading();
            const data = await response.json(); // Récupérer les données correctement
            // console.log("Scan terminé :", data);
            appendScanResultToTable(data);
            return;
        }

    } catch (error) {
        console.error("Error during POST request:", error);
    }
}


function editElementContent(elementId, content) {
    $(elementId).html(content);
}

function showLoading(text) {
    $("#loadingSpinner").css("display", "inline-block"); // Affiche le spinner
    $("#loadingText").css("display", "inline").text(text); // Affiche et met à jour le texte
}

function hideLoading() {
    $("#loadingSpinner, #loadingText").css("display", "none"); // Cache les deux
}

/**
 * 
 * @param {JSON} scanResult 
 */
function appendScanResultToTable(scanResult) {
    for (const package of scanResult.analysis) {
        const row = $('<tr></tr>');
        row.append($("<td></td>").text(package.package));
        row.append($("<td></td>").text(package.version));
        row.append($("<td></td>").text("CVEs"));
        if (package.package in scanResult.packages_to_update) {
            row.append($("<td></td>").text(scanResult.packages_to_update[package.package]));
        }
        else {

        }
    // Append the row to the table
    $("#scanResults").append(row);
    }
}


// Functions assignations on HTML elements

document.getElementById("scanButton").addEventListener("click", function () {
    const imageName = document.getElementById("dockerImage").value.trim();
    if (!imageName) {
        editElementContent("#scanModalContent", "Please enter a valid Docker Image.");
        $('#scanModal').modal('show');
        return;
    }

    scanImage(imageName);
});

