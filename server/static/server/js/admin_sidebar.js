document.addEventListener("DOMContentLoaded", function () {
    const sidebar = document.getElementById("admin-sidebar");
    const overlay = document.getElementById("admin-sidebar-overlay");
    const toggleBtn = document.getElementById("admin-sidebar-toggle");
    const closeBtn = document.getElementById("admin-sidebar-close");

    function setOpen(isOpen) {
        if (!sidebar) return;

        sidebar.classList.toggle("-translate-x-full", !isOpen);
        sidebar.classList.toggle("translate-x-0", isOpen);

        overlay?.classList.toggle("hidden", !isOpen);

        document.body.classList.toggle("overflow-hidden", isOpen);
    }

    toggleBtn?.addEventListener("click", () => setOpen(true));

    closeBtn?.addEventListener("click", () => setOpen(false));

    overlay?.addEventListener("click", () => setOpen(false));

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            setOpen(false);
        }
    });
});