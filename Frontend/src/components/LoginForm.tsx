import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { login, requestForgotPassword, verifyMfaChallenge } from "../api/authApi";
import { normalizeLogoUrl } from "../api/schoolSettingsApi";
import { useUser } from "../context/UserContext";
import { FaUser, FaLock, FaEnvelope, FaEye, FaEyeSlash } from "react-icons/fa";
import { motion } from "framer-motion";

const resolveDashboardPath = (roles: string[]): string | null => {
  const normalizedRoles = new Set(roles.map((role) => role.toLowerCase()));
  const hasRole = (...roleNames: string[]) =>
    roleNames.some((roleName) => normalizedRoles.has(roleName.toLowerCase()));

  const isStudent = hasRole("student");
  const isSsg = hasRole("ssg");
  const isEventOrganizer = hasRole("event-organizer", "event_organizer");

  if (hasRole("admin")) return "/admin_dashboard";
  if (hasRole("school_it", "school-it")) return "/school_it_dashboard";
  if (isStudent && isSsg && isEventOrganizer) return "/student_ssg_eventorganizer_dashboard";
  if (isStudent && isSsg) return "/student_ssg_dashboard";
  if (isStudent) return "/student_dashboard";
  if (isSsg) return "/ssg_dashboard";
  if (isEventOrganizer) return "/event_organizer_dashboard";
  return null;
};

