const API_URL = 'http://ajy3a0q7.fbxos.fr:44880'

let fixArgs = null;

function addPackageToFixArgs(p_package, p_action)
{
    for (package of fixArgs.packages)
    {
        if (package.libname == p_package)
        {
            package.action = p_action
            // Exit the function if we did what we needed to
            return; 
        }
    }
    // If we didn't find the package in fixArgs, add it
    fixArgs.packages.push({
        "action": p_action,
        "libname": p_package
    })
}

$(document).ready(function() {
    let selectedRows = new Set();
    
    // Permet de sélectionner une ligne avec clic gauche
    $("#scanResults").on("click", "tr", function(event) {
        if (!event.ctrlKey && !event.shiftKey) {
            $("#scanResults tr").removeClass("selected");
            selectedRows.clear();
        }
        $(this).toggleClass("selected");
        selectedRows.has(this) ? selectedRows.delete(this) : selectedRows.add(this);
    });
    
    // Gestion du menu contextuel
    $("#scanResults").on("contextmenu", "tr", function(event) {
        event.preventDefault();
        
        let menuHtml = `<ul id="contextMenu" class="dropdown-menu show" style="position:absolute; top:${event.pageY}px; left:${event.pageX}px;">
            <li><a class="dropdown-item" href="#" id="upgradeLatest">Upgrade to Latest</a></li>
            <li><a class="dropdown-item" href="#" id="upgradeRecommended">Upgrade to Recommended</a></li>
            <li><a class="dropdown-item" href="#" id="remove">Remove</a></li>`;
        
        if (selectedRows.size === 1) {
            menuHtml += `<li><a class="dropdown-item" href="#" id="upgradeCustom">Upgrade to...</a></li>`;
        }
        
        menuHtml += `</ul>`;
        $("body").append(menuHtml);
    });
    
    // Action : Upgrade to latest
    $(document).on("click", "#upgradeLatest", function() {
        selectedRows.forEach(row => {
            $(row).find("td:nth-child(6)").text("Latest");
            addPackageToFixArgs($(row).find("td:nth-child(1)").text(), "upgrade");
        });
        $("#contextMenu").remove();
    });
    
    // Action : Upgrade to recommended
    $(document).on("click", "#upgradeRecommended", function() {
        selectedRows.forEach(row => {
            let recommendedVersion = $(row).find("td:nth-child(5)").text();
            if (recommendedVersion !== "N/A") {
                $(row).find("td:nth-child(6)").text(recommendedVersion);
                addPackageToFixArgs($(row).find("td:nth-child(1)").text(), "upgrade_"+$(row).find("td:nth-child(5)").text());
            }
        });
        $("#contextMenu").remove();
    });
    
    // Action : Remove
    $(document).on("click", "#remove", function() {
        selectedRows.forEach(row => {
            $(row).find("td:nth-child(6)").text("Remove");
            addPackageToFixArgs($(row).find("td:nth-child(1)").text(), "remove");
        });
        $("#contextMenu").remove();
    });
    
    // Action : Upgrade to custom version (ouvre une modal)
    $(document).on("click", "#upgradeCustom", function() {
        let modalHtml = `<div class="modal fade" id="upgradeModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Enter Custom Version</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <input type="text" id="customVersion" class="form-control" placeholder="Enter version">
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" id="confirmUpgrade">Upgrade</button>
                    </div>
                </div>
            </div>
        </div>`;
        
        $("body").append(modalHtml);
        $("#upgradeModal").modal("show");
        $("#contextMenu").remove();
    });
    
    // Confirmer la mise à jour personnalisée
    $(document).on("click", "#confirmUpgrade", function() {
        let newVersion = $("#customVersion").val();
        if (newVersion) {
            selectedRows.forEach(row => $(row).find("td:nth-child(6)").text(newVersion));
            addPackageToFixArgs($(row).find("td:nth-child(1)").text(), "upgrade_"+newVersion);
        }
        $("#upgradeModal").modal("hide").remove();
    });
    
    // Supprime le menu contextuel si on clique ailleurs
    $(document).click(function(event) {
        if (!$(event.target).closest("#contextMenu").length) {
            $("#contextMenu").remove();
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

function resetScan() {
    $('#scanResults').empty();  // Removes everything from this table body
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
            $("#downloadButton").css("display", "none");
            const data = await response.json();
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
            showLoading(`Currently scanning ${imageName}, please wait...`);

            setTimeout(() => fetchScanResults(imageName, interval), interval);
        }

        else if (response.status === 401) {
            return 'error';
        }

        else if (response.status === 200) {
            hideLoading();
            const data = await response.json();
            appendScanResultToTable(data);
            return;
        }

    } catch (error) {
        console.error("Error during POST request:", error);
    }
}

async function fixImage() {
    try {
        showLoading(`Currently fixing ${fixArgs.image_name}, please wait...`)
        const response = await fetch(`${API_URL}/fix`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(fixArgs)
        });
        if (response.ok) {
            $("#downloadButton").css("display", "block");
            
        } else if (response.status == 400) 
        {
            const data = await response.json(); // Récupère le JSON
            const message = data.message || '';  // Extrait le message du JSON

            // Affiche le message dans #logs avec un focus
            $("#logs").text(message).focus();
        }
        else {
            console.error("POST request failed", response.status);
        }
        hideLoading();
    } catch (error) {
        console.error("Error during POST request:", error);
    }
}

async function autofixImage() {
    try {
        showLoading(`Currently fixing ${fixArgs.image_name}, please wait...`);
        
        const response = await fetch(`${API_URL}/autofix`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ "image_name": fixArgs.image_name })
        });

        if (response.ok) {
            $("#downloadButton").css("display", "block");
        } else if (response.status === 400) {
            const data = await response.json();
            const message = data.message || '';
            $("#logs").text(message).focus();
        } else {
            console.error("POST request failed", response.json());
        }
        hideLoading();
    } catch (error) {
        console.error("Error during POST request:", error);
    }
}

