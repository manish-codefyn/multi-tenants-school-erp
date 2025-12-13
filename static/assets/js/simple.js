// simple.js - Basic functionality test
document.addEventListener('DOMContentLoaded', function() {
    console.log('Simple JS loaded - testing functionality');
    
    // Test 1: Mobile menu toggle
    const mobileMenu = document.querySelector('.mobile-toggle-menu');
    if (mobileMenu) {
        mobileMenu.addEventListener('click', function() {
            console.log('Mobile menu clicked');
            document.querySelector('.wrapper').classList.toggle('toggled');
        });
        console.log('Mobile menu button found');
    } else {
        console.log('Mobile menu button NOT found');
    }
    
    // Test 2: Dark mode toggle
    const darkMode = document.querySelector('.dark-mode');
    if (darkMode) {
        darkMode.addEventListener('click', function() {
            console.log('Dark mode clicked');
            const html = document.documentElement;
            const icon = document.querySelector('.dark-mode-icon i');
            
            if (html.classList.contains('dark-theme')) {
                // Switch to light
                html.classList.remove('dark-theme');
                html.classList.add('light-theme');
                if (icon) icon.className = 'bx bx-moon';
            } else {
                // Switch to dark
                html.classList.remove('light-theme');
                html.classList.add('dark-theme');
                if (icon) icon.className = 'bx bx-sun';
            }
        });
        console.log('Dark mode button found');
    } else {
        console.log('Dark mode button NOT found');
    }
    
    // Test 3: Back to top
    const backToTop = document.querySelector('.back-to-top');
    if (backToTop) {
        backToTop.addEventListener('click', function(e) {
            e.preventDefault();
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
    }
});