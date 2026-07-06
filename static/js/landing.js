/*==================================================
DIGITAL HEALTH INSURANCE CLAIMS MANAGEMENT SYSTEM
LANDING PAGE JAVASCRIPT
==================================================*/

document.addEventListener("DOMContentLoaded", function () {

    /*==========================================
    AOS
    ==========================================*/

    if (typeof AOS !== "undefined") {
        AOS.init({
            duration: 1000,
            once: true,
            easing: "ease-in-out"
        });
    }

    /*==========================================
    COUNTER ANIMATION
    ==========================================*/

    const counters = document.querySelectorAll(".counter");

    counters.forEach(counter => {

        const updateCounter = () => {

            const target = Number(counter.getAttribute("data-target"));

            const current = Number(counter.innerText);

            const increment = Math.ceil(target / 80);

            if (current < target) {

                counter.innerText = current + increment;

                setTimeout(updateCounter, 25);

            } else {

                counter.innerText = target;

            }

        };

        updateCounter();

    });

    /*==========================================
    BACK TO TOP BUTTON
    ==========================================*/

    const backButton = document.getElementById("backToTop");

    window.addEventListener("scroll", function () {

        if (window.scrollY > 300) {

            backButton.style.display = "block";

        } else {

            backButton.style.display = "none";

        }

    });

    if (backButton) {

        backButton.addEventListener("click", function () {

            window.scrollTo({

                top: 0,

                behavior: "smooth"

            });

        });

    }

    /*==========================================
    SMOOTH SCROLL
    ==========================================*/

    document.querySelectorAll('a[href^="#"]').forEach(anchor => {

        anchor.addEventListener("click", function (e) {

            const target = document.querySelector(this.getAttribute("href"));

            if (target) {

                e.preventDefault();

                target.scrollIntoView({

                    behavior: "smooth"

                });

            }

        });

    });

    /*==========================================
    NAVBAR COLOR CHANGE
    ==========================================*/

    const navbar = document.querySelector(".glass-navbar");

    window.addEventListener("scroll", function () {

        if (window.scrollY > 60) {

            navbar.style.background = "#0d6efd";

        } else {

            navbar.style.background = "rgba(0,0,0,.75)";

        }

    });

    /*==========================================
    ACTIVE NAVIGATION
    ==========================================*/

    const sections = document.querySelectorAll("section");

    const navLinks = document.querySelectorAll(".nav-link");

    window.addEventListener("scroll", function () {

        let current = "";

        sections.forEach(section => {

            const sectionTop = section.offsetTop - 120;

            if (pageYOffset >= sectionTop) {

                current = section.getAttribute("id");

            }

        });

        navLinks.forEach(link => {

            link.classList.remove("active");

            if (link.getAttribute("href") === "#" + current) {

                link.classList.add("active");

            }

        });

    });

    /*==========================================
    AUTO CLOSE MOBILE MENU
    ==========================================*/

    const navItems = document.querySelectorAll(".navbar-collapse .nav-link");

    const navbarCollapse = document.querySelector(".navbar-collapse");

    navItems.forEach(item => {

        item.addEventListener("click", function () {

            if (navbarCollapse.classList.contains("show")) {

                bootstrap.Collapse.getInstance(navbarCollapse).hide();

            }

        });

    });

    /*==========================================
    CARD HOVER EFFECT
    ==========================================*/

    const cards = document.querySelectorAll(".card");

    cards.forEach(card => {

        card.addEventListener("mouseenter", function () {

            card.style.transform = "translateY(-10px)";

        });

        card.addEventListener("mouseleave", function () {

            card.style.transform = "translateY(0px)";

        });

    });

    /*==========================================
    HERO IMAGE EFFECT
    ==========================================*/

    const heroImage = document.querySelector(".hero-image");

    if (heroImage) {

        window.addEventListener("mousemove", function (e) {

            let x = (window.innerWidth / 2 - e.pageX) / 80;

            let y = (window.innerHeight / 2 - e.pageY) / 80;

            heroImage.style.transform =
                `translate(${x}px, ${y}px)`;

        });

    }

    /*==========================================
    FADE IN
    ==========================================*/

    const observer = new IntersectionObserver(entries => {

        entries.forEach(entry => {

            if (entry.isIntersecting) {

                entry.target.classList.add("show");

            }

        });

    });

    document.querySelectorAll(".feature-box,.about-card,.feature-card,.dashboard-preview,.testimonial-card")
        .forEach(element => {

            observer.observe(element);

        });

});