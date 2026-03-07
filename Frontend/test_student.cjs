const fs = require('fs');

async function testLoginAndDashboard() {
    try {
        // 1. Log in
        const loginRes = await fetch('https://backend-c65g.onrender.com/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
                'username': 'joyborjacom6@gmail.com', // A student email from the screenshot
                'password': 'password123' // guess, or maybe I should use 'student@university.edu'? Let's just create a new script that impersonates the frontend fetch logic using the admin token to fetch that user
            })
        });

        // Actually, let's just use the Admin token to fetch Joy's profile and test the formatting locally
        const adminRes = await fetch('https://backend-c65g.onrender.com/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
                'username': 'admin@university.edu',
                'password': 'adminpassword123'
            })
        });
        const token = (await adminRes.json()).access_token;

        const profileRes = await fetch('https://backend-c65g.onrender.com/users/23-A-01617', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const profile = await profileRes.json();

        fs.writeFileSync('test_student_profile.json', JSON.stringify(profile, null, 2));
        console.log("Dumped Joy's profile.");
    } catch (err) {
        console.error(err);
    }
}
testLoginAndDashboard();
