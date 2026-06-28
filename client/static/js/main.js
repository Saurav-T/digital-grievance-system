document.addEventListener("DOMContentLoaded", function () {

    /* ---------- Sidebar (slides in from the right) ---------- */
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebar-overlay");
    const toggleBtn = document.getElementById("sidebar-toggle");
    const iconHamburger = document.getElementById("icon-hamburger");
    const iconClose = document.getElementById("icon-close");

    function setSidebarOpen(isOpen) {
        if (!sidebar) return;

        sidebar.classList.toggle("sidebar-open", isOpen);
        overlay && overlay.classList.toggle("hidden", !isOpen);
        document.body.classList.toggle("overflow-hidden", isOpen);

        if (toggleBtn) toggleBtn.setAttribute("aria-expanded", isOpen ? "true" : "false");
        if (iconHamburger) iconHamburger.classList.toggle("hidden", isOpen);
        if (iconClose) iconClose.classList.toggle("hidden", !isOpen);
    }

    if (toggleBtn) {
        toggleBtn.addEventListener("click", function () {
            const isCurrentlyOpen = sidebar.classList.contains("sidebar-open");
            setSidebarOpen(!isCurrentlyOpen);
        });
    }

    if (overlay) overlay.addEventListener("click", () => setSidebarOpen(false));

    document.addEventListener("keydown", function (e) {
        if (e.key === "Escape") setSidebarOpen(false);
    });

    /* ---------- Marquee: randomised notice pool ---------- */
    const marqueeTrack = document.getElementById("marquee-track");

    if (marqueeTrack && Array.isArray(window.MARQUEE_NOTICES) && window.MARQUEE_NOTICES.length) {
        // Shuffle a copy of the pool (Fisher-Yates) so the order differs per page load.
        const pool = [...window.MARQUEE_NOTICES];
        for (let i = pool.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [pool[i], pool[j]] = [pool[j], pool[i]];
        }

        function buildItem(text, hidden) {
            const span = document.createElement("span");
            span.className = "flex items-center gap-2";
            if (hidden) span.setAttribute("aria-hidden", "true");

            const dot = document.createElement("span");
            dot.className = "h-1.5 w-1.5 rounded-full bg-white/70 inline-block";

            span.appendChild(dot);
            span.appendChild(document.createTextNode(text));
            return span;
        }

        // Render the shuffled list once, then a duplicate (aria-hidden) so the CSS
        // animation (-50% translateX) loops seamlessly.
        pool.forEach((text) => marqueeTrack.appendChild(buildItem(text, false)));
        pool.forEach((text) => marqueeTrack.appendChild(buildItem(text, true)));
    }

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

        function next() { goTo(current + 1); }
        function prev() { goTo(current - 1); }

        function startAutoplay() {
            stopAutoplay();
            autoplayId = setInterval(next, 5000);
        }
        function stopAutoplay() {
            if (autoplayId) clearInterval(autoplayId);
        }

        if (nextBtn) nextBtn.addEventListener("click", () => { next(); startAutoplay(); });
        if (prevBtn) prevBtn.addEventListener("click", () => { prev(); startAutoplay(); });
        if (dotsWrap) {
            [...dotsWrap.children].forEach((dot) => {
                dot.addEventListener("click", () => {
                    goTo(parseInt(dot.dataset.index, 10));
                    startAutoplay();
                });
            });
        }

        renderDots();
        startAutoplay();
    }
});