const LoginForm = () => {
  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [rememberMe, setRememberMe] = useState<boolean>(false);
  const [showPassword, setShowPassword] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [showForgotPassword, setShowForgotPassword] = useState<boolean>(false);
  const [forgotEmail, setForgotEmail] = useState<string>("");
  const [forgotSubmitting, setForgotSubmitting] = useState<boolean>(false);
  const [forgotMessage, setForgotMessage] = useState<string | null>(null);
  const [forgotError, setForgotError] = useState<string | null>(null);
  const [mfaChallengeId, setMfaChallengeId] = useState<string | null>(null);
  const [mfaEmail, setMfaEmail] = useState<string | null>(null);
  const [mfaCode, setMfaCode] = useState<string>("");
  const [mfaPending, setMfaPending] = useState<boolean>(false);
  const [mfaSubmitting, setMfaSubmitting] = useState<boolean>(false);
  const [mfaExpiresAt, setMfaExpiresAt] = useState<string | null>(null);
  const navigate = useNavigate();
  const { setBranding } = useUser();

  useEffect(() => {
    const savedEmail = localStorage.getItem("rememberedEmail");
    if (savedEmail) {
      setEmail(savedEmail);
      setRememberMe(true);
    }
  }, []);

  const finalizeLogin = (userData: any) => {
    if (!userData.token || !userData.roles) {
      throw new Error("Invalid response from server.");
    }

    localStorage.setItem("user", JSON.stringify(userData));
    localStorage.setItem("token", userData.token);

    if (userData.schoolId) {
      setBranding({
        school_id: userData.schoolId,
        school_name: userData.schoolName || "School",
        school_code: userData.schoolCode || null,
        logo_url: normalizeLogoUrl(userData.logoUrl),
        primary_color: userData.primaryColor || "#162F65",
        secondary_color: userData.secondaryColor || "#2C5F9E",
        subscription_status: "trial",
        active_status: true,
      });
    }

    if (rememberMe) {
      localStorage.setItem("rememberedEmail", email);
    } else {
      localStorage.removeItem("rememberedEmail");
    }

    if (userData.mustChangePassword) {
      navigate("/change-password");
      return;
    }

    const targetPath = resolveDashboardPath(userData.roles || []);
    if (targetPath) {
      navigate(targetPath);
      return;
    }
    alert("No valid role found!");
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsLoading(true);

    try {
      const userData = await login(email, password);
      if (userData.mfaRequired) {
        setMfaPending(true);
        setMfaChallengeId(userData.mfaChallengeId || null);
        setMfaEmail(userData.email || email);
        setMfaExpiresAt(userData.mfaExpiresAt || null);
        setMfaCode("");
        return;
      }
      finalizeLogin(userData);
    } catch (error: any) {
      alert(error.message || "Login failed! Please check your credentials.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyMfa = async () => {
    if (!mfaChallengeId || !mfaEmail) {
      alert("MFA challenge is missing. Please log in again.");
      setMfaPending(false);
      return;
    }
    if (!mfaCode.trim()) {
      alert("Enter your MFA code.");
      return;
    }
    setMfaSubmitting(true);
    try {
      const userData = await verifyMfaChallenge(mfaEmail, mfaChallengeId, mfaCode.trim());
      setMfaPending(false);
      setMfaChallengeId(null);
      setMfaEmail(null);
      setMfaCode("");
      finalizeLogin(userData);
    } catch (error: any) {
      alert(error.message || "Failed to verify MFA code.");
    } finally {
      setMfaSubmitting(false);
    }
  };

  const handleForgotPasswordSubmit = async () => {
    setForgotSubmitting(true);
    setForgotError(null);
    setForgotMessage(null);

    try {
      const targetEmail = forgotEmail.trim();
      if (!targetEmail) {
        throw new Error("Please enter your email.");
      }
      const message = await requestForgotPassword(targetEmail);
      setForgotMessage(message);
    } catch (error: any) {
      setForgotError(error.message || "Failed to submit forgot password request.");
    } finally {
      setForgotSubmitting(false);
    }
  };

  return (
    <div className="login-form-container">
      <h4 className="user-login-title">
        <FaUser className="user-icon" /> User Login
      </h4>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label">
            <FaEnvelope className="input-icon" /> Email
          </label>
          <input
            type="email"
            className="form-input"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            placeholder="Enter your email address"
            minLength={2}
            maxLength={50}
          />
        </div>

        <div className="form-group">
          <label className="form-label">
            <FaLock className="input-icon" /> Password
          </label>
          <div className="password-input-container">
            <input
              type={showPassword ? "text" : "password"}
              className="form-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              placeholder="Enter your password"
              minLength={8}
              maxLength={30}
            />
            <button
              type="button"
              className="toggle-password"
              onClick={() => setShowPassword(!showPassword)}
            >
              {showPassword ? <FaEyeSlash /> : <FaEye />}
            </button>
          </div>
        </div>

        <div className="form-options">
          <div className="remember-me">
            <input
              type="checkbox"
              id="rememberMe"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
            />
            <label htmlFor="rememberMe">Remember me</label>
          </div>
          <button
            type="button"
            className="forgot-password"
            onClick={() => {
              setShowForgotPassword((prev) => !prev);
              setForgotEmail((prev) => (prev ? prev : email));
              setForgotError(null);
              setForgotMessage(null);
            }}
          >
            Forgot password?
          </button>
        </div>

        {showForgotPassword && (
          <div className="forgot-password-panel">
            <label className="form-label mb-2">Reset Password Request</label>
            <input
              type="email"
              className="form-input"
              value={forgotEmail}
              onChange={(e) => setForgotEmail(e.target.value)}
              placeholder="Enter your account email"
              required
            />
            <button
              type="button"
              className="forgot-password-submit"
              onClick={handleForgotPasswordSubmit}
              disabled={forgotSubmitting}
            >
              {forgotSubmitting ? "Submitting..." : "Submit Request"}
            </button>
            {forgotMessage && <p className="forgot-password-message">{forgotMessage}</p>}
            {forgotError && <p className="forgot-password-error">{forgotError}</p>}
          </div>
        )}

        {mfaPending && (
          <div className="forgot-password-panel">
            <label className="form-label mb-2">Multi-Factor Verification</label>
            <p style={{ marginBottom: 8 }}>
              Enter the 6-digit code sent to <strong>{mfaEmail}</strong>.
            </p>
            {mfaExpiresAt && <p style={{ marginBottom: 8 }}>Code expires at: {mfaExpiresAt}</p>}
            <input
              type="text"
              className="form-input"
              value={mfaCode}
              onChange={(e) => setMfaCode(e.target.value)}
              placeholder="Enter MFA code"
              maxLength={12}
            />
            <button
              type="button"
              className="forgot-password-submit"
              onClick={handleVerifyMfa}
              disabled={mfaSubmitting}
            >
              {mfaSubmitting ? "Verifying..." : "Verify Code"}
            </button>
          </div>
        )}

        <motion.button
          type="submit"
          className="login-button"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          disabled={isLoading}
        >
          {isLoading ? <span className="spinner"></span> : "Login"}
        </motion.button>
      </form>
    </div>
  );
};

export default LoginForm;
