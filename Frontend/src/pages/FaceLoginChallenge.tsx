import { Navigate, useNavigate } from "react-router-dom";
import { FaUserShield } from "react-icons/fa";

import {
  clearPendingFaceAuthSession,
  getPendingFaceAuthSession,
  persistAuthSession,
  type PendingFaceAuthSession,
} from "../api/authApi";
import type { VerificationResult } from "../api/facialVerificationApi";
import {
  buildBrandingFromAuthSession,
  resolveDashboardPath,
  syncRememberedEmail,
} from "../authFlow";
import PrivilegedFaceWorkspace from "../components/PrivilegedFaceWorkspace";
import { useUser } from "../context/UserContext";
import "../css/FacialVerification.css";

const FaceLoginChallengeContent = ({
  pendingAuth,
}: {
  pendingAuth: PendingFaceAuthSession;
}) => {
  const navigate = useNavigate();
  const { setBranding } = useUser();
  const { session, rememberMe, faceRole } = pendingAuth;
  const roleLabel = faceRole === "school_IT" ? "School IT" : "Admin";
  const subjectId = session.email || `${faceRole}:${session.id ?? "pending"}`;
  const subjectLabel =
    `${session.firstName ?? ""} ${session.lastName ?? ""}`.trim() ||
    session.email ||
    roleLabel;

  const completeLogin = (result: VerificationResult) => {
    const verifiedSession = result.authSessionPatch?.accessToken
      ? {
          ...session,
          token: result.authSessionPatch.accessToken,
          tokenType: result.authSessionPatch.tokenType,
          sessionId: result.authSessionPatch.sessionId,
          faceVerificationPending:
            result.authSessionPatch.faceVerificationPending,
        }
      : {
          ...session,
          faceVerificationPending: false,
        };

    persistAuthSession(verifiedSession);
    setBranding(buildBrandingFromAuthSession(verifiedSession));
    syncRememberedEmail(verifiedSession.email, rememberMe);

    navigate(
      verifiedSession.mustChangePassword
        ? "/change-password"
        : resolveDashboardPath(verifiedSession.roles || []),
      { replace: true }
    );
  };

  const handleCancel = () => {
    clearPendingFaceAuthSession();
    navigate("/", { replace: true });
  };

  return (
    <div className="facial-verification-page">
      <main className="facial-verification-shell facial-login-shell">
        <section className="facial-verification-hero">
          <span className="facial-verification-badge">
            <FaUserShield />
            Secure Sign-In
          </span>
          <h1>{roleLabel} Live Face Verification</h1>
          <p>{subjectLabel}</p>
        </section>

        <PrivilegedFaceWorkspace
          role={faceRole}
          subjectId={subjectId}
          subjectLabel={subjectLabel}
          authToken={session.token}
          variant="login"
          onVerified={completeLogin}
          onCancel={handleCancel}
        />
      </main>
    </div>
  );
};

const FaceLoginChallenge = () => {
  const pendingAuth = getPendingFaceAuthSession();
  if (!pendingAuth) {
    return <Navigate to="/" replace />;
  }

  return <FaceLoginChallengeContent pendingAuth={pendingAuth} />;
};

export default FaceLoginChallenge;
