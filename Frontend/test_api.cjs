const fs = require('fs');

async function testFetch() {
    try {
        // 1. Login to get token
        const loginRes = await fetch('https://backend-c65g.onrender.com/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
                'username': 'admin@university.edu',
                'password': 'adminpassword123'
            })
        });

        const loginData = await loginRes.json();
        const token = loginData.access_token;

        // 2. Fetch users
        const usersRes = await fetch('https://backend-c65g.onrender.com/users/', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        const usersData = await usersRes.json();

        fs.writeFileSync('temp_api_test.json', JSON.stringify(usersData, null, 2));

        console.log("Successfully fetched and saved to temp_api_test.json");

    } catch (err) {
        console.error("Error:", err);
    }
}

testFetch();
