const fs = require('fs');
const https = require('https');

async function check() {
    try {
        const loginRes = await fetch('https://backend-c65g.onrender.com/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
                username: 'admin@university.edu',
                password: 'adminpassword123'
            })
        });
        const loginData = await loginRes.json();
        const token = loginData.access_token;
        if (!token) return console.error("No token", loginData);

        const usersRes = await fetch('https://backend-c65g.onrender.com/users/', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const users = await usersRes.json();

        fs.writeFileSync('all_users_dump.json', JSON.stringify(users, null, 2));
        console.log("Dumped all users");
    } catch (e) {
        console.error(e);
    }
}
check();
