const canvas = document.getElementById("line-canvas");
const ctx = canvas.getContext("2d");

const container = document.getElementById("match-container");
const submitBtn = document.getElementById("submit-btn");

let startElem = null;
let isDrawing = false;
let connections = [];

function resizeCanvas() {
    canvas.width = container.offsetWidth;
    canvas.height = container.offsetHeight;
    redraw();
}
resizeCanvas();
window.addEventListener("resize", resizeCanvas);

function getCenter(el) {
    const rect = el.getBoundingClientRect();
    const parentRect = container.getBoundingClientRect();

    return {
        x: rect.left - parentRect.left + rect.width / 2,
        y: rect.top - parentRect.top + rect.height / 2
    };
}

function redraw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    connections.forEach(conn => {
        const start = getCenter(conn.left);
        const end = getCenter(conn.right);
        drawLine(start, end);
    });
}

function drawLine(start, end) {
    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    ctx.lineTo(end.x, end.y);
    ctx.strokeStyle = "black";
    ctx.lineWidth = 2;
    ctx.stroke();
}

document.querySelectorAll(".left-item").forEach(item => {
    item.addEventListener("mousedown", () => {
        startElem = item;
        isDrawing = true;
    });
});

document.addEventListener("mousemove", (e) => {
    if (!isDrawing || !startElem) return;

    redraw();

    const start = getCenter(startElem);
    const parentRect = container.getBoundingClientRect();

    const current = {
        x: e.clientX - parentRect.left,
        y: e.clientY - parentRect.top
    };

    drawLine(start, current);
});

document.addEventListener("mouseup", (e) => {
    if (!isDrawing || !startElem) return;

    let matched = null;

    document.querySelectorAll(".right-item").forEach(item => {
        const rect = item.getBoundingClientRect();

        if (
            e.clientX >= rect.left &&
            e.clientX <= rect.right &&
            e.clientY >= rect.top &&
            e.clientY <= rect.bottom
        ) {
            matched = item;
        }
    });

    if (matched) {
        connections = connections.filter(c => c.left !== startElem);

        connections.push({
            left: startElem,
            right: matched
        });
    }

    isDrawing = false;
    startElem = null;

    redraw();

    const totalLeft = document.querySelectorAll(".left-item").length;
    if (connections.length === totalLeft) {
        submitBtn.style.display = "inline-block";
    }
});

submitBtn.addEventListener("click", () => {
    const payload = {};

    connections.forEach(conn => {
        const leftId = conn.left.dataset.id;
        const rightId = conn.right.dataset.id;
        payload[leftId] = rightId;
    });

    fetch("/match/submit", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    })
    .then(res => res.text())
    .then(html => {
        document.open();
        document.write(html);
        document.close();
    });
});