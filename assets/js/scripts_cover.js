document.addEventListener('DOMContentLoaded', function () {
    // *** Modal Handling ***
    function openModal() {
        document.getElementById('authModal').style.display = 'flex';
    }

    function closeModal() {
        document.getElementById('authModal').style.display = 'none';
    }

    function openTab(event, tabName) {
        // Remove active class from all form contents and tabs
        document.querySelectorAll('.form-content').forEach(content => content.classList.remove('active'));
        document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));

        // Add active class to the selected tab and content
        document.getElementById(tabName).classList.add('active');
        event.currentTarget.classList.add('active');
    }

    // Expose modal and tab functions globally
    window.openModal = openModal;
    window.closeModal = closeModal;
    window.openTab = openTab;

    // *** Navigation Handling ***
    function navigateToService(serviceId) {
        const isLoggedIn = localStorage.getItem("isLoggedIn");

        if (!isLoggedIn) {
            localStorage.setItem("redirectAfterLogin", "https://sednabcn.github.io/ai-llm-blog");
            openModal();
        } else if (serviceId === 1) {
            window.location.href = "https://sednabcn.github.io/ai-llm-blog";
        } else {
            alert("Invalid service or service not recognized.");
        }
    }
    window.navigateToService = navigateToService;

    // *** Utility Function: Hash Password ***
    function hashPassword(password) {
        // Simple hashing for demonstration (use a real hashing library in production)
        return btoa(password); // Base64 encoding
    }

    // *** Registration Handling ***
    const registerForm = document.getElementById("registerForm");
    if (registerForm) {
        registerForm.addEventListener("submit", function (event) {
            event.preventDefault();

            const email = document.getElementById("registerEmail").value.trim();
            const password = document.getElementById("registerPassword").value.trim();

            if (email && password) {
                // Hash and store credentials
                localStorage.setItem("userEmail", email);
                localStorage.setItem("userPassword", hashPassword(password));

                alert("Registration successful. Please log in.");
                // Switch to Login tab
                openTab({ currentTarget: document.querySelector('.tab.login') }, 'loginTab');
            } else {
                alert("Please enter a valid email and password.");
            }
        });
    }

    // *** Login Handling ***
    const loginForm = document.getElementById("loginForm");
    if (loginForm) {
        loginForm.addEventListener("submit", function (event) {
            event.preventDefault();

            const email = document.getElementById("loginEmail").value.trim();
            const password = document.getElementById("loginPassword").value.trim();

            const storedEmail = localStorage.getItem("userEmail");
            const storedPassword = localStorage.getItem("userPassword");

            if (!storedEmail || !storedPassword) {
                alert("No user registered. Please register first.");
                return;
            }

            // Compare credentials
            if (email === storedEmail && hashPassword(password) === storedPassword) {
                localStorage.setItem("isLoggedIn", "true");

                const redirectAfterLogin = localStorage.getItem("redirectAfterLogin") || "https://sednabcn.github.io/ai-llm-blog";
                localStorage.removeItem("redirectAfterLogin");

                alert("Login successful!");
                window.location.href = redirectAfterLogin;
            } else {
                alert("Incorrect email or password.");
            }
        });
    }

    // *** Logout Handling ***
    const logoutButton = document.getElementById("logoutButton");
    if (logoutButton) {
        logoutButton.addEventListener("click", function () {
            localStorage.removeItem("isLoggedIn");
            localStorage.removeItem("userEmail");
            localStorage.removeItem("userPassword");
            alert("You have been logged out.");
            window.location.href = "index.html";
        });
    }

    // *** Modal Click Outside to Close ***
    window.onclick = function (event) {
        const modal = document.getElementById('authModal');
        if (modal && event.target === modal) {
            closeModal();
        }
    };
});

document.addEventListener('DOMContentLoaded', function () {
    const flushingText = document.getElementById('flushingText');
    const stopLink = document.getElementById('stopLink');
    let flushInterval;
    let isFlushing = true;

    // Check if news was already fetched today
    function isSameDay(lastFetched) {
        const now = new Date();
        const lastFetchedDate = new Date(lastFetched);
        return now.toDateString() === lastFetchedDate.toDateString();
    }

    // Fetch latest news from GitHub-hosted JSON
    async function fetchNews() {
        try {
            const response = await fetch('https://sednabcn.github.io/news.json'); // CHANGE THIS
            if (!response.ok) throw new Error('Network error');
            const data = await response.json();
            return data.title || 'No latest news found.';
        } catch (error) {
            console.error('Error fetching news:', error);
            return 'Unable to load latest news.';
        }
    }

    // Start blinking effect
    function startFlushingEffect() {
        let visible = true;
        flushInterval = setInterval(() => {
            if (!isFlushing) return; // skip if stopped
            flushingText.style.visibility = visible ? 'hidden' : 'visible';
            visible = !visible;
        }, 500);
    }

    // Stop blinking manually
    stopLink.addEventListener('click', function (event) {
        event.preventDefault();
        isFlushing = false;
        clearInterval(flushInterval);
        flushingText.style.visibility = 'visible'; // make sure it's shown
        stopLink.textContent = 'Stopped';
        stopLink.style.pointerEvents = 'none';
        stopLink.style.color = '#aaa';
    });

    // Display news + start flashing
    async function displayNews() {
        // Get the last fetched timestamp from localStorage
        const lastFetched = localStorage.getItem('lastFetched');
        
        // If the news has already been fetched today, use it
        if (lastFetched && isSameDay(lastFetched)) {
            const cachedNews = localStorage.getItem('cachedNews');
            flushingText.textContent = cachedNews + ' ';
            flushingText.appendChild(stopLink); // re-add link after text
            startFlushingEffect();
        } else {
            flushingText.textContent = 'Loading...';
            const news = await fetchNews();
            flushingText.textContent = news + ' ';
            flushingText.appendChild(stopLink); // re-add link after text
            startFlushingEffect();

            // Store the fetched news and timestamp in localStorage
            localStorage.setItem('cachedNews', news);
            localStorage.setItem('lastFetched', new Date().toString());
        }
    }

    displayNews();
});
