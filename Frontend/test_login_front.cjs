const fs = require('fs');

async function testFetch() {
    try {
        const loginRes = await fetch('https://backend-c65g.onrender.com/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
                'username': 'front@gmail.com',
                'password': 'password123' // guessing what they typed
            })
        });

        if (!loginRes.ok) {
            console.log("Login failed", await loginRes.text());
            return;
        }
        const loginData = await loginRes.json();
        const token = loginData.access_token;

        // Fetch specifically this user's profile
        const usersRes = await fetch('https://backend-c65g.onrender.com/users/me', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const profile = await usersRes.json();
        fs.writeFileSync('front_profile.json', JSON.stringify(profile, null, 2));
        console.log("Saved to front_profile.json");

    } catch (err) {
        console.error("Error:", err);
    }
}
testFetch();
