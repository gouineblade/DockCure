const API_URL = 'http://ajy3a0q7.fbxos.fr:44880'

// Allows pressing enter on the text input
$(document).ready(function() {
    $("#dockerImage").keypress(function(event) {
        if (event.which === 13) {  // 13 = Touche "Enter"
            event.preventDefault(); // Prevent reloading of the page
            $("#scanButton").click(); // Triggers click on scanButton
        }
    });
});

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
        const packageId = package.package.replace(/[^a-zA-Z0-9]/g, "_");
        const modalId = `cveModal_${packageId}`;

        const row = $('<tr></tr>');
        row.append($("<td></td>").text(package.package));
        row.append($("<td></td>").text(package.version));

        if (package.cve) {
            const cveButton = $(`<button class="btn btn-warning btn-sm" data-bs-toggle="modal" data-bs-target="#${modalId}">Voir CVEs</button>`);
            row.append($(`<td class="d-flex justify-content-between align-items-center" id=cve_${packageId}></td>`).append(cveButton));
        }
        else
        {
            row.append($("<td></td>").text("N/A"));
        }
        row.append($(`<td style="font-size: 0.5em;"></td>`).text(package.master_package))
        if (package.package in scanResult.packages_to_update) {
            row.append($("<td></td>").text(scanResult.packages_to_update[package.package]));
        }
        else {
            row.append($("<td></td>").text("N/A"));
        }
    // Append the row to the table
    $("#scanResults").append(row);
    let cveCount = 0;
    console.log(package);

         // Génération de la modal associée
         let modalContent = `
         <div class="modal fade" id="${modalId}" tabindex="-1" aria-labelledby="${modalId}Label" aria-hidden="true">
             <div class="modal-dialog modal-lg">
                 <div class="modal-content">
                     <div class="modal-header">
                         <h5 class="modal-title" id="${modalId}Label">CVEs pour ${package.package}</h5>
                         <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                     </div>
                     <div class="modal-body">
                         <table class="table table-striped">
                             <thead>
                                 <tr>
                                     <th scope="col">CVE ID</th>
                                     <th scope="col">Severity</th>
                                 </tr>
                             </thead>
                             <tbody>`;

    // critical, high, medium, low, negligible, unknown
    if (package.cve.critical) {
        package.cve.critical.forEach(cve => {
            cveCount++;
            modalContent += `
            <tr>
                <td><a href="https://nvd.nist.gov/vuln/detail/${cve}">${cve}</a></td>
                <td class="text-danger">Critical</td>
            </tr>
            `;
        })
    }
    if (package.cve.high) {
        package.cve.high.forEach(cve => {
            cveCount++;
            modalContent += `
            <tr>
                <td><a href="https://nvd.nist.gov/vuln/detail/${cve}">${cve}</a></td>
                <td class="text-warning">High</td>
            </tr>
            `;
        })
    }
    if (package.cve.medium) {
        package.cve.medium.forEach(cve => {
            cveCount++;
            modalContent += `
            <tr>
                <td><a href="https://nvd.nist.gov/vuln/detail/${cve}">${cve}</a></td>
                <td class="text-secondary">Medium</td>
            </tr>
            `;
        })
    }
    if (package.cve.low) {
        package.cve.low.forEach(cve => {
            cveCount++;
            modalContent += `
            <tr>
                <td><a href="https://nvd.nist.gov/vuln/detail/${cve}">${cve}</a></td>
                <td class="text-primary">Low</td>
            </tr>
            `;
        })
    }
    if (package.cve.negligible) {
        package.cve.negligible.forEach(cve => {
            cveCount++;
            modalContent += `
            <tr>
                <td><a href="https://nvd.nist.gov/vuln/detail/${cve}">${cve}</a></td>
                <td class="text-info">Negligible</td>
            </tr>
            `;
        })
    }
    if (package.cve.unknown) {
        package.cve.unknown.forEach(cve => {
            cveCount++;
            modalContent += `
            <tr>
                <td><a href="https://nvd.nist.gov/vuln/detail/${cve}">${cve}</a></td>
                <td class="text-dark">Unknown</td>
            </tr>
            `;
        })
    }

    // Modal on the CVE button
     modalContent += `
                             </tbody>
                         </table>
                     </div>
                     <div class="modal-footer">
                         <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fermer</button>
                     </div>
                 </div>
             </div>
         </div>`;

    $(`#cve_${packageId}`).append($("<span></span>").text(cveCount));

     $("body").append(modalContent); // Add the modal to the body
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

