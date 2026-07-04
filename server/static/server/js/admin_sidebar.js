document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.getElementById("admin-sidebar");
    const overlay = document.getElementById("admin-sidebar-overlay");
    const toggleBtn = document.getElementById("admin-sidebar-toggle");

    function setOpen(isOpen) {
        if (!sidebar) return;
        sidebar.classList.toggle("-translate-x-full", !isOpen);
        sidebar.classList.toggle("translate-x-0", isOpen);
        overlay && overlay.classList.toggle("hidden", !isOpen);
        document.body.classList.toggle("overflow-hidden", isOpen);
    }

    if (toggleBtn) {
        toggleBtn.addEventListener("click", function () {
            const isOpen = sidebar.classList.contains("translate-x-0");
            setOpen(!isOpen);
        });
    }

    if (overlay) overlay.addEventListener("click", () => setOpen(false));

    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") setOpen(false);
    });
});
