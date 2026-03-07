const fs = require('fs');

async function checkDatabase() {
    try {
        // 1. Login as Admin
        console.log("Logging in as admin...");
        const loginRes = await fetch('https://backend-c65g.onrender.com/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: 'admin@university.edu',
                password: 'adminpassword123'
            })
        });

        if (!loginRes.ok) {
            console.error("Admin login failed", await loginRes.text());
            return;
        }
        const token = (await loginRes.json()).access_token;

        // 2. Fetch all users
        console.log("Fetching users...");
        const usersRes = await fetch('https://backend-c65g.onrender.com/users/', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const users = await usersRes.json();

        // 3. Find the "test test" user
        const testUser = users.find(u => u.first_name === 'test' || u.email.startsWith('test@'));

        if (!testUser) {
            console.log("Could not find 'test' user in DB.");
        } else {
            console.log("Found Test User ID:", testUser.id);
            fs.writeFileSync('test_user_db.json', JSON.stringify(testUser, null, 2));
            console.log("Saved full DB profile to test_user_db.json");
        }
    } catch (err) {
        console.error("Error:", err);
    }
}
checkDatabase();
