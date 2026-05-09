document.addEventListener("DOMContentLoaded", function () {
    const progressScript = document.getElementById("learning-progress-data");
window.learningProgress = progressScript ? JSON.parse(progressScript.textContent) : {};

const progressBar = document.getElementById("topic-progress-bar");
if (progressBar) {
    const completed = Number(progressBar.dataset.completed || 0);
    const total = Number(progressBar.dataset.total || 0);
    const percent = total > 0 ? (completed / total) * 100 : 0;
    progressBar.style.width = percent + "%";
}
    fetch("/data/learn.json")
        .then(function (response) {
            if (!response.ok) {
                throw new Error("Failed to fetch learn.json");
            }
            return response.json();
        })
        .then(function (data) {
            const container = document.getElementById("topics");
            container.innerHTML = "";

            const progress = window.learningProgress || {};
            const completedTopics = new Set(progress.completed_topics || []);
            const sectionStatus = progress.section_status || {};

            Object.keys(data).forEach(function (key) {
                const href = data[key];
                const status = sectionStatus[key] || {};
                const completed = completedTopics.has(key) || status.completed === true;
                const visited = status.visited === true;

                const col = document.createElement("div");
                col.className = "col-md-4";

                const card = document.createElement("div");
                card.className = "card shadow-sm topic-card";

                const cardBody = document.createElement("div");
                cardBody.className = "card-body d-flex flex-column";

                const title = document.createElement("h5");
                title.className = "card-title";
                title.innerText = formatTopicName(key);

                const statusText = document.createElement("p");
                statusText.className = "mb-3";

                if (completed) {
                    statusText.innerHTML = '<span class="badge bg-success">Completed</span>';
                } else if (visited) {
                    statusText.innerHTML = '<span class="badge bg-primary">Visited</span>';
                } else {
                    statusText.innerHTML = '<span class="badge bg-secondary">Not Started</span>';
                }

                const desc = document.createElement("p");
                desc.className = "text-muted small flex-grow-1";
                desc.innerText = getTopicDescription(key);

                const link = document.createElement("a");
                link.href = href;
                link.className = completed
                    ? "btn btn-outline-success mt-auto"
                    : "btn btn-primary mt-auto";

                if (completed) {
                    link.innerText = "Review Topic";
                } else if (visited) {
                    link.innerText = "Continue Topic";
                } else {
                    link.innerText = "Start Topic";
                }

                cardBody.appendChild(title);
                cardBody.appendChild(statusText);
                cardBody.appendChild(desc);
                cardBody.appendChild(link);
                card.appendChild(cardBody);
                col.appendChild(card);
                container.appendChild(col);
            });
        })
        .catch(function (err) {
            console.error(err);

            const container = document.getElementById("topics");
            container.innerHTML = `
                <div class="col-12">
                    <div class="alert alert-danger">
                        Could not load learning topics.
                    </div>
                </div>
            `;
        });
});

function formatTopicName(text) {
    if (text === "symbols") {
        return "Symbols";
    }

    if (text === "relationships") {
        return "Relationships";
    }

    return text.charAt(0).toUpperCase() + text.slice(1);
}

function getTopicDescription(topic) {
    if (topic === "zeus") {
        return "Learn about Zeus, king of the gods, and his connection to the sky and lightning";
    }

    if (topic === "poseidon") {
        return "Learn about Poseidon, ruler of the sea, earthquakes, and oceans";
    }

    if (topic === "athena") {
        return "Learn about Athena, goddess of wisdom, strategy, and intelligence";
    }

    if (topic === "aphrodite") {
        return "Learn about Aphrodite, goddess of love, beauty, and desire";
    }

    if (topic === "relationships") {
        return "Review how the gods are connected and why those family ties matter";
    }

    if (topic === "symbols") {
        return "Learn the symbols associated with each Olympian god and what they represent";
    }

    return "Open this learning topic.";
}

function saveCheckpointAnswers(answerData) {
    fetch("/learn/checkpoint/save", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(answerData)
    })
    .then(function (response) {
        return response.json();
    })
    .then(function (data) {
        console.log("Checkpoint saved:", data);
    })
    .catch(function (error) {
        console.error("Error saving checkpoint:", error);
    });
}