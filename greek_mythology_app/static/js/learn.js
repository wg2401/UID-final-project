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

            Object.keys(data).forEach(key => {
                const link = document.createElement("a");
                link.href = data[key];

                link.className = "btn btn-primary m-2";
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