async function downloadImage() {
        const response = await fetch(`${API_URL}/image`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({image_name: fixArgs.image_name + "-secure"})
        })
        .then(response => {
            if (!response.ok) {
                // En cas d'erreur (400 ou 404), on récupère le message d'erreur depuis la réponse
                return response.json().then(data => {
                    alert(data.error);
                    throw new Error(data.error);
                });
            }
            // Conversion de la réponse en Blob pour le téléchargement
            return response.blob();
        })
        .then(blob => {
            // Création d'un lien temporaire pour lancer le téléchargement
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = fixArgs.image_name + "-secure" + ".tar";
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        })
        .catch(error => console.error("Erreur:", error));
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
            const cveButton = $(`<button class="btn btn-warning btn-sm" data-bs-toggle="modal" data-bs-target="#${modalId}">CVEs</button>`);
            row.append($(`<td class="d-flex justify-content-between align-items-center" id=cve_${packageId}></td>`).append(cveButton));
        }
        else
        {
            row.append($("<td></td>").text("N/A"));
        }
        row.append($(`<td style="font-size: 0.8em;"></td>`).text(package.master_package))
        if (package.package in scanResult.packages_to_update) {
            row.append($("<td></td>").text(scanResult.packages_to_update[package.package]));
        }
        else {
            row.append($("<td></td>").text("N/A"));
        }
        row.append($("<td></td>").text("N/A"));
    // Append the row to the table
    $("#scanResults").append(row);
    let cveCount = 0;
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
    resetScan();
    const imageName = document.getElementById("dockerImage").value.trim();
    if (!imageName) {
        editElementContent("#scanModalContent", "Please enter a valid Docker Image.");
        $('#scanModal').modal('show');
        return;
    }

    scanImage(imageName);
    fixArgs = {
        "image_name": imageName,
        // "new_name": imageName + "_fix",
        packages: [

        ]
    }
});



document.getElementById("fixButton").addEventListener("click", function () {
    fixImage();
});

document.getElementById("autofixButton").addEventListener("click", function () {
    autofixImage();
})

document.getElementById("downloadButton").addEventListener("click", function () {
    downloadImage();
})