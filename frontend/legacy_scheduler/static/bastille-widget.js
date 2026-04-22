(function () {

    function initWidget() {

        const BASE_URL = "http://127.0.0.1:8000";

        // ==========================
        // 建立 icon
        // ==========================
        const fab = document.createElement("div");
        fab.innerHTML = "📊";
        Object.assign(fab.style, {
            position: "fixed",
            bottom: "30px",
            right: "30px",
            width: "70px",
            height: "70px",
            borderRadius: "50%",
            background: "#b21f1f",
            color: "white",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "26px",
            cursor: "pointer",
            zIndex: "999999",
            boxShadow: "0 8px 25px rgba(0,0,0,0.3)"
        });

        document.body.appendChild(fab);

        // ==========================
        // 建立 modal container
        // ==========================
        const modal = document.createElement("div");
        Object.assign(modal.style, {
            position: "fixed",
            bottom: "20px",
            right: "20px",
            top: "auto",
            left: "auto",

            width: "650px",
            height: "550px",
            maxHeight: "80vh",

            background: "white",
            borderRadius: "16px",
            boxShadow: "0 10px 30px rgba(0,0,0,0.25)",
            zIndex: "999998",

            display: "none",
            resize: "both",
            overflow: "auto",

            minWidth: "350px",
            minHeight: "300px"
        });

        document.body.appendChild(modal);

        // ==========================
        // header (拖動區)
        // ==========================
        const header = document.createElement("div");
        header.innerHTML = "";
        Object.assign(header.style, {
            height: "50px",
            background: "#b21f1f",
            color: "white",
            display: "flex",
            alignItems: "center",
            paddingLeft: "15px",
            cursor: "move",
            userSelect: "none"
        });

        modal.appendChild(header);

        // ==========================
        // iframe
        // ==========================
        const iframe = document.createElement("iframe");
        iframe.src = BASE_URL + "/console";

        Object.assign(iframe.style, {
            width: "100%",
            height: "calc(100% - 50px)",
            border: "none"
        });

        modal.appendChild(iframe);

        // ==========================
        // 拖動邏輯
        // ==========================
        let isDragging = false;
        let offsetX = 0;
        let offsetY = 0;

        header.addEventListener("mousedown", (e) => {
            isDragging = true;
            const rect = modal.getBoundingClientRect();
            offsetX = e.clientX - rect.left;
            offsetY = e.clientY - rect.top;
        });

        document.addEventListener("mousemove", (e) => {
            if (!isDragging) return;

            modal.style.left = (e.clientX - offsetX) + "px";
            modal.style.top = (e.clientY - offsetY) + "px";
        });

        document.addEventListener("mouseup", () => {
            isDragging = false;
        });

        // ==========================
        // 開關邏輯
        // ==========================
        fab.addEventListener("click", () => {
            modal.style.display = "block";
            fab.style.display = "none";
        });

        window.addEventListener("message", (event) => {
            if (event.data === "close-console") {
                modal.style.display = "none";
                fab.style.display = "flex";
            }
        });
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initWidget);
    } else {
        initWidget();
    }

})();