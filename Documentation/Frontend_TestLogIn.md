Frontend Testing Report – CodeKnights VALID8 (mr.frontend)

Tester Information 
Tester Role: QA / Frontend Tester 
Environment: Local Development (localhost) 
Browser Used: Chrome 
Date Tested: April 6, 2026 

Application Overview 
The application is a Campus Portal System that allows users to log in using a school account 
and access workspace features such as attendance and administrative tools. 

The frontend was successfully run locally using: 
npm install 
npm run dev 

Accessed via: 
http://localhost:5173 

Test Scope 
- Login UI functionality 
- Input validation 
- API connectivity 
 User interaction behavior 

Test Cases & Results 
1. Page Load Test 
Action: Open localhost URL 
Expected Result: Login page loads correctly 
Actual Result: Page loaded successfully with UI elements visible 

2. Input Field Validation 
Action: Leave email and password empty, then click login 
Expected Result: Validation error message 
Actual Result: Depends on implementation 

3. Invalid Input Test 
Action: Enter invalid email format or incorrect credentials 
Expected Result: Error message shown 
Actual Result: Depends on backend response 

4. Login Functionality Test (Initial Attempt) 
Action: Enter credentials and click “Log In” 
Expected Result: User should be authenticated and redirected 
Actual Result: Login failed 

Initial Issue Found 
Issue: API Connection Failure 
Error Message: Unable to reach the API 
Severity: High 
Type: Backend/API Integration Issue 
Root Cause Analysis (Initial) 
- Backend server not running 
- Incorrect API endpoint configuration 
- Network/CORS restrictions 
- Missing environment configuration 

Resolution / Retest 

Fix Applied: 
npm run dev:all 

Result After Fix: 
- Frontend and backend services started simultaneously 
- API connection established successfully 
- Login functionality is now operational 

Retest Results 

5. Login Functionality Test (After Fix) 
Action: Enter credentials and click “Log In” 
Expected Result: Successful authentication 
Actual Result: Login request successfully connects to backend

Overall Assessment 
Frontend UI: Working 
User Interaction: Functional 
API Integration: Working after fix 
System Status: Fully Functional (Local Environment) 

Recommendations 
- Ensure npm run dev:all is documented as the correct startup command 
- Improve error handling messages 
- Improve frontend validation 
- Use Postman for API testing 

Conclusion 
The frontend application was successfully tested locally. Initial API connection issues were 
resolved by running npm run dev:all. The system is now fully functional.