document.addEventListener("DOMContentLoaded", function () {
    fetch("/data/learn.json")
        .then(response => {
            if (!response.ok) {
                throw new Error("Failed to fetch learn.json");
            }
            return response.json();
        })
        .then(data => {
            const container = document.getElementById("topics");
            container.innerHTML = "";

            Object.keys(data).forEach(key => {
                const link = document.createElement("a");
                link.href = data[key];
                link.className = "btn btn-primary m-2 col-auto";
                link.innerText = capitalize(key);
                container.appendChild(link);
            });
        })
        .catch(err => {
            console.error(err);
        });
});

function capitalize(text) {
    return text.charAt(0).toUpperCase() + text.slice(1);
}

// optional helper for checkpoint pages
function saveCheckpointAnswers(answerData) {
    fetch("/learn/checkpoint/save", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(answerData)
    })
    .then(response => response.json())
    .then(data => {
        console.log("Checkpoint saved:", data);
    })
    .catch(error => {
        console.error("Error saving checkpoint:", error);
    });
}