document.addEventListener("DOMContentLoaded", function () {

    /* ---------- Sidebar (slides in from the right) ---------- */
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebar-overlay");
    const toggleBtn = document.getElementById("sidebar-toggle");
    const closeBtn = document.getElementById("sidebar-close");

    function setSidebarOpen(isOpen) {
        if (!sidebar) return;

        sidebar.classList.toggle("sidebar-open", isOpen);
        overlay?.classList.toggle("hidden", !isOpen);

        // Prevent the page from scrolling while the sidebar is open.
        document.body.classList.toggle("overflow-hidden", isOpen);

        toggleBtn?.setAttribute("aria-expanded", isOpen ? "true" : "false");
    }

    // Open sidebar
    toggleBtn?.addEventListener("click", () => {
        setSidebarOpen(true);
    });

    // Close sidebar
   closeBtn?.addEventListener("click", (e) => {
    console.log("Close button clicked");
    e.stopPropagation();
    setSidebarOpen(false);
});

    // Close when clicking the overlay
    overlay?.addEventListener("click", () => {
        setSidebarOpen(false);
    });

    // Close on Escape
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            setSidebarOpen(false);
        }
    });
    
    /* ---------- Hero carousel ---------- */
    const track = document.getElementById("hero-track");
    const dotsWrap = document.getElementById("hero-dots");
    const prevBtn = document.getElementById("hero-prev");
    const nextBtn = document.getElementById("hero-next");

    if (track) {
        const slideCount = track.children.length;
        let current = 0;
        let autoplayId = null;

        function renderDots() {
            if (!dotsWrap) return;

            [...dotsWrap.children].forEach((dot, i) => {
                dot.classList.toggle("bg-white", i === current);
                dot.classList.toggle("bg-white/60", i !== current);
            });
        }

        function goTo(index) {
            current = (index + slideCount) % slideCount;
            track.style.transform = `translateX(-${current * 100}%)`;
            renderDots();
        }

        function next() {
            goTo(current + 1);
        }

        function prev() {
            goTo(current - 1);
        }

        function startAutoplay() {
            stopAutoplay();
            autoplayId = setInterval(next, 5000);
        }

        function stopAutoplay() {
            if (autoplayId) {
                clearInterval(autoplayId);
            }
        }

        nextBtn?.addEventListener("click", () => {
            next();
            startAutoplay();
        });

        prevBtn?.addEventListener("click", () => {
            prev();
            startAutoplay();
        });

        if (dotsWrap) {
            [...dotsWrap.children].forEach((dot) => {
                dot.addEventListener("click", () => {
                    goTo(Number(dot.dataset.index));
                    startAutoplay();
                });
            });
        }

        renderDots();
        startAutoplay();
    }
